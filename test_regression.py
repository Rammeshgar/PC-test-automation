import os
import re
import time
import json
import base64
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect

# --- E2E Regression Monitor: Perfect WebM API Injection ---
load_dotenv()
TEST_NAME = "UI Regression - Direct Consultation (WebM API Inject)"
print(f"--- Playwright Monitor: {TEST_NAME} ---")

# --- Configuration ---
BASE_APP_URL = "https://clinic.peoplesdoctor.ai"
LOGIN_URL = f"{BASE_APP_URL}/signin"

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME") 
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
AUDIO_FILE_PATH = "test-audio.webm" 
SCREENSHOT_DIR = "monitor_screenshots_regression"

if not ADMIN_USERNAME or not ADMIN_PASSWORD: 
    exit("CRITICAL ERROR: Missing credentials in environment. Check your GitHub Secrets!")
if not os.path.exists(AUDIO_FILE_PATH): 
    exit(f"CRITICAL ERROR: Audio file not found at '{AUDIO_FILE_PATH}'. Did you commit it to GitHub?")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
screenshot_counter = 0

def take_screenshot(page, stage_name, status=""):
    global screenshot_counter
    screenshot_counter += 1
    sanitized_status = re.sub(r'[\\/*?:"<>|]', "", status)
    filename = f"{SCREENSHOT_DIR}/{screenshot_counter:02d}_{stage_name}_{sanitized_status}.png"
    try:
        page.screenshot(path=filename)
        print(f"   - Screenshot {screenshot_counter:02d} saved: '{status}'")
    except Exception as e:
        pass

def inject_webm_via_api(token, cookies, consultation_id):
    print("   - Injecting identical WebM audio payload into LIVE session via API...")
    trans_url = f"{BASE_APP_URL}/api/live/transcription"
    headers = {
        'Authorization': f'Bearer {token}', 'Cookie': cookies, 'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'{BASE_APP_URL}/consultation/live/{consultation_id}'
    }
    
    with open(AUDIO_FILE_PATH, 'rb') as f:
        audio_bytes = f.read()
    
    raw_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    payload = {
        "consultation_id": consultation_id, 
        "transcription": raw_base64,
        "mimeType": "audio/webm;codecs=opus" 
    }
    
    response = requests.post(trans_url, headers=headers, json=payload)
    try:
        response.raise_for_status()
        print(f"   - SUCCESS: WebM Audio accepted by Backend API.")
    except Exception as e:
        print(f"   - ❌ API ERROR RESPONSE: {response.text}")
        raise e

def run_regression():
    current_stage = "setup"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=500) 
        context = browser.new_context(viewport={"width": 1920, "height": 1080}, permissions=[])
        page = context.new_page()
        
        try:
            # --- PHASE 1: Sign In ---
            current_stage = "01_Sign_In"
            print(f"\n--- PHASE: {current_stage} ---")
            page.goto(LOGIN_URL)
            page.locator("input").first.fill(ADMIN_USERNAME)
            page.locator('input[type="password"]').first.fill(ADMIN_PASSWORD)
            
            sign_in_btn = page.get_by_role("button", name=re.compile(r"Log ind|Sign in", re.IGNORECASE)).first
            take_screenshot(page, current_stage, "before_click_sign_in")
            sign_in_btn.click()
            take_screenshot(page, current_stage, "after_click_sign_in")
            
            expect(page).to_have_url(re.compile(r".*/dashboard"), timeout=20000)
            page.wait_for_timeout(2000) 
            print("   - SUCCESS: Signed into Dashboard.")

            # --- PHASE 2: Select English Language ---
            current_stage = "02_Select_Language"
            print(f"\n--- PHASE: {current_stage} ---")
            try:
                en_flag = page.locator("img[src*='gb'], img[src*='en'], img[alt*='English'], img[alt*='UK']").first
                if en_flag.is_visible():
                    take_screenshot(page, current_stage, "before_click_language_flag")
                    en_flag.click(timeout=5000)
                    take_screenshot(page, current_stage, "after_click_language_flag")
                    time.sleep(2) 
            except Exception: pass

            # --- PHASE 3: Start Consultation Directly ---
            current_stage = "03_Start_Direct_Consultation"
            print(f"\n--- PHASE: {current_stage} ---")
            
            # Generate Dynamic Patient Name
            now = datetime.now(ZoneInfo("Europe/Budapest"))
            dynamic_first_name = f"Auto{now.strftime('%H%M')}" 
            dynamic_family_name = f"Test{now.strftime('%Y%m%d')}"
            full_patient_name = f"{dynamic_first_name} {dynamic_family_name}"
            
            # Generate Dynamic CPR (10 digits)
            cpr_first_six = now.strftime('%H%M%S') 
            cpr_last_four = now.strftime('%d%m')
            full_cpr = f"{cpr_first_six}{cpr_last_four}"
            
            print(f"   - Entering Patient Name: {full_patient_name}")
            print(f"   - Entering CPR: {cpr_first_six}-{cpr_last_four}")
            
            # UPDATED: Single CPR Input field
            cpr_input = page.get_by_placeholder(re.compile(r"CPR-Number|CPR-nummer", re.IGNORECASE)).first
            cpr_input.fill(full_cpr)

            # UPDATED: Single Patient Name Input field
            name_input = page.get_by_placeholder(re.compile(r"Patient Name|Patientnavn", re.IGNORECASE)).first
            name_input.fill(full_patient_name, force=True)
            
            # Press Escape to close any Mantine autocomplete dropdowns
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            
            start_btn_regex = re.compile(r"Start (Consultation|Konsultation)", re.IGNORECASE)
            start_btn = page.get_by_role("button", name=start_btn_regex).last
            
            take_screenshot(page, current_stage, "before_click_start_consultation")
            start_btn.click()
            take_screenshot(page, current_stage, "after_click_start_consultation")
            
            live_page_url_pattern = re.compile(r"/consultation/live/(\d+)")
            expect(page).to_have_url(live_page_url_pattern, timeout=15000)
            consultation_id = live_page_url_pattern.search(page.url).group(1)
            
            print(f"   - SUCCESS: Consultation is LIVE with ID: {consultation_id}")

            # --- PHASE 4: Inject Full WebM via API ---
            current_stage = "04_Inject_Audio"
            print(f"\n--- PHASE: {current_stage} ---")
            
            all_cookies = context.cookies()
            token = next((c['value'] for c in all_cookies if 'token' in c['name'].lower() or 'auth' in c['name'].lower() or 'pc-cookie' in c['name'].lower()), None)
            
            if not token:
                raise Exception("Cannot find auth token in Cookies! The developers might have logged you out.")

            print("   - ✅ Successfully extracted Auth Token from Cookies.")

            cookies_str = "; ".join([f"{c['name']}={c['value']}" for c in all_cookies])
            
            inject_webm_via_api(token, cookies_str, consultation_id)
            
            print("   - Waiting 5 seconds for backend to process the audio file...")
            time.sleep(5)
            take_screenshot(page, current_stage, "live_transcription_visible_before_finish")

# --- PHASE 5: Finish Consultation ---
            current_stage = "05_Finish_Consultation"
            print(f"\n--- PHASE: {current_stage} ---")
            
            finish_btn = page.get_by_role("button", name=re.compile(r"Finish & Edit Note", re.IGNORECASE)).first
            take_screenshot(page, current_stage, "before_click_finish_consultation")
            finish_btn.click()
            take_screenshot(page, current_stage, "after_click_finish_consultation")
            
            # UPDATED: Use get_by_text instead of heading role, because the devs likely used a <div>
            expect(page.get_by_text(re.compile(r"Edit and Save Note", re.IGNORECASE)).first).to_be_visible(timeout=60000)

# --- PHASE 6: Validate Transcription & Save ---
            current_stage = "06_Validate_and_Save"
            print(f"\n--- PHASE: {current_stage} ---")
            
            # UPDATED: The loading text changed in the new UI!
            print("   - Waiting for 'Note is being generated...' loader to disappear...")
            expect(page.get_by_text(re.compile(r"Note is being generated", re.IGNORECASE))).to_be_hidden(timeout=90000)
            
            # Adding a tiny pause to allow the text to fully render in the DOM after the loader disappears
            page.wait_for_timeout(1500) 
            
            # Look for the editor content
            note_editor = page.locator('.rich-text-content, .ProseMirror, .mantine-TypographyStylesProvider-root').first
            
            # UPDATED: Looking specifically for alphanumeric characters rather than just any regex character
            expect(note_editor).to_have_text(re.compile(r"[a-zA-Z]"), timeout=15000)
            
            note_text = note_editor.inner_text()
            print(f"   - Extracted AI Note Text (first 100 chars): {note_text[:100]}...")
            
            if len(note_text) < 30 or "No transcription available" in note_text or "Der mangler" in note_text:
                raise Exception(f"AI Note failed to generate correctly. Output: '{note_text}'")
            else:
                print("   - ✅ SUCCESS: Rich transcription content is present!")
            
            approve_btn = page.get_by_role("button", name=re.compile(r"Approve & Save Note", re.IGNORECASE)).first
            take_screenshot(page, current_stage, "before_click_approve_and_save")
            approve_btn.click()
            take_screenshot(page, current_stage, "after_click_approve_and_save")

# --- PHASE 7: Provide Feedback (Rating) ---
            current_stage = "07_Provide_Feedback"
            print(f"\n--- PHASE: {current_stage} ---")
            
            # UPDATED: The modal is now titled "How accurate was the note?"
            feedback_modal = page.get_by_role("dialog")
            expect(feedback_modal.get_by_text(re.compile(r"How accurate was the note", re.IGNORECASE)).first).to_be_visible(timeout=10000)
            
            # UPDATED: Rating is now 1-10 buttons. Let's select '10'.
            # We use exact=True so it doesn't accidentally match other numbers.
            rating_btn = feedback_modal.get_by_text("10", exact=True).first
            take_screenshot(page, current_stage, "before_click_rating_10")
            rating_btn.click()
            take_screenshot(page, current_stage, "after_click_rating_10")
            
            # UPDATED: Submit button is now "SEND FEEDBACK"
            submit_feedback_btn = feedback_modal.get_by_role("button", name=re.compile(r"SEND FEEDBACK", re.IGNORECASE)).first
            take_screenshot(page, current_stage, "before_click_submit_feedback")
            submit_feedback_btn.click()
            take_screenshot(page, current_stage, "after_click_submit_feedback")
            
            expect(feedback_modal).to_be_hidden(timeout=10000)

            # --- PHASE 8: Verify Main Dashboard ---
            current_stage = "08_Verify_Dashboard"
            print(f"\n--- PHASE: {current_stage} ---")
            
            expect(page.get_by_role("button", name=re.compile(r"Start Consultation", re.IGNORECASE)).first).to_be_visible(timeout=20000)
            time.sleep(3) 
            take_screenshot(page, current_stage, "dashboard_loaded_before_table_check")
            
            # Check the table using ONLY the unique Time-based first six numbers of the CPR
            expect(page.get_by_text(cpr_first_six).first).to_be_visible(timeout=15000)
            print(f"   - ✅ SUCCESS: Consultation with CPR starting with '{cpr_first_six}' is visible in Recent Activity.")
            take_screenshot(page, current_stage, "final_success_dashboard")

            print(f"\n\n--- ✅ ✅ ✅ REGRESSION TEST PASSED ✅ ✅ ✅ ---")
            time.sleep(3)

        except Exception as e:
            print(f"\n--- ❌ ❌ ❌ TEST FAILED during stage: {current_stage} ❌ ❌ ❌ ---")
            if 'page' in locals():
                take_screenshot(page, current_stage, "FAILED")
            time.sleep(10) 
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run_regression()
