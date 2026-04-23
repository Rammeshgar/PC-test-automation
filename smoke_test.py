import os
import re
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect

# --- Simple Smoke Test: Login & Logout ---
load_dotenv()
print("--- Starting 10-Minute Smoke Test: Login & Logout ---")

# --- Configuration ---
BASE_APP_URL = "https://clinic.peoplesdoctor.ai"
LOGIN_URL = f"{BASE_APP_URL}/signin"

TEST_USERNAME = os.getenv("TEST_USERNAME")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")
SCREENSHOT_DIR = "test_screenshots_smoke"

if not TEST_USERNAME or not TEST_PASSWORD:
    exit("CRITICAL ERROR: Please set TEST_USERNAME and TEST_PASSWORD in your GitHub Secrets/env.")

# --- Screenshot Setup ---
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
screenshot_counter = 0

def take_screenshot(page, stage_name, status=""):
    """Takes a screenshot and saves it with a sequential, descriptive name."""
    global screenshot_counter
    screenshot_counter += 1
    sanitized_status = re.sub(r'[\\/*?:"<>|]', "", status).replace(" ", "_")
    filename = f"{SCREENSHOT_DIR}/{screenshot_counter:02d}_{stage_name}_{sanitized_status}.png"
    try:
        if page and not page.is_closed():
            page.screenshot(path=filename)
            print(f"   - Screenshot {screenshot_counter:02d} saved to '{filename}'")
    except Exception as e:
        print(f"   - Could not take screenshot: {e}")

# --- Test Execution ---
def run_smoke_test():
    current_stage = "setup"
    page = None

    try:
        with sync_playwright() as p:
            # Set headless=True for GitHub Actions, slow_mo ensures we don't click too fast
            browser = p.chromium.launch(headless=True, slow_mo=500) 
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

            # --- PHASE 1: Login ---
            current_stage = "01_Login"
            print(f"\n--- PHASE: {current_stage} ---")
            page.goto(LOGIN_URL)
            
            # Fill Credentials
            page.locator("input").first.fill(TEST_USERNAME)
            page.locator('input[type="password"]').first.fill(TEST_PASSWORD)
            
            # Bilingual Login check (Log ind / Sign in)
            sign_in_btn = page.get_by_role("button", name=re.compile(r"Log ind|Sign in", re.IGNORECASE)).first
            
            take_screenshot(page, current_stage, "before_signin_click")
            sign_in_btn.click()
            
            # Verify Dashboard loaded successfully
            print("   - Verifying dashboard loaded successfully...")
            expect(page).to_have_url(re.compile(r".*/dashboard"), timeout=20000)
            page.wait_for_timeout(2000) 
            
            # UPDATED: Look for "Recent Consultations" based on the new UI
            expect(page.get_by_text(re.compile(r"Recent Consultations|Seneste Konsultationer", re.IGNORECASE)).first).to_be_visible(timeout=15000)
            
            take_screenshot(page, current_stage, "login_successful_on_dashboard")
            print(f"   - SUCCESS: Logged in and Dashboard is fully visible.")

            # --- PHASE 2: Logout ---
            current_stage = "02_Logout"
            print(f"\n--- PHASE: {current_stage} ---")
            
            # UPDATED: Logout is now directly accessible in the bottom left sidebar menu
            print("   - Clicking Logout in the sidebar...")
            logout_btn = page.get_by_text(re.compile(r"Logout|Log ud", re.IGNORECASE)).first
            expect(logout_btn).to_be_visible(timeout=5000)
            take_screenshot(page, current_stage, "before_logout_click")
            logout_btn.click()

            # Verify successful logout by checking we are back at the Sign In page
            print("   - Verifying successful logout...")
            expect(page).to_have_url(re.compile(r".*/signin"), timeout=15000)
            take_screenshot(page, current_stage, "logout_successful")
            print("   - SUCCESS: Logged out.")

            browser.close()

        print("\n\n--- ✅ SMOKE TEST PASSED ✅ ---")

    except Exception as e:
        print(f"\n--- ❌ TEST FAILED during stage: {current_stage} ❌ ---")
        if page:
            try:
                take_screenshot(page, current_stage, "FAILED")
            except:
                pass
        print("\nDetails:", e)
        raise e
    finally:
        print("--- SCRIPT FINISHED ---")

if __name__ == "__main__":
    run_smoke_test()
