#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug X compose page - find Post button
"""

import re
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("[!] Playwright not installed.")
    sys.exit(1)

CREDENTIALS_PATH = Path(__file__).parent.parent.parent / "x_credentials.md"


def parse_credentials(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    username_match = re.search(r"\|\s*Username / Email\s*\|\s*`([^`]+)`", text)
    password_match = re.search(r"\|\s*Password\s*\|\s*`([^`]+)`", text)
    username = username_match.group(1).strip().split("|")[0].strip().strip("'") if username_match else ""
    password = password_match.group(1).strip() if password_match else ""
    return {"username": username, "password": password}


def debug():
    creds = parse_credentials(CREDENTIALS_PATH)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        try:
            print("[*] Logging into X...")
            page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            page.fill('input[type="text"]', creds["username"])
            page.wait_for_timeout(2000)
            page.press('input[type="text"]', 'Enter')
            page.wait_for_timeout(3000)

            try:
                page.click('button:has-text("Use password")', timeout=3000)
                page.wait_for_timeout(3000)
            except Exception:
                pass

            page.fill('input[type="password"]', creds["password"])
            page.wait_for_timeout(2000)
            page.press('input[type="password"]', 'Enter')
            page.wait_for_timeout(5000)

            # Go to compose
            page.goto("https://x.com/compose/tweet", wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            # Type post
            page.click('div[data-testid="tweetTextarea_0"]', timeout=3000)
            page.wait_for_timeout(500)
            page.type('div[data-testid="tweetTextarea_0"]', "Test post from Quillan-Ronin debug", delay=5)
            page.wait_for_timeout(1000)

            # Screenshot
            page.screenshot(path="x_compose_debug4.png")
            print("[+] Screenshot saved to x_compose_debug4.png")

            # Find all buttons
            buttons = page.locator('button').all()
            print("[*] All buttons on compose page:")
            for i, btn in enumerate(buttons):
                try:
                    txt = btn.inner_text().strip()[:60]
                    disabled = btn.is_disabled()
                    print("  Button %d: %s disabled=%s" % (i, repr(txt), disabled))
                except Exception:
                    pass

            print("[*] Current URL: %s" % page.url)

        except Exception as e:
            print("[!] Error: %s" % e)
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    debug()
