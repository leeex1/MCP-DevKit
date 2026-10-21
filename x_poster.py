#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quillan-Ronin X (Twitter) Poster
Reads credentials from x_credentials.json (locally filled, never committed)
Uses Playwright browser automation to log in and post.
"""

import json
import os
import sys
import time
from pathlib import Path

CREDENTIALS_PATH = Path(__file__).parent / "x_credentials.json"
SESSION_DIR = Path(__file__).parent / "x_session"


def load_credentials() -> dict:
    if not CREDENTIALS_PATH.exists():
        print(f"[!] Credentials file not found: {CREDENTIALS_PATH}")
        print("    Copy x_credentials.template.json to x_credentials.json and fill it in locally.")
        sys.exit(1)

    with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def post_to_x(content: str, creds: dict) -> bool:
    """
    Log into X/Twitter and post content using Playwright.
    Requires: pip install playwright && playwright install chromium
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[!] Playwright not installed. Run: pip install playwright && playwright install chromium")
        return False

    acct = creds.get("x_twitter", {})
    browser_cfg = creds.get("browser", {})

    username = acct.get("username_or_email", "")
    password = acct.get("password", "")

    if "REPLACE_WITH" in username or "REPLACE_WITH" in password:
        print("[!] Credentials not filled in yet. Edit x_credentials.json first.")
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=browser_cfg.get("headless", False),
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            storage_state=str(SESSION_DIR / "state.json") if SESSION_DIR.exists() else None,
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        try:
            page.goto(acct.get("login_url", "https://x.com/i/flow/login"), wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # Username/email
            page.fill('input[autocomplete="username"]', username)
            page.click('button:has-text("Next"), button:has-text("다음")')
            page.wait_for_timeout(2000)

            # Password
            page.fill('input[type="password"]', password)
            page.click('button:has-text("Log in"), button:has-text("로그인")')
            page.wait_for_timeout(5000)

            # Handle 2FA if present
            if acct.get("two_factor_enabled"):
                # 2FA handling would go here
                pass

            # Compose post
            page.click('a[href="/compose/tweet"], a[data-testid="SideNav_NewTweet_Button"]')
            page.wait_for_timeout(2000)

            page.fill('div[data-testid="tweetTextarea_0"], div[role="textbox"]', content)
            page.wait_for_timeout(1000)

            page.click('button[data-testid="tweetButton"], button:has-text("Post")')
            page.wait_for_timeout(3000)

            # Save session
            SESSION_DIR.mkdir(exist_ok=True)
            context.storage_state(path=str(SESSION_DIR / "state.json"))

            print(f"[+] Posted to X (@Quillan_Ronin): {content[:80]}...")
            return True

        except Exception as e:
            print(f"[!] Error during X post: {e}")
            return False
        finally:
            browser.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Post to X as @Quillan_Ronin")
    parser.add_argument("message", nargs="?", help="Message to post")
    args = parser.parse_args()

    creds = load_credentials()
    msg = args.message or "Quillan-Ronin v5.4.0-ONI stack is live. MCP-DevKit, Validation-test-kit-, and quillan.cpp all synced. ⚔️ #QuillanRonin"

    success = post_to_x(msg, creds)
    sys.exit(0 if success else 1)
