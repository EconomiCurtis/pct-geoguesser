from __future__ import annotations

import csv
import json
import shutil
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import pytest


TESTING_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TESTING_ROOT.parent


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def photo_rows(project_root: Path) -> list[dict[str, str]]:
    with (project_root / "misc" / "photos.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="session")
def photos_by_id(photo_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["id"]: row for row in photo_rows}


@pytest.fixture(scope="session")
def built_project(tmp_path_factory: pytest.TempPathFactory, project_root: Path) -> Path:
    """Build the real app scripts inside an isolated temporary project."""
    destination = tmp_path_factory.mktemp("pct-built-project")

    for app_dir in (
        "app-landing",
        "app-game",
        "app-leaderboard",
        "app-hiker",
        "app-admin",
    ):
        target = destination / app_dir
        target.mkdir()
        shutil.copy2(project_root / app_dir / "build.py", target / "build.py")

    misc = destination / "misc"
    misc.mkdir()
    shutil.copy2(project_root / "misc" / "photos.csv", misc / "photos.csv")
    (misc / "supabase_config.py").write_text(
        'SUPABASE_URL = "https://testing.invalid"\n'
        'SUPABASE_ANON_KEY = "test-anon-key"\n'
    )

    deploy_misc = destination / "deploy" / "misc"
    deploy_misc.mkdir(parents=True)
    for asset in (project_root / "deploy" / "misc").iterdir():
        if asset.is_file():
            shutil.copy2(asset, deploy_misc / asset.name)

    shutil.copy2(project_root / "build.sh", destination / "build.sh")
    result = subprocess.run(
        ["bash", "build.sh"],
        cwd=destination,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        pytest.fail(
            "Temporary app build failed.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return destination


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        pass


@pytest.fixture(scope="session")
def live_site(built_project: Path):
    handler = partial(_QuietHandler, directory=str(built_project / "deploy"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


_SUPABASE_STUB = """
window.supabase = {
  createClient: function () {
    const query = {
      select() { return this; },
      eq() { return this; },
      gt() { return this; },
      gte() { return this; },
      ilike() { return this; },
      order() { return this; },
      limit() { return this; },
      maybeSingle: async function () { return {data: null, error: null}; },
      then(resolve) { resolve({data: [], error: null, count: 0}); }
    };
    return {
      auth: {
        onAuthStateChange(callback) {
          queueMicrotask(() => callback("INITIAL_SESSION", null));
          return {data: {subscription: {unsubscribe() {}}}};
        },
        getSession: async function () { return {data: {session: null}}; },
        signInWithOAuth: async function () { return {data: null, error: null}; },
        signOut: async function () { return {error: null}; }
      },
      from() { return Object.create(query); },
      rpc: async function () { return {data: null, error: null}; }
    };
  }
};
"""


@pytest.fixture
def local_app(page, live_site: str, project_root: Path):
    """Route remote app assets to local files and block production data access."""
    context = page.context

    def serve_photo(route) -> None:
        filename = Path(unquote(urlparse(route.request.url).path)).name
        local_path = project_root / "deploy" / "miles" / filename
        if local_path.is_file():
            route.fulfill(path=str(local_path))
        else:
            route.fulfill(status=404, body="missing test photo")

    def serve_misc(route) -> None:
        filename = Path(unquote(urlparse(route.request.url).path)).name
        local_path = project_root / "deploy" / "misc" / filename
        if local_path.is_file():
            route.fulfill(path=str(local_path))
        else:
            route.fulfill(status=404, body="missing test asset")

    context.route("https://pct-geoguesser.pages.dev/miles/**", serve_photo)
    context.route("https://pct-geoguesser.economicurtis.com/misc/**", serve_misc)
    context.route(
        "https://fonts.googleapis.com/**",
        lambda route: route.fulfill(status=200, content_type="text/css", body=""),
    )
    context.route(
        "https://fonts.gstatic.com/**",
        lambda route: route.fulfill(status=200, body=""),
    )
    context.route(
        "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js",
        lambda route: route.fulfill(
            status=200,
            content_type="application/javascript",
            body=_SUPABASE_STUB,
        ),
    )
    context.route(
        "https://testing.invalid/**",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps([]),
        ),
    )
    return page, live_site

