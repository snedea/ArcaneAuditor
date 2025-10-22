#!/usr/bin/env python3
"""
Automated screenshot capture for Arcane Auditor Learning Game
Uses Playwright to navigate the game and capture key screenshots
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, Page
import time


def setup_directories():
    """Create necessary directories for screenshots"""
    project_root = Path(__file__).parent.parent
    assets_dir = project_root / "assets" / "learning-game"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir


def capture_hero_screenshot(page: Page, output_path: Path):
    """Capture the main menu screen"""
    print("📸 Capturing hero/main menu screenshot...")

    # Wait for the main menu to be visible
    page.wait_for_selector(".menu-content", state="visible")
    page.wait_for_selector(".category-btn", state="visible")

    # Take screenshot
    page.screenshot(path=str(output_path / "game-hero.png"), full_page=False)
    print(f"   ✓ Saved: {output_path / 'game-hero.png'}")


def capture_question_screenshot(page: Page, output_path: Path):
    """Capture a question screen"""
    print("📸 Capturing question screenshot...")

    # Click Script Rules category
    page.click('button[data-category="script"]')
    time.sleep(0.3)

    # Click Easy difficulty
    page.click('button[data-difficulty="easy"]')
    time.sleep(0.3)

    # Click Start Learning
    page.click("#start-game")

    # Wait for quiz screen to load
    page.wait_for_selector("#quiz-screen.active", state="visible")
    page.wait_for_selector(".question-text", state="visible")
    page.wait_for_selector(".answer-btn", state="visible")

    # Wait a moment for everything to render
    time.sleep(0.5)

    # Take screenshot
    page.screenshot(path=str(output_path / "game-question.png"), full_page=False)
    print(f"   ✓ Saved: {output_path / 'game-question.png'}")


def capture_correct_answer_screenshot(page: Page, output_path: Path):
    """Capture a correct answer result screen"""
    print("📸 Capturing correct answer screenshot...")

    # Find the correct answer button
    correct_btn = page.query_selector('button.answer-btn[data-correct="true"]')
    if correct_btn:
        correct_btn.click()
        time.sleep(0.3)

        # Click submit
        page.click("#submit-answer")

        # Wait for result screen
        page.wait_for_selector("#result-screen.active", state="visible")
        page.wait_for_selector("#result-title", state="visible")

        # Wait for animations to complete
        time.sleep(0.8)

        # Take screenshot
        page.screenshot(path=str(output_path / "game-correct.png"), full_page=False)
        print(f"   ✓ Saved: {output_path / 'game-correct.png'}")
    else:
        print("   ⚠ Could not find correct answer button")


def capture_wrong_answer_screenshot(page: Page, output_path: Path):
    """Capture a wrong answer result screen"""
    print("📸 Capturing wrong answer screenshot...")

    # Click next question
    page.click("#next-question")

    # Wait for new question
    page.wait_for_selector("#quiz-screen.active", state="visible")
    page.wait_for_selector(".answer-btn", state="visible")
    time.sleep(0.5)

    # Find a wrong answer button
    wrong_btn = page.query_selector('button.answer-btn[data-correct="false"]')
    if wrong_btn:
        wrong_btn.click()
        time.sleep(0.3)

        # Click submit
        page.click("#submit-answer")

        # Wait for result screen
        page.wait_for_selector("#result-screen.active", state="visible")
        page.wait_for_selector("#result-title", state="visible")

        # Wait for animations to complete
        time.sleep(0.8)

        # Take screenshot
        page.screenshot(path=str(output_path / "game-wrong.png"), full_page=False)
        print(f"   ✓ Saved: {output_path / 'game-wrong.png'}")
    else:
        print("   ⚠ Could not find wrong answer button")


def main():
    """Main screenshot capture workflow"""
    print("🧙‍♂️ Arcane Auditor Learning Game - Screenshot Capture")
    print("=" * 60)

    # Setup
    assets_dir = setup_directories()
    project_root = Path(__file__).parent.parent
    game_path = project_root / "arcane-learning-game" / "index.html"

    if not game_path.exists():
        print(f"❌ Error: Game file not found at {game_path}")
        sys.exit(1)

    print(f"📂 Output directory: {assets_dir}")
    print(f"🎮 Game path: {game_path}")
    print()

    # Launch browser and capture screenshots
    with sync_playwright() as p:
        print("🚀 Launching Chromium browser...")
        browser = p.chromium.launch(headless=True)

        # Create context with specific viewport
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2  # Retina/HiDPI for better quality
        )

        page = context.new_page()

        # Load the game
        print(f"📄 Loading game from file://{game_path}")
        page.goto(f"file://{game_path}")

        # Wait for page to fully load
        page.wait_for_load_state("networkidle")
        time.sleep(1)  # Extra wait for any animations

        try:
            # Capture all screenshots
            capture_hero_screenshot(page, assets_dir)
            capture_question_screenshot(page, assets_dir)
            capture_correct_answer_screenshot(page, assets_dir)
            capture_wrong_answer_screenshot(page, assets_dir)

            print()
            print("=" * 60)
            print("✅ All screenshots captured successfully!")
            print()
            print("📁 Screenshots saved to:")
            for screenshot in ["game-hero.png", "game-question.png", "game-correct.png", "game-wrong.png"]:
                print(f"   - {assets_dir / screenshot}")

        except Exception as e:
            print(f"\n❌ Error during screenshot capture: {e}")
            sys.exit(1)

        finally:
            browser.close()


if __name__ == "__main__":
    main()
