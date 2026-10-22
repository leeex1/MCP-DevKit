#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug X compose page - take screenshot and dump HTML
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
            print("[*] Logging in...")
            page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            page.fill('input[type="text"]', creds["username"])
            page.click('button:has-text("Next")')
            page.wait_for_timeout(3000)

            page.fill('input[type="password"]', creds["password"])
            page.click('button:has-text("Log in")')
            page.wait_for_timeout(5000)

            print("[*] Going to compose...")
            page.goto("https://x.com/compose/tweet", wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            page.screenshot(path="x_compose_debug.png")
            print("[+] Screenshot saved to x_compose_debug.png")

            # Dump all input/textarea/div contenteditable elements
            print("\n[*] All editable elements:")
            editable = page.locator('input, textarea, div[contenteditable="true"]').all()
            for i, el in enumerate(editable):
                try:
                    tag = el.evaluate("el => el.tagName")
                    cls = el.evaluate("el => el.className")[:100]
                    testid = el.get_attribute("data-testid") or ""
                    role = el.get_attribute("role") or ""
                    print(f"  {i}: <{tag}> testid={testid!r} role={role!r} class={cls!r}")
                except Exception:
                    pass

            # Also check body text for "Post" button
            print("\n[*] Buttons containing 'Post':")
            btns = page.locator('button').all()
            for btn in btns:
                try:
                    txt = btn.inner_text().strip()[:50]
                    if 'Post' in txt or 'ポスト' in txt:
                        print(f"  Button: {txt!r}")
                except Exception:
                    pass

        except Exception as e:
            print(f"[!] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    debug()
