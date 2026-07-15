import json
import time

import pytest
from playwright.sync_api import Page, Route, expect


def _mock_hello(page: Page, message: str = "Hello, Test User!", delay_ms: int = 0):
    def handler(route: Route):
        if delay_ms:
            time.sleep(delay_ms / 1000)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"message": message}),
        )
    page.route("**/hello", handler)


# ── Group A: Page Load ──────────────────────────────────────────────────────

def test_page_title(page: Page):
    page.goto("/")
    assert page.title() == "Hello World Agent"


def test_page_heading_contains_claude_agent(page: Page):
    page.goto("/")
    assert "Claude Agent" in page.locator("h1").text_content()


def test_initial_dom_state(page: Page):
    page.goto("/")
    expect(page.locator("#name-input")).to_be_visible()
    expect(page.locator("button")).to_be_visible()
    expect(page.locator("#hello-loading")).to_be_hidden()
    expect(page.locator("#hello-result")).to_be_hidden()


# ── Group B: Form Validation ────────────────────────────────────────────────

def test_empty_name_shows_alert(page: Page):
    page.goto("/")

    alert_text = []

    def on_dialog(dialog):
        alert_text.append(dialog.message)
        dialog.dismiss()

    page.on("dialog", on_dialog)
    page.click("button")

    assert alert_text, "Expected an alert dialog"
    assert "enter your name" in alert_text[0].lower()
    expect(page.locator("#hello-result")).to_be_hidden()


def test_whitespace_only_name_shows_alert(page: Page):
    page.goto("/")

    alert_text = []

    def on_dialog(dialog):
        alert_text.append(dialog.message)
        dialog.dismiss()

    page.on("dialog", on_dialog)
    page.fill("#name-input", "   ")
    page.click("button")

    assert alert_text, "Expected an alert dialog for whitespace-only input"
    assert "enter your name" in alert_text[0].lower()
    expect(page.locator("#hello-result")).to_be_hidden()


# ── Group C: Loading Indicator ──────────────────────────────────────────────

def test_loading_appears_during_slow_request(page: Page):
    page.goto("/")

    # Instrument before the click: record if loading ever becomes visible.
    # Playwright sync calls route handlers inline within page.click(), so we
    # can't check mid-flight from Python — a MutationObserver captures it instead.
    page.evaluate("""() => {
        const el = document.getElementById('hello-loading');
        window._loadingWasVisible = false;
        new MutationObserver(() => {
            if (el.style.display !== 'none') window._loadingWasVisible = true;
        }).observe(el, { attributes: true, attributeFilter: ['style'] });
    }""")

    _mock_hello(page, message="Hello, Slow!", delay_ms=600)
    page.fill("#name-input", "Test")
    page.click("button")

    assert page.evaluate("() => window._loadingWasVisible"), \
        "Loading indicator was never shown during the request"
    expect(page.locator("#hello-result")).to_be_visible(timeout=5000)
    expect(page.locator("#hello-loading")).to_be_hidden()


def test_loading_hidden_after_response(page: Page):
    page.goto("/")
    _mock_hello(page, message="Quick hello!")

    page.fill("#name-input", "Test")
    page.click("button")

    expect(page.locator("#hello-result")).to_be_visible(timeout=5000)
    expect(page.locator("#hello-loading")).to_be_hidden()


# ── Group D: Greeting Flow — Mocked ────────────────────────────────────────

def test_greeting_displays_mocked_message(page: Page):
    page.goto("/")
    mock_msg = "Hi there, Test User! Hope you're having a great day."
    _mock_hello(page, message=mock_msg)

    page.fill("#name-input", "Test User")
    page.click("button")

    expect(page.locator("#hello-result")).to_have_text(mock_msg, timeout=5000)


def test_enter_key_triggers_greeting(page: Page):
    page.goto("/")
    mock_msg = "Hello via Enter key!"
    _mock_hello(page, message=mock_msg)

    page.fill("#name-input", "Keyboard")
    page.press("#name-input", "Enter")

    expect(page.locator("#hello-result")).to_have_text(mock_msg, timeout=5000)


def test_result_box_replaces_previous_result(page: Page):
    page.goto("/")

    call_count = [0]
    messages = ["First greeting!", "Second greeting!"]

    def handler(route: Route):
        idx = min(call_count[0], len(messages) - 1)
        call_count[0] += 1
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"message": messages[idx]}),
        )

    page.route("**/hello", handler)

    page.fill("#name-input", "Alice")
    page.click("button")
    expect(page.locator("#hello-result")).to_have_text("First greeting!", timeout=5000)

    page.fill("#name-input", "Bob")
    page.click("button")
    expect(page.locator("#hello-result")).to_have_text("Second greeting!", timeout=5000)

    assert page.locator("#hello-result").count() == 1


# ── Group E: Real Flask Error Path ─────────────────────────────────────────

def test_invalid_api_key_shows_error_in_result(page: Page):
    page.goto("/")
    page.fill("#name-input", "ErrorTest")
    page.click("button")

    expect(page.locator("#hello-result")).to_be_visible(timeout=10000)
    assert "Error" in page.locator("#hello-result").text_content()
