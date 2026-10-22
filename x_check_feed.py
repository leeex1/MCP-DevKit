#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check @Quillan_Ronin's recent posts to avoid duplicates.
Robust login handling for X's changing login flow.
"""

import re
import sys
import time
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


def check_feed():
    creds = parse_credentials(CREDENTIALS_PATH)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        try:
            print("[*] Navigating to X login...")
            page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            # Try multiple selectors for the text input
            print("[*] Looking for username/email field...")
            username_selectors = [
                'input[autocomplete="username"]',
                'input[name="text"]',
                'input[type="text"]',
                'input[data-testid="ocfEnterTextTextInput"]',
                'div[data-testid="ocfEnterTextTextInput"] input',
                'input:not([type="password"]):not([type="hidden"])',
            ]

            username_entered = False
            for sel in username_selectors:
                try:
                    page.wait_for_selector(sel, timeout=5000)
                    page.fill(sel, creds["username"])
                    username_entered = True
                    print(f"    Username entered via: {sel}")
                    break
                except Exception:
                    continue

            if not username_entered:
                print("[!] Could not find username field.")
                return []

            page.wait_for_timeout(2000)

            # Click Next
            print("[*] Clicking Next...")
            next_selectors = [
                'button:has-text("Next")',
                'button:has-text("다음")',
                'div[data-testid="ocfEnterTextNextButton"]',
                'button[data-testid="ocfEnterTextNextButton"]',
            ]
            for sel in next_selectors:
                try:
                    page.click(sel, timeout=5000)
                    break
                except Exception:
                    continue

            page.wait_for_timeout(3000)

            # Password
            print("[*] Entering password...")
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'div[data-testid="ocfEnterPasswordTextInput"] input',
            ]
            password_entered = False
            for sel in password_selectors:
                try:
                    page.wait_for_selector(sel, timeout=5000)
                    page.fill(sel, creds["password"])
                    password_entered = True
                    print(f"    Password entered via: {sel}")
                    break
                except Exception:
                    continue

            if not password_entered:
                print("[!] Could not find password field.")
                return []

            page.wait_for_timeout(2000)

            # Click Log in
            print("[*] Clicking Log in...")
            login_selectors = [
                'button:has-text("Log in")',
                'button:has-text("로그인")',
                'div[data-testid="ocfEnterPasswordNextButton"]',
                'button[data-testid="ocfEnterPasswordNextButton"]',
            ]
            for sel in login_selectors:
                try:
                    page.click(sel, timeout=5000)
                    break
                except Exception:
                    continue

            page.wait_for_timeout(5000)

            # Navigate to profile
            print("[*] Navigating to @Quillan_Ronin profile...")
            page.goto("https://x.com/Quillan_Ronin", wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            # Scroll to load posts
            print("[*] Scrolling to load posts...")
            for i in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)

            # Extract post texts - try multiple selectors
            posts = page.locator('div[data-testid="tweetText"]').all()
            if not posts:
                posts = page.locator('article div[lang]').all()
            if not posts:
                posts = page.locator('article').all()

            if not posts:
                print("[!] No posts found on profile.")
                print(f"    Current URL: {page.url}")
                print(f"    Page title: {page.title()}")
                # Take a screenshot for debugging
                page.screenshot(path="x_profile_debug.png")
                print("    Screenshot saved to x_profile_debug.png")
                return []

            post_texts = []
            for post in posts[:10]:
                text = post.inner_text().strip()
                if text:
                    post_texts.append(text)
                    print(f"  • {text[:150]}...")

            print(f"\n[+] Found {len(post_texts)} recent posts.")
            return post_texts

        except Exception as e:
            print(f"[!] Error: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            browser.close()


if __name__ == "__main__":
    check_feed()
