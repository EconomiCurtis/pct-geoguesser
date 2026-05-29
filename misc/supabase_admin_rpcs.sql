-- ─────────────────────────────────────────────────────────────────────────────
-- Admin RPCs for PCT GeoGuesser admin dashboard
--
-- Paste both functions into Supabase Dashboard → SQL Editor and run once.
-- These are SECURITY DEFINER — they run with elevated privileges, but
-- include their own server-side admin email check (curtisesjunk@gmail.com),
-- so calling them via the anon key is safe.
--
-- IMPORTANT: These RPCs delete game data only. They do NOT delete from
-- auth.users — do that manually in Supabase Dashboard → Authentication → Users.
-- ─────────────────────────────────────────────────────────────────────────────


-- ── 1. Delete a player's games only (keep profile + auth account) ────────────
CREATE OR REPLACE FUNCTION admin_delete_player_games(target_user_id UUID)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  admin_email  CONSTANT TEXT := 'curtisesjunk@gmail.com';
  caller_email TEXT;
  n_del        INT;
BEGIN
  -- Verify caller is admin
  SELECT email INTO caller_email
  FROM auth.users
  WHERE id = auth.uid();

  IF caller_email IS DISTINCT FROM admin_email THEN
    RAISE EXCEPTION 'Access denied';
  END IF;

  -- Delete guesses first (FK constraint)
  DELETE FROM game_guesses
  WHERE session_id IN (
    SELECT id FROM game_sessions WHERE user_id = target_user_id
  );

  -- Delete sessions
  DELETE FROM game_sessions WHERE user_id = target_user_id;
  GET DIAGNOSTICS n_del = ROW_COUNT;

  RETURN format('Deleted %s game session(s) for %s', n_del, target_user_id);
END;
$$;


-- ── 2. Delete a player's profile + all games (auth account left intact) ──────
CREATE OR REPLACE FUNCTION admin_delete_player(target_user_id UUID)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  admin_email  CONSTANT TEXT := 'curtisesjunk@gmail.com';
  caller_email TEXT;
  n_del        INT;
BEGIN
  -- Verify caller is admin
  SELECT email INTO caller_email
  FROM auth.users
  WHERE id = auth.uid();

  IF caller_email IS DISTINCT FROM admin_email THEN
    RAISE EXCEPTION 'Access denied';
  END IF;

  -- Delete guesses first (FK constraint)
  DELETE FROM game_guesses
  WHERE session_id IN (
    SELECT id FROM game_sessions WHERE user_id = target_user_id
  );

  -- Delete sessions
  DELETE FROM game_sessions WHERE user_id = target_user_id;
  GET DIAGNOSTICS n_del = ROW_COUNT;

  -- Delete profile
  DELETE FROM profiles WHERE id = target_user_id;

  RETURN format('Deleted player %s with %s game session(s)', target_user_id, n_del);
END;
$$;


-- ── 3. Rename a player's trail name ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION admin_update_player_name(target_user_id UUID, new_name TEXT)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  admin_email  CONSTANT TEXT := 'curtisesjunk@gmail.com';
  caller_email TEXT;
BEGIN
  SELECT email INTO caller_email FROM auth.users WHERE id = auth.uid();
  IF caller_email IS DISTINCT FROM admin_email THEN
    RAISE EXCEPTION 'Access denied';
  END IF;
  IF trim(new_name) = '' THEN
    RAISE EXCEPTION 'Name cannot be empty';
  END IF;
  UPDATE profiles SET trail_name = trim(new_name) WHERE id = target_user_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Player not found';
  END IF;
  RETURN 'Updated name to: ' || trim(new_name);
END;
$$;
