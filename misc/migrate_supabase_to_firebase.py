"""One-time import of the Supabase CSV exports (misc/db-export/) into Firebase.

Dry run by default (validates and prints counts); pass --commit to write.
Safe to re-run: every document keeps its Supabase ID and is overwritten, and
Auth users are imported by uid.

Players keep their Supabase UUID as their Firebase uid. Each is imported with
their Google account ID (google_sub), so signing in with Google on Firebase
lands in the same account — hiker links and leaderboard rows stay valid.

Needs a service-account key: Firebase console → Project settings → Service
accounts → Generate new private key. Keep it outside Google Drive; default
path is ~/.config/pct-geoguesser/firebase-admin-key.json. Delete the key in
Google Cloud console → IAM → Service accounts once the migration is done.

Usage:
  python misc/migrate_supabase_to_firebase.py            # dry run
  python misc/migrate_supabase_to_firebase.py --commit
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

EXPORT      = Path(__file__).resolve().parent / "db-export"
PROJECT_ID  = "pct-geoguesser-9d535"
DEFAULT_KEY = Path.home() / ".config" / "pct-geoguesser" / "firebase-admin-key.json"
BATCH_SIZE  = 400   # Firestore allows 500 writes per batch


def read(name):
    with open(EXPORT / name, newline="") as f:
        return list(csv.DictReader(f))


def ts(s):
    return datetime.fromisoformat(s)


def opt_float(s):
    return float(s) if s != "" else None


def opt_text(s):
    return s if s != "" else None


def load():
    users = read("auth_users.csv")
    profiles = {
        r["id"]: {
            "trail_name": r["trail_name"],
            "pct_year":   r["pct_year"],
            "about":      opt_text(r["about"]),
            "created_at": ts(r["created_at"]),
        }
        for r in read("profiles_rows.csv")
    }
    sessions = {
        r["id"]: {
            "user_id":       r["user_id"],
            "total_score":   float(r["total_score"]),
            "perfect_count": int(r["perfect_count"]),
            "photo_count":   int(r["photo_count"]),
            "played_at":     ts(r["played_at"]),
        }
        for r in read("game_sessions_rows.csv")
    }
    guesses = {
        r["id"]: {
            "session_id":   r["session_id"],
            "photo_id":     r["photo_id"],
            "true_mile":    float(r["true_mile"]),
            "guessed_mile": opt_float(r["guessed_mile"]),
            "score":        float(r["score"]),
            "timed_out":    r["timed_out"] == "true",
        }
        for r in read("game_guesses_rows.csv")
    }
    photo_stats = {
        r["photo_id"]: {
            "appearances":   int(r["appearances"]),
            "n_guesses":     int(r["n_guesses"]),
            "avg_error":     float(r["avg_error"]),
            "m2":            float(r["m2"]),
            "v_var":         float(r["v_var"]),
            "v_sd":          float(r["v_sd"]),
            "perfect_count": int(r["perfect_count"]),
            "updated_at":    ts(r["updated_at"]),
        }
        for r in read("photo_stats_rows.csv")
    }
    settings = {
        r["key"]: {"value": r["value"], "updated_at": ts(r["updated_at"])}
        for r in read("site_settings_rows.csv")
    }
    return users, {
        "profiles":      profiles,
        "game_sessions": sessions,
        "game_guesses":  guesses,
        "photo_stats":   photo_stats,
        "site_settings": settings,
    }


def check(users, colls):
    problems = []
    user_ids = {u["id"] for u in users}
    if missing := [u["id"] for u in users if not u["email"] or not u["google_sub"]]:
        problems.append(f"{len(missing)} auth users lack email or google_sub")
    if orphans := set(colls["profiles"]) - user_ids:
        problems.append(f"{len(orphans)} profiles have no auth user")
    if orphans := {s["user_id"] for s in colls["game_sessions"].values()} - set(colls["profiles"]):
        problems.append(f"{len(orphans)} users with sessions have no profile")
    if orphans := {g["session_id"] for g in colls["game_guesses"].values()} - set(colls["game_sessions"]):
        problems.append(f"{len(orphans)} guess session_ids have no session")
    return problems


def commit(users, colls, key_path):
    import firebase_admin
    from firebase_admin import auth, credentials, firestore

    key_project = json.loads(key_path.read_text())["project_id"]
    if key_project != PROJECT_ID:
        sys.exit(f"Key is for project {key_project!r}, expected {PROJECT_ID!r}")

    firebase_admin.initialize_app(credentials.Certificate(str(key_path)), {"projectId": PROJECT_ID})

    records = [
        auth.ImportUserRecord(
            uid=u["id"],
            email=u["email"],
            email_verified=True,
            provider_data=[auth.UserProvider(uid=u["google_sub"], provider_id="google.com", email=u["email"])],
        )
        for u in users
    ]
    result = auth.import_users(records)
    for err in result.errors:
        print(f"  auth import error (row {err.index}): {err.reason}")
    if result.failure_count:
        sys.exit("Auth import failed; Firestore left untouched.")
    print(f"auth users imported: {result.success_count}")

    db = firestore.client()
    for name, docs in colls.items():
        items = list(docs.items())
        for i in range(0, len(items), BATCH_SIZE):
            batch = db.batch()
            for doc_id, data in items[i:i + BATCH_SIZE]:
                batch.set(db.collection(name).document(doc_id), data)
            batch.commit()
        print(f"{name}: wrote {len(items)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--commit", action="store_true", help="write to Firebase (default: dry run)")
    ap.add_argument("--key", type=Path, default=DEFAULT_KEY, help="service-account key JSON")
    args = ap.parse_args()

    users, colls = load()
    print(f"auth users: {len(users)}")
    for name, docs in colls.items():
        print(f"{name}: {len(docs)}")

    if problems := check(users, colls):
        sys.exit("Export problems:\n  " + "\n  ".join(problems))
    print("export checks passed")

    if not args.commit:
        print("dry run — pass --commit to write")
        return
    if not args.key.is_file():
        sys.exit(f"No service-account key at {args.key}")
    commit(users, colls, args.key)


if __name__ == "__main__":
    main()
