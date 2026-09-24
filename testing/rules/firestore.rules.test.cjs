// Firestore security-rules tests. Run with testing/rules/run.sh (starts the
// local Firestore emulator; never touches the real project).
//
// CommonJS so NODE_PATH can point at dependencies installed outside Google
// Drive (~/.cache/pct-geoguesser-rules-test).

const { test, describe, before, after, beforeEach } = require('node:test');
const fs = require('node:fs');
const {
  initializeTestEnvironment, assertSucceeds, assertFails,
} = require('@firebase/rules-unit-testing');
const {
  doc, collection, getDoc, getDocs, setDoc, updateDoc, deleteDoc,
  writeBatch, serverTimestamp, increment, Timestamp, setLogLevel,
} = require('firebase/firestore');

// Denied writes are the point of most tests; don't log each one.
setLogLevel('silent');

const PLAYER = 'player1';
const OTHER  = 'player2';
const ADMIN_UID = '1791279a-bd07-4345-9448-e06ce5807d97';

let env;

const anon   = () => env.unauthenticatedContext().firestore();
const player = (uid = PLAYER) =>
  env.authenticatedContext(uid, { email: `${uid}@example.com`, email_verified: true }).firestore();
const admin  = () =>
  env.authenticatedContext(ADMIN_UID, { email: 'admin@example.com', email_verified: true }).firestore();

const ago = ms => Timestamp.fromMillis(Date.now() - ms);

async function seed({ gameCount = 0, lastGameAgoMs = null } = {}) {
  await env.withSecurityRulesDisabled(async ctx => {
    const db = ctx.firestore();
    const base = { trail_name: 'Tester', pct_year: '2025', about: null, created_at: ago(864e5) };
    const p1 = { ...base, game_count: gameCount };
    if (lastGameAgoMs !== null) p1.last_game_at = ago(lastGameAgoMs);
    await setDoc(doc(db, 'profiles', PLAYER), p1);
    await setDoc(doc(db, 'profiles', OTHER), { ...base, trail_name: 'Other' });
    await setDoc(doc(db, 'game_sessions', 'AAAAAAAAAAAAAAAAAAAA'), {
      user_id: OTHER, total_score: 900, perfect_count: 0, photo_count: 10, played_at: ago(864e5),
    });
    await setDoc(doc(db, 'game_guesses', 'AAAAAAAAAAAAAAAAAAAA_0'), {
      session_id: 'AAAAAAAAAAAAAAAAAAAA', photo_id: 'abcde', true_mile: 10, guessed_mile: 20, score: 90, timed_out: false,
    });
    await setDoc(doc(db, 'site_settings', 'primary_font'), { value: 'futura', updated_at: ago(0) });
    await setDoc(doc(db, 'photo_stats', 'abcde'), { appearances: 1 });
  });
}

// Mirrors submitGameScore() in app-game/build.py; opts override pieces to
// build malicious variants.
function gameBatch(db, uid = PLAYER, opts = {}) {
  const batch = writeBatch(db);
  const sid = opts.sid ?? doc(collection(db, 'game_sessions')).id;
  const now = serverTimestamp();
  if (opts.profile !== false) {
    batch.update(doc(db, 'profiles', uid), {
      game_count: increment(opts.inc ?? 1),
      last_game_at: now,
      last_session_id: opts.lastSessionId ?? sid,
      ...(opts.profileExtra ?? {}),
    });
  }
  batch.set(doc(db, 'game_sessions', sid), {
    user_id: opts.userId ?? uid,
    total_score: opts.score ?? 1200.5,
    perfect_count: opts.perfect ?? 2,
    photo_count: opts.count ?? 10,
    played_at: opts.playedAt ?? now,
    ...(opts.sessionExtra ?? {}),
  });
  const ids = opts.guessIds ?? Array.from({ length: 10 }, (_, i) => `${sid}_${i}`);
  ids.forEach((gid, i) => batch.set(doc(db, 'game_guesses', gid), {
    session_id: sid, photo_id: 'abcde', true_mile: 100.5,
    guessed_mile: i === 0 ? null : 120, score: opts.guessScore ?? 120.25, timed_out: i === 0,
  }));
  return { batch, sid };
}

before(async () => {
  env = await initializeTestEnvironment({
    projectId: 'demo-pct-geoguesser',
    firestore: { rules: fs.readFileSync(process.env.RULES_FILE, 'utf8'), host: '127.0.0.1', port: 8085 },
  });
});
after(async () => { await env.cleanup(); });
beforeEach(async () => { await env.clearFirestore(); await seed(); });

describe('public reads', () => {
  test('anyone can read leaderboard data and settings', async () => {
    const db = anon();
    await assertSucceeds(getDocs(collection(db, 'game_sessions')));
    await assertSucceeds(getDocs(collection(db, 'profiles')));
    await assertSucceeds(getDocs(collection(db, 'game_guesses')));
    await assertSucceeds(getDoc(doc(db, 'site_settings', 'primary_font')));
    await assertSucceeds(getDoc(doc(db, 'photo_stats', 'abcde')));
  });

  test('signed-out visitors cannot write anything', async () => {
    const db = anon();
    await assertFails(setDoc(doc(db, 'profiles', 'x'), { trail_name: 'x', pct_year: '1', created_at: serverTimestamp() }));
    await assertFails(setDoc(doc(db, 'game_sessions', 'BBBBBBBBBBBBBBBBBBBB'), { user_id: 'x' }));
    await assertFails(setDoc(doc(db, 'site_settings', 'primary_font'), { value: 'open-sans' }));
    await assertFails(deleteDoc(doc(db, 'game_sessions', 'AAAAAAAAAAAAAAAAAAAA')));
  });
});

describe('profiles', () => {
  const fresh = extra => ({ trail_name: 'Newbie', pct_year: '2026', about: null, created_at: serverTimestamp(), ...extra });

  test('a player can create their own profile', async () => {
    await assertSucceeds(setDoc(doc(player('newbie'), 'profiles', 'newbie'), fresh()));
  });
  test('cannot create a profile for someone else', async () => {
    await assertFails(setDoc(doc(player('newbie'), 'profiles', 'victim'), fresh()));
  });
  test('cannot create a profile with game counters or extra fields', async () => {
    await assertFails(setDoc(doc(player('newbie'), 'profiles', 'newbie'), fresh({ game_count: -100 })));
    await assertFails(setDoc(doc(player('newbie'), 'profiles', 'newbie'), fresh({ email: 'a@b.c' })));
  });
  test('cannot backdate created_at', async () => {
    await assertFails(setDoc(doc(player('newbie'), 'profiles', 'newbie'), fresh({ created_at: ago(1e10) })));
  });
  test('trail name must be 1–60 chars, year 1–40, about ≤ 1000', async () => {
    const db = player('newbie');
    await assertFails(setDoc(doc(db, 'profiles', 'newbie'), fresh({ trail_name: '' })));
    await assertFails(setDoc(doc(db, 'profiles', 'newbie'), fresh({ trail_name: 'x'.repeat(61) })));
    await assertFails(setDoc(doc(db, 'profiles', 'newbie'), fresh({ pct_year: 'x'.repeat(41) })));
    await assertFails(setDoc(doc(db, 'profiles', 'newbie'), fresh({ about: 'x'.repeat(1001) })));
    await assertFails(setDoc(doc(db, 'profiles', 'newbie'), fresh({ trail_name: 42 })));
  });
  test('owner can edit name, year and about', async () => {
    await assertSucceeds(updateDoc(doc(player(), 'profiles', PLAYER), { trail_name: 'Renamed', pct_year: '2024', about: 'hi' }));
  });
  test('owner cannot reset their game counters', async () => {
    await env.clearFirestore(); await seed({ gameCount: 15, lastGameAgoMs: 5000 });
    const ref = doc(player(), 'profiles', PLAYER);
    await assertFails(updateDoc(ref, { game_count: 0 }));
    await assertFails(updateDoc(ref, { last_game_at: ago(1e9) }));
  });
  test('cannot change created_at, edit someone else, or delete own profile', async () => {
    await assertFails(updateDoc(doc(player(), 'profiles', PLAYER), { created_at: ago(1e10) }));
    await assertFails(updateDoc(doc(player(), 'profiles', OTHER), { trail_name: 'Hacked' }));
    await assertFails(deleteDoc(doc(player(), 'profiles', PLAYER)));
  });
});

describe('saving a scored game', () => {
  test('a normal game save succeeds', async () => {
    await assertSucceeds(gameBatch(player()).batch.commit());
  });
  test('a first-ever save works for a player with no counters yet', async () => {
    await env.clearFirestore(); await seed();
    await assertSucceeds(gameBatch(player()).batch.commit());
  });
  test('rate limit: a second game within a minute is rejected', async () => {
    await env.clearFirestore(); await seed({ gameCount: 3, lastGameAgoMs: 30 * 1000 });
    await assertFails(gameBatch(player()).batch.commit());
  });
  test('rate limit: a game more than a minute later is accepted', async () => {
    await env.clearFirestore(); await seed({ gameCount: 3, lastGameAgoMs: 61 * 1000 });
    await assertSucceeds(gameBatch(player()).batch.commit());
  });
  test('back-to-back saves: the second is rejected', async () => {
    await assertSucceeds(gameBatch(player()).batch.commit());
    await assertFails(gameBatch(player()).batch.commit());
  });
  test('cap: the 16th game is rejected', async () => {
    await env.clearFirestore(); await seed({ gameCount: 15, lastGameAgoMs: 864e5 });
    await assertFails(gameBatch(player()).batch.commit());
    await env.clearFirestore(); await seed({ gameCount: 14, lastGameAgoMs: 864e5 });
    await assertSucceeds(gameBatch(player()).batch.commit());
  });
  test('out-of-range scores are rejected', async () => {
    for (const opts of [{ score: 9999 }, { score: -1 }, { score: '1000' }, { perfect: 11 }, { perfect: -1 }, { count: 0 }, { guessScore: 300 }, { guessScore: -5 }]) {
      await assertFails(gameBatch(player(), PLAYER, opts).batch.commit(), JSON.stringify(opts));
    }
  });
  test('a session without the profile counter update is rejected', async () => {
    await assertFails(gameBatch(player(), PLAYER, { profile: false }).batch.commit());
  });
  test('two sessions in one save are rejected', async () => {
    const db = player();
    const { batch, sid } = gameBatch(db);
    const sid2 = doc(collection(db, 'game_sessions')).id;
    batch.set(doc(db, 'game_sessions', sid2), {
      user_id: PLAYER, total_score: 2600, perfect_count: 10, photo_count: 10, played_at: serverTimestamp(),
    });
    await assertFails(batch.commit(), `extra session next to ${sid}`);
  });
  test('cannot post a session as another player', async () => {
    await assertFails(gameBatch(player(), PLAYER, { userId: OTHER }).batch.commit());
  });
  test('cannot backdate played_at', async () => {
    await assertFails(gameBatch(player(), PLAYER, { playedAt: ago(1e10) }).batch.commit());
  });
  test('cannot add extra fields to a session', async () => {
    await assertFails(gameBatch(player(), PLAYER, { sessionExtra: { verified: true } }).batch.commit());
  });
  test('game counter must go up by exactly one, with no other profile changes', async () => {
    await assertFails(gameBatch(player(), PLAYER, { inc: 2 }).batch.commit());
    await assertFails(gameBatch(player(), PLAYER, { inc: 0 }).batch.commit());
    await assertFails(gameBatch(player(), PLAYER, { profileExtra: { trail_name: 'Sneaky' } }).batch.commit());
  });
  test('session id must be a Firestore auto-ID', async () => {
    await assertFails(gameBatch(player(), PLAYER, { sid: '.*' }).batch.commit());
    await assertFails(gameBatch(player(), PLAYER, { sid: 'short' }).batch.commit());
  });
  test('only guesses _0.._9 of that session may be written', async () => {
    const db = player();
    const sid = doc(collection(db, 'game_sessions')).id;
    await assertFails(gameBatch(db, PLAYER, { sid, guessIds: [`${sid}_10`] }).batch.commit());
    await assertFails(gameBatch(db, PLAYER, { sid, guessIds: [`other_${sid}_1`] }).batch.commit());
  });
  test('cannot add guesses to an existing session later', async () => {
    await assertFails(setDoc(doc(player(OTHER), 'game_guesses', 'AAAAAAAAAAAAAAAAAAAA_5'), {
      session_id: 'AAAAAAAAAAAAAAAAAAAA', photo_id: 'abcde', true_mile: 10, guessed_mile: 10, score: 265, timed_out: false,
    }));
  });
  test('players cannot edit or delete saved games', async () => {
    const db = player(OTHER);
    await assertFails(updateDoc(doc(db, 'game_sessions', 'AAAAAAAAAAAAAAAAAAAA'), { total_score: 2600 }));
    await assertFails(deleteDoc(doc(db, 'game_sessions', 'AAAAAAAAAAAAAAAAAAAA')));
    await assertFails(deleteDoc(doc(db, 'game_guesses', 'AAAAAAAAAAAAAAAAAAAA_0')));
  });
  test('nobody can write legacy photo_stats', async () => {
    await assertFails(setDoc(doc(player(), 'photo_stats', 'abcde'), { appearances: 999 }));
    await assertFails(setDoc(doc(admin(), 'photo_stats', 'abcde'), { appearances: 999 }));
  });
});

describe('admin', () => {
  test('admin can change settings; other accounts cannot', async () => {
    await assertSucceeds(setDoc(doc(admin(), 'site_settings', 'primary_font'), { value: 'open-sans', updated_at: serverTimestamp() }));
    await assertFails(setDoc(doc(player(), 'site_settings', 'primary_font'), { value: 'open-sans' }));
    const lookAlike = env.authenticatedContext('evil', { email: 'admin@example.com', email_verified: true }).firestore();
    await assertFails(setDoc(doc(lookAlike, 'site_settings', 'primary_font'), { value: 'open-sans' }));
  });
  test('admin can rename, reset counters and delete players and games', async () => {
    const db = admin();
    await assertSucceeds(updateDoc(doc(db, 'profiles', OTHER), { trail_name: 'Cleaned Up' }));
    await assertSucceeds(updateDoc(doc(db, 'profiles', OTHER), { game_count: 0 }));
    await assertSucceeds(deleteDoc(doc(db, 'game_guesses', 'AAAAAAAAAAAAAAAAAAAA_0')));
    await assertSucceeds(deleteDoc(doc(db, 'game_sessions', 'AAAAAAAAAAAAAAAAAAAA')));
    await assertSucceeds(deleteDoc(doc(db, 'profiles', OTHER)));
  });
  test('admin still cannot write invalid profile data', async () => {
    await assertFails(updateDoc(doc(admin(), 'profiles', OTHER), { trail_name: 'x'.repeat(61) }));
  });
});
