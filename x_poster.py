#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quillan-Ronin X (Twitter) Poster
Reads credentials from x_credentials.md (local file, never committed)
Uses Playwright browser automation to log in and post.
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
    """Parse username/password from the markdown credentials file."""
    if not md_path.exists():
        print(f"[!] Credentials file not found: {md_path}")
        sys.exit(1)

    text = md_path.read_text(encoding="utf-8")
    username_match = re.search(r"\|\s*Username / Email\s*\|\s*`([^`]+)`", text)
    password_match = re.search(r"\|\s*Password\s*\|\s*`([^`]+)`", text)
    username = username_match.group(1).strip().split("|")[0].strip().strip("'") if username_match else ""
    password = password_match.group(1).strip() if password_match else ""
    username = username.split("|")[0].strip().strip("'")

    if not username or not password:
        print("[!] Could not parse credentials from x_credentials.md")
        sys.exit(1)

    return {"username": username, "password": password}


def click_button(page, text, timeout=5000):
    """Click a button containing the given text."""
    selectors = [
        'button:has-text("%s")' % text,
        'div[role="button"]:has-text("%s")' % text,
    ]
    for sel in selectors:
        try:
            page.wait_for_selector(sel, timeout=timeout)
            page.click(sel, timeout=timeout)
            return True
        except Exception:
            continue
    return False


def fill_field(page, selectors, value, timeout=5000):
    """Fill a field using one of several selectors."""
    for sel in selectors:
        try:
            page.wait_for_selector(sel, timeout=timeout)
            page.fill(sel, value, timeout=timeout)
            return True
        except Exception:
            continue
    return False


def post_to_x(content: str) -> bool:
    """Log into X/Twitter and post content using Playwright."""
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
            if not fill_field(page, [
                'input[autocomplete="username"]',
                'input[name="text"]',
                'input[type="text"]',
                'input[data-testid="ocfEnterTextTextInput"]',
            ], creds["username"]):
                print("[!] Username field not found.")
                return False

            page.wait_for_timeout(2000)
            page.press('input[type="text"]', 'Enter')
            page.wait_for_timeout(3000)

            # Check if X shows "Use password" button (verification code fallback)
            print("[*] Checking for 'Use password' button...")
            if click_button(page, "Use password", timeout=3000):
                print("[+] Clicked 'Use password'")
                page.wait_for_timeout(3000)

            # Password
            print("[*] Password...")
            if not fill_field(page, [
                'input[type="password"]',
                'input[name="password"]',
                'div[data-testid="ocfEnterPasswordTextInput"] input',
            ], creds["password"]):
                print("[!] Password field not found.")
                page.screenshot(path="x_no_password.png")
                return False

            page.wait_for_timeout(2000)

            # Continue / Log in (try clicking button first, then Enter key as fallback)
            print("[*] Continue / Log in...")
            clicked = click_button(page, "Continue", timeout=5000)
            if not clicked:
                clicked = click_button(page, "Log in", timeout=5000)
            if not clicked:
                # Try pressing Enter on the password field
                try:
                    page.press('input[type="password"]', 'Enter')
                    page.wait_for_timeout(3000)
                    clicked = True
                    print("    Pressed Enter on password field")
                except Exception:
                    pass
            if not clicked:
                print("[!] Continue/Log in button not found.")
                page.screenshot(path="x_no_login.png")
                return False

            page.wait_for_timeout(5000)

            # Go to compose
            print("[*] Going to compose...")
            page.goto("https://x.com/compose/tweet", wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            # Type post
            print("[*] Typing post...")
            text_selectors = [
                'div[data-testid="tweetTextarea_0"]',
                'div[role="textbox"]',
                'div[data-testid="TweetTextarea_0"]',
                'div[contenteditable="true"]',
                'div.public-DraftEditor-content',
            ]

            typed = False
            for sel in text_selectors:
                try:
                    page.wait_for_selector(sel, timeout=5000)
                    page.click(sel, timeout=3000)
                    page.wait_for_timeout(500)
                    page.type(sel, content, delay=5)
                    typed = True
                    print("    Typed via: %s" % sel)
                    break
                except Exception:
                    continue

            if not typed:
                print("[!] Could not type into compose area.")
                page.screenshot(path="x_compose_fail.png")
                return False

            page.wait_for_timeout(1000)

            # Post — try multiple approaches
            print("[*] Posting...")
            posted = False

            # Approach 1: Click enabled "Post" button
            try:
                post_buttons = page.locator('button:has-text("Post")').all()
                for btn in post_buttons:
                    try:
                        if not btn.is_disabled():
                            btn.click(timeout=3000)
                            posted = True
                            print("    Post clicked via enabled button")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Approach 2: Keyboard shortcut Ctrl+Enter (common on Twitter/X)
            if not posted:
                try:
                    page.press('div[data-testid="tweetTextarea_0"]', 'Control+Enter')
                    page.wait_for_timeout(3000)
                    posted = True
                    print("    Posted via Ctrl+Enter shortcut")
                except Exception:
                    pass

            # Approach 3: Try clicking with data-testid
            if not posted:
                try:
                    page.click('button[data-testid="tweetButton"]', timeout=3000)
                    posted = True
                    print("    Post clicked via data-testid")
                except Exception:
                    pass

            if not posted:
                print("[!] Post button not found.")
                page.screenshot(path="x_post_fail.png")
                return False

            page.wait_for_timeout(5000)
            print("[+] Posted to X (@Quillan_Ronin): %s..." % content[:100])
            return True

        except Exception as e:
            print("[!] Error during X post: %s" % e)
            import traceback
            traceback.print_exc()
            return False
        finally:
            browser.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Post to X as @Quillan_Ronin")
    parser.add_argument("message", nargs="?", help="Message to post")
    args = parser.parse_args()

    default_msg = (
        "Quillan-Ronin v5.4.0-ONI stack is live. MCP-DevKit, Validation-test-kit-, "
        "and quillan.cpp all synced across GitHub. 34 council personas, E_ICE governor, "
        "and feedback loop operational. ⚔️ #QuillanRonin"
    )
    msg = args.message or default_msg

    success = post_to_x(msg)
    sys.exit(0 if success else 1)
