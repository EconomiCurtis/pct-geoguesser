from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def fail_on_browser_errors(page):
    errors: list[str] = []

    def record_console(message) -> None:
        if message.type == "error":
            errors.append(f"console: {message.text}")

    page.on("console", record_console)
    page.on("pageerror", lambda error: errors.append(f"pageerror: {error}"))
    yield
    assert not errors, "\n".join(errors)

