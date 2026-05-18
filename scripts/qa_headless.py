"""Headless QA harness for the Deșertul de servicii public web app.

Spins up `python -m http.server` against `web/`, drives the app with
Playwright headless Chromium, walks the QA checklist in
`docs/qa-checklist.md`, and emits screenshots to `docs/qa-screenshots/`.

Run from project root:
    .venv/bin/python scripts/qa_headless.py

Exits non-zero on any QA assertion failure or unexpected console error.
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import ConsoleMessage, Page, Route, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
SCREENSHOT_DIR = ROOT / "docs" / "qa-screenshots"
PORT = 8765
BASE_URL = f"http://localhost:{PORT}/"

# Playwright 1.40 ships with Chromium 1091, which segfaults on recent macOS
# arm64. Prefer the newer Chrome-for-Testing 1223 binary if present.
_CHROME_TESTING = (
    Path.home()
    / "Library/Caches/ms-playwright/chromium-1223/chrome-mac-arm64"
    / "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
)
CHROME_EXECUTABLE = str(_CHROME_TESTING) if _CHROME_TESTING.exists() else None


class QAFailure(Exception):
    pass


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        try:
            s.connect(("127.0.0.1", port))
            return True
        except OSError:
            return False


@contextmanager
def http_server():
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT)],
        cwd=str(WEB_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        # Wait for socket to accept
        for _ in range(50):
            if _port_open(PORT):
                break
            time.sleep(0.1)
        else:
            raise QAFailure(f"http.server failed to open port {PORT}")
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def must(cond: bool, label: str, detail: str = "") -> None:
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail else ""))
    if not cond:
        raise QAFailure(f"{label}: {detail}")


def main() -> int:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    console_errors: list[str] = []
    plausible_events: list[dict] = []

    def on_console(msg: ConsoleMessage) -> None:
        if msg.type == "error":
            # Ignore favicon 404 noise — the app has no favicon configured.
            location = msg.location or {}
            url = (location.get("url") or "")
            if "favicon" in url.lower() or "favicon" in msg.text.lower():
                return
            console_errors.append(msg.text)
            print(f"  [console.error] {msg.text} @ {url}")
        else:
            # Helpful when diagnosing — show warnings/info
            if msg.type in ("warning",):
                print(f"  [console.{msg.type}] {msg.text}")

    # The production Plausible script no-ops on localhost. For QA we substitute
    # a tiny shim that exposes a counting `window.plausible` and forwards each
    # call to a POST that we capture below.
    PLAUSIBLE_SHIM = """
    (function () {
      window.plausible = window.plausible || function (name, opts) {
        try {
          fetch('https://plausible.io/api/event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ n: name, p: (opts && opts.props) || {} }),
            keepalive: true,
          });
        } catch (e) { /* swallow */ }
      };
    })();
    """

    def handle_plausible(route: Route) -> None:
        req = route.request
        if req.method == "POST" and "/api/event" in req.url:
            try:
                body = req.post_data_json or json.loads(req.post_data or "{}")
            except (ValueError, TypeError):
                body = {"raw": req.post_data}
            plausible_events.append(body)
            route.fulfill(status=202, body="ok", content_type="text/plain")
            return
        # Replace the Plausible JS bundle with our counter shim.
        route.fulfill(status=200, body=PLAUSIBLE_SHIM, content_type="application/javascript")

    with http_server(), sync_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": [
                "--no-sandbox",
                # MapLibre needs WebGL. In headless Chromium on macOS arm64 the
                # GPU process is sandboxed away — fall back to SwiftShader.
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
                "--ignore-gpu-blocklist",
            ],
        }
        if CHROME_EXECUTABLE:
            launch_kwargs["executable_path"] = CHROME_EXECUTABLE
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        context.route("**/plausible.io/**", handle_plausible)
        page: Page = context.new_page()
        page.on("console", on_console)

        def on_pageerror(exc):
            console_errors.append(f"pageerror: {exc}")
            print(f"  [pageerror] {exc}")

        page.on("pageerror", on_pageerror)

        def on_requestfailed(req):
            # surface only non-favicon failures
            if "favicon" not in (req.url or "").lower():
                print(f"  [requestfailed] {req.url} -- {req.failure}")

        page.on("requestfailed", on_requestfailed)

        def on_response(resp):
            if resp.status >= 400 and "favicon" not in resp.url.lower():
                print(f"  [http {resp.status}] {resp.url}")

        page.on("response", on_response)

        # --- Load page
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_function("window.__map_ready === true", timeout=20000)
        # MapLibre needs the tiles/source to render; wait until the uats source
        # has features queryable from a rendered viewport.
        page.wait_for_function(
            "window.map && window.map.getSource('uats') && "
            "window.map.querySourceFeatures('uats').length > 0",
            timeout=20000,
        )

        # --- 99 UAT polygons in source
        feature_count = page.evaluate("window.uatsGeo ? window.uatsGeo.features.length : null")
        if feature_count is None:
            # Fall back to fetching the geojson directly through the same server.
            feature_count = page.evaluate(
                "fetch('data/uats_timis.geojson').then(r => r.json()).then(d => d.features.length)"
            )
        must(feature_count == 99, "99 UAT polygons in dataset", f"got {feature_count}")

        # Composite fills: every feature should have a non-grey _display_color or _color_composite
        composite_painted = page.evaluate(
            "(() => { const src = window.map.getSource('uats')._data; "
            "return src.features.filter(f => f.properties._color_composite && "
            "f.properties._color_composite !== '#9a9a9a').length; })()"
        )
        must(composite_painted >= 90, "Composite view paints most UATs", f"painted={composite_painted}/99")

        # --- Screenshot: desktop composite (initial)
        page.screenshot(path=str(SCREENSHOT_DIR / "desktop-composite.png"), full_page=False)

        # --- Click Timișoara via permalink (faster + deterministic than canvas click)
        page.evaluate("window.location.hash = '#timisoara-tm'")
        page.wait_for_timeout(600)
        panel_text = page.text_content("#detail-panel") or ""
        must("Timișoara" in panel_text, "Timișoara detail panel populated", f"panel={panel_text[:80]!r}")

        # --- Click a rural bottom-decile UAT via permalink
        rural_targets = ["beba-veche-tm", "cenad-tm", "dudestii-vechi-tm", "sanpetru-mare-tm", "gataia-tm"]
        rural_hit = None
        for slug in rural_targets:
            page.evaluate(f"window.location.hash = '#{slug}'")
            page.wait_for_timeout(400)
            txt = page.text_content("#detail-panel") or ""
            # Detail panel for that UAT: name appears in h2
            if txt and txt.strip() and "Timișoara" not in txt[:60]:
                rural_hit = (slug, txt)
                break
        must(rural_hit is not None, "Rural bottom-decile UAT panel populated",
             f"tried {rural_targets}")
        if rural_hit:
            print(f"  rural-hit: {rural_hit[0]} -> {rural_hit[1][:80]!r}")

        # --- View toggles: composite -> school -> hospital
        errors_before = len(console_errors)
        for view in ["school", "hospital", "composite"]:
            page.click(f'button[data-view="{view}"]')
            page.wait_for_timeout(400)
            must(len(console_errors) == errors_before,
                 f"view toggle '{view}' fires no console.error",
                 f"new errors: {console_errors[errors_before:]}")

        # --- Permalink: bogus uat hash is silent
        errors_before = len(console_errors)
        page.evaluate("window.location.hash = '#bogus-uat-tm'")
        page.wait_for_timeout(400)
        must(len(console_errors) == errors_before, "#bogus-uat-tm silent",
             f"new errors: {console_errors[errors_before:]}")

        # --- Permalink fires Plausible (count before/after)
        events_before = len(plausible_events)
        page.evaluate("window.location.hash = '#timisoara-tm'")
        page.wait_for_timeout(700)
        permalink_events = [
            e for e in plausible_events[events_before:]
            if (e.get("n") or e.get("name") or "") in ("permalink_visit",)
        ]
        must(len(permalink_events) >= 1, "Plausible permalink_visit event fired",
             f"new events={plausible_events[events_before:]}")

        view_events_before = len(plausible_events)
        page.click('button[data-view="school"]')
        page.wait_for_timeout(500)
        page.click('button[data-view="composite"]')
        page.wait_for_timeout(500)
        view_events = [
            e for e in plausible_events[view_events_before:]
            if (e.get("n") or e.get("name") or "") == "view_mode_change"
        ]
        must(len(view_events) >= 1, "Plausible view_mode_change event fired",
             f"new events={plausible_events[view_events_before:]}")

        # --- EN toggle
        page.click("#lang-toggle")
        page.wait_for_timeout(300)
        html_lang = page.evaluate("document.documentElement.lang")
        must(html_lang == "en", "documentElement.lang flips to 'en'", f"got {html_lang!r}")
        brand_text = page.text_content("#top-bar h1") or ""
        must(
            "Service Desert" in brand_text or "Banat" in brand_text and "Deșertul" not in brand_text,
            "Brand H1 switched to EN",
            f"h1={brand_text!r}",
        )

        # Footer disclaimer present in EN
        footer_en = page.text_content("footer") or ""
        must("independent civic" in footer_en or "abolishing" in footer_en,
             "Footer disclaimer present (EN)", f"footer={footer_en[:120]!r}")

        # Screenshot EN state
        page.screenshot(path=str(SCREENSHOT_DIR / "desktop-en.png"), full_page=False)

        # Toggle back to RO to check disclaimer text
        page.click("#lang-toggle")
        page.wait_for_timeout(300)
        footer_ro = page.text_content("footer") or ""
        must("inițiativă civică" in footer_ro and "desființarea" in footer_ro,
             "Footer disclaimer present (RO)", f"footer={footer_ro[:120]!r}")

        # --- "desființare" appears only in the disclaimer
        body_text = page.evaluate("document.body.textContent") or ""
        # Match the root word (any Romanian suffix) without double-counting.
        import re
        matches = list(re.finditer(r"desființare\w*", body_text.lower()))
        count = len(matches)
        for m in matches:
            s = max(0, m.start() - 40)
            e = min(len(body_text), m.end() + 40)
            print(f"  desf-match: ...{body_text[s:e]!r}...")
        # The disclaimer contains one occurrence ("desființarea localităților").
        # Tagline is "Investiție, nu desființare." — that's a second occurrence,
        # also a denial. Both are framing-safe; flag anything beyond 2.
        must(count <= 2,
             "'desființare' only appears in denial framing (tagline + disclaimer)",
             f"count={count}")
        must("Investiție, nu desființare" in body_text,
             "Tagline 'Investiție, nu desființare' present", "")

        # --- Mobile viewport
        page.set_viewport_size({"width": 375, "height": 812})
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("window.__map_ready === true", timeout=20000)
        page.wait_for_timeout(800)
        # No horizontal overflow: documentElement.scrollWidth <= clientWidth + small tolerance
        overflow = page.evaluate(
            "({sw: document.documentElement.scrollWidth, "
            "cw: document.documentElement.clientWidth})"
        )
        must(overflow["sw"] <= overflow["cw"] + 1,
             "Mobile viewport has no horizontal overflow",
             f"scrollWidth={overflow['sw']} clientWidth={overflow['cw']}")
        # Map fills: #map clientWidth ≈ viewport width
        map_w = page.evaluate("document.getElementById('map').clientWidth")
        must(map_w >= 320, "Mobile map fills viewport", f"map width={map_w}")
        page.screenshot(path=str(SCREENSHOT_DIR / "mobile-composite.png"), full_page=False)

        # --- Final console hygiene
        must(len(console_errors) == 0,
             "No JS console errors across the run",
             f"errors={console_errors}")

        # --- Summary
        print("")
        print("=== QA SUMMARY ===")
        print(f"Plausible events captured: {len(plausible_events)}")
        for ev in plausible_events:
            print(f"  - {ev.get('n') or ev.get('name')} props={ev.get('p') or ev.get('props')}")
        print(f"Screenshots written to: {SCREENSHOT_DIR}")
        for path in sorted(SCREENSHOT_DIR.glob("*.png")):
            print(f"  - {path.name} ({path.stat().st_size} bytes)")

        context.close()
        browser.close()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except QAFailure as e:
        print(f"\n!!! QA FAILURE: {e}", file=sys.stderr)
        sys.exit(2)
