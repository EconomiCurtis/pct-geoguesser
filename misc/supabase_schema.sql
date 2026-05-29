-- ─────────────────────────────────────────────────────────────────────────────
-- PCT GeoGuesser — Supabase schema
-- Run each block in order in the Supabase SQL Editor.
-- ─────────────────────────────────────────────────────────────────────────────


-- ── Block 1: Profiles ────────────────────────────────────────────────────────
-- One row per Google account. trail_name + pct_year are shown on the leaderboard.

CREATE TABLE profiles (
  id         UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  trail_name TEXT NOT NULL,
  pct_year   TEXT NOT NULL,   -- freeform, e.g. "2025", "2025 / 2016", "planning 2027"
  about      TEXT,            -- up to 1000 chars, shown on /hiker/{id}/ page only
  created_at TIMESTAMPTZ DEFAULT now()
);


-- ── Block 2: Game sessions ───────────────────────────────────────────────────
-- One row per completed scored game.

CREATE TABLE game_sessions (
  id            UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID    NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  total_score   INTEGER NOT NULL,    -- sum of per-round errors in miles (lower = better)
  perfect_count INTEGER DEFAULT 0,  -- rounds where error ≤ 3 miles
  photo_count   INTEGER DEFAULT 10,
  played_at     TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON game_sessions (user_id, total_score);
CREATE INDEX ON game_sessions (played_at DESC);


-- ── Block 3: Game guesses ────────────────────────────────────────────────────
-- One row per photo per game. Inserted atomically via submit_game() RPC.

CREATE TABLE game_guesses (
  id           UUID  PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id   UUID  NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
  photo_id     TEXT  NOT NULL,     -- 5-letter ID from photos.csv
  true_mile    FLOAT NOT NULL,
  guessed_mile FLOAT,              -- NULL if player timed out
  score        INTEGER NOT NULL,
  timed_out    BOOLEAN DEFAULT FALSE
);

CREATE INDEX ON game_guesses (photo_id);


-- ── Block 4: Photo stats ─────────────────────────────────────────────────────
-- Aggregate per-photo statistics, updated at game completion via submit_game().
--
-- Running statistics use Welford's online algorithm, which updates mean,
-- variance, and std dev in a single pass without storing all raw values.
--
-- Columns:
--   appearances   total times shown in a completed scored game
--   n_guesses     non-timed-out guesses (the denominator for all stats)
--   avg_error     running mean of guessing error (miles off)
--   m2            Welford's M2 accumulator — needed to update variance correctly;
--                 not meaningful on its own but must be persisted between updates
--   v_var         population variance  = m2 / n_guesses
--   v_sd          standard deviation   = sqrt(v_var)
--   perfect_count times guessed within ±3 miles

CREATE TABLE photo_stats (
  photo_id      TEXT    PRIMARY KEY,
  appearances   INTEGER DEFAULT 0,
  n_guesses     INTEGER DEFAULT 0,
  avg_error     FLOAT   DEFAULT 0,
  m2            FLOAT   DEFAULT 0,   -- Welford accumulator; do not interpret directly
  v_var         FLOAT   DEFAULT 0,
  v_sd          FLOAT   DEFAULT 0,
  perfect_count INTEGER DEFAULT 0,
  updated_at    TIMESTAMPTZ DEFAULT now()
);


-- ── Block 5: Row Level Security ──────────────────────────────────────────────
-- The anon key is embedded in public HTML. RLS ensures it can only READ public
-- data, and authenticated users can only write their own rows.

ALTER TABLE profiles      ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_guesses  ENABLE ROW LEVEL SECURITY;
ALTER TABLE photo_stats   ENABLE ROW LEVEL SECURITY;

-- profiles
CREATE POLICY "profiles_read"   ON profiles FOR SELECT USING (true);
CREATE POLICY "profiles_insert" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "profiles_update" ON profiles FOR UPDATE  USING   (auth.uid() = id);
-- no DELETE policy → users cannot delete their own profile via API

-- game_sessions: public read; users insert their own only; no edit or delete
CREATE POLICY "sessions_read"   ON game_sessions FOR SELECT USING (true);
CREATE POLICY "sessions_insert" ON game_sessions FOR INSERT WITH CHECK (auth.uid() = user_id);

-- game_guesses and photo_stats: public read only; all writes go through submit_game()
CREATE POLICY "guesses_read"     ON game_guesses FOR SELECT USING (true);
CREATE POLICY "photo_stats_read" ON photo_stats  FOR SELECT USING (true);


-- ── Block 6: Triggers ────────────────────────────────────────────────────────

-- 6a. Rate limit: reject a new game if the same user submitted one within 1 min
CREATE OR REPLACE FUNCTION enforce_game_rate_limit()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM game_sessions
    WHERE user_id  = NEW.user_id
      AND played_at > NOW() - INTERVAL '1 minute'
  ) THEN
    RAISE EXCEPTION 'Rate limit: wait 1 minute between scored games';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER game_rate_limit
  BEFORE INSERT ON game_sessions
  FOR EACH ROW EXECUTE FUNCTION enforce_game_rate_limit();


-- 6b. Score validation: reject values outside what a real game could produce
CREATE OR REPLACE FUNCTION validate_game_score()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  -- 10 rounds × 2655.5 mi max trail = 26,555 absolute worst-case total
  IF NEW.total_score   < 0 OR NEW.total_score   > 26555           THEN
    RAISE EXCEPTION 'Invalid total_score';
  END IF;
  IF NEW.perfect_count < 0 OR NEW.perfect_count > NEW.photo_count THEN
    RAISE EXCEPTION 'Invalid perfect_count';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER validate_score
  BEFORE INSERT ON game_sessions
  FOR EACH ROW EXECUTE FUNCTION validate_game_score();


-- 6c. Session cap: hard limit of 10 saved games per user
CREATE OR REPLACE FUNCTION enforce_session_cap()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF (SELECT COUNT(*) FROM game_sessions WHERE user_id = NEW.user_id) >= 10 THEN
    RAISE EXCEPTION 'Session cap reached (10 games max per user)';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER session_cap
  BEFORE INSERT ON game_sessions
  FOR EACH ROW EXECUTE FUNCTION enforce_session_cap();


-- ── Block 7: submit_game() RPC ───────────────────────────────────────────────
-- Called once by the JS client when a game ends.
-- Inserts the session + all guesses + updates photo_stats in one transaction.
-- SECURITY DEFINER means it runs with table-owner privileges, bypassing the
-- "no direct insert" RLS on game_guesses and photo_stats.
--
-- Photo stats update uses Welford's online algorithm:
--   delta     = new_error - old_mean
--   new_mean  = old_mean + delta / new_n
--   delta2    = new_error - new_mean          ← uses the *updated* mean
--   new_M2    = old_M2 + delta * delta2
--   variance  = new_M2 / new_n               ← population variance
--   std_dev   = sqrt(variance)
--
-- This is numerically stable and requires only the stored (n, mean, M2) —
-- no raw values needed. First entry (n=0) is handled naturally: delta=error,
-- new_mean=error, delta2=0, M2 stays 0, variance=0.

CREATE OR REPLACE FUNCTION submit_game(
  p_user_id       UUID,
  p_total_score   INTEGER,
  p_perfect_count INTEGER,
  p_guesses       JSONB    -- [{photo_id, true_mile, guessed_mile, score, timed_out}, ...]
) RETURNS UUID LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  v_session_id UUID;
  v_guess      JSONB;
  -- photo stats working variables
  v_n          INTEGER;
  v_avg        FLOAT;
  v_m2         FLOAT;
  v_error      FLOAT;
  v_new_n      INTEGER;
  v_delta      FLOAT;
  v_new_mean   FLOAT;
  v_delta2     FLOAT;
  v_new_m2     FLOAT;
  v_new_var    FLOAT;
  v_new_sd     FLOAT;
BEGIN

  -- Insert session row (triggers fire here: rate limit + validation + cap)
  INSERT INTO game_sessions (user_id, total_score, perfect_count, photo_count)
  VALUES (p_user_id, p_total_score, p_perfect_count, jsonb_array_length(p_guesses))
  RETURNING id INTO v_session_id;

  -- Process each photo in the game
  FOR v_guess IN SELECT * FROM jsonb_array_elements(p_guesses) LOOP

    -- Record the individual guess
    INSERT INTO game_guesses (session_id, photo_id, true_mile, guessed_mile, score, timed_out)
    VALUES (
      v_session_id,
      v_guess->>'photo_id',
      (v_guess->>'true_mile')::FLOAT,
      NULLIF(v_guess->>'guessed_mile', 'null')::FLOAT,
      (v_guess->>'score')::INTEGER,
      (v_guess->>'timed_out')::BOOLEAN
    );

    -- Ensure a photo_stats row exists for this photo
    INSERT INTO photo_stats (photo_id)
    VALUES (v_guess->>'photo_id')
    ON CONFLICT (photo_id) DO NOTHING;

    -- Always increment appearances (timed-out rounds still count as a showing)
    UPDATE photo_stats
    SET appearances = appearances + 1,
        updated_at  = now()
    WHERE photo_id = v_guess->>'photo_id';

    -- Update running stats only for non-timed-out guesses
    IF NOT (v_guess->>'timed_out')::BOOLEAN THEN

      -- Load current state
      SELECT n_guesses, avg_error, m2
      INTO   v_n, v_avg, v_m2
      FROM   photo_stats
      WHERE  photo_id = v_guess->>'photo_id';

      v_error    := ABS((v_guess->>'guessed_mile')::FLOAT - (v_guess->>'true_mile')::FLOAT);

      -- Welford's online update
      v_new_n    := v_n + 1;
      v_delta    := v_error - v_avg;                      -- delta from OLD mean
      v_new_mean := v_avg + v_delta / v_new_n;            -- update mean
      v_delta2   := v_error - v_new_mean;                 -- delta from NEW mean
      v_new_m2   := v_m2 + v_delta * v_delta2;            -- update M2 accumulator
      v_new_var  := CASE WHEN v_new_n > 1
                         THEN v_new_m2 / v_new_n          -- population variance
                         ELSE 0 END;
      v_new_sd   := sqrt(v_new_var);

      UPDATE photo_stats SET
        n_guesses     = v_new_n,
        avg_error     = v_new_mean,
        m2            = v_new_m2,
        v_var         = v_new_var,
        v_sd          = v_new_sd,
        perfect_count = perfect_count + CASE WHEN v_error <= 3 THEN 1 ELSE 0 END,
        updated_at    = now()
      WHERE photo_id = v_guess->>'photo_id';

    END IF;

  END LOOP;

  RETURN v_session_id;
END;
$$;
