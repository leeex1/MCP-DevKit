#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug X login - screenshot after username
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

            # Username
            print("[*] Username...")
            page.fill('input[type="text"]', creds["username"])
            page.wait_for_timeout(2000)
            page.press('input[type="text"]', 'Enter')
            page.wait_for_timeout(5000)

            # Screenshot after username + Enter
            page.screenshot(path="x_after_username.png")
            print("[+] Screenshot saved to x_after_username.png")

            # Check what's on the page now
            print("[*] Page elements after username Enter:")

            # Check for password field
            pwd_count = page.locator('input[type="password"]').count()
            print(f"  Password fields: {pwd_count}")

            # Check for phone field
            phone_count = page.locator('input[type="tel"]').count()
            print(f"  Phone fields: {phone_count}")

            # Check for any text input
            inputs = page.locator('input').all()
            for i, inp in enumerate(inputs):
                try:
                    itype = inp.get_attribute("type") or "text"
                    iname = inp.get_attribute("name") or ""
                    ivalue = inp.input_value() or ""
                    print("  Input %d: type=%s name=%s value=%s" % (i, repr(itype), repr(iname), repr(ivalue[:30])))
                except Exception:
                    pass

            # Check for buttons
            buttons = page.locator('button').all()
            for i, btn in enumerate(buttons):
                try:
                    txt = btn.inner_text().strip()[:50]
                    if txt:
                        print("  Button %d: %s" % (i, repr(txt)))
                except Exception:
                    pass

            # Check URL
            print("[*] Current URL: %s" % page.url)

        except Exception as e:
            print("[!] Error: %s" % e)
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    debug()
