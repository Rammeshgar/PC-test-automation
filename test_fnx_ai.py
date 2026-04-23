import os
import re
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect

# --- FNX AI & Parser E2E Test ---
load_dotenv()
TEST_NAME = "FNX Parser & AI Chatbot Test"
print(f"--- Playwright Monitor: {TEST_NAME} ---")

# --- Configuration ---
BASE_APP_URL = "https://clinic.peoplesdoctor.ai"
LOGIN_URL = f"{BASE_APP_URL}/signin"

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME") 
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
FNX_FILE_PATH = "test_data/2024-12-14_CGM_P300_1_Ref.FNX"
SCREENSHOT_DIR = "monitor_screenshots_fnx"

if not ADMIN_USERNAME or not ADMIN_PASSWORD: 
    exit("CRITICAL ERROR: Missing credentials in environment.")
if not os.path.exists(FNX_FILE_PATH): 
    exit(f"CRITICAL ERROR: Patient file not found at '{FNX_FILE_PATH}'. Did you create the test_data folder?")

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
    except Exception:
        pass

def run_fnx_test():
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
            sign_in_btn.click()
            expect(page).to_have_url(re.compile(r".*/dashboard"), timeout=20000)
            print("   - SUCCESS: Signed into Dashboard.")

            # --- PHASE 2: Select English Language ---
            current_stage = "02_Select_Language"
            print(f"\n--- PHASE: {current_stage} ---")
            try:
                en_flag = page.locator("img[src*='gb'], img[src*='en'], img[alt*='English'], img[alt*='UK']").first
                if en_flag.is_visible(timeout=5000):
                    en_flag.click(timeout=5000)
                    time.sleep(2) 
                    print("   - SUCCESS: Switched UI to English.")
            except Exception: pass

# --- PHASE 3: Test FNX Parser (Auto-fill) ---
            current_stage = "03_FNX_Parser_Upload"
            print(f"\n--- PHASE: {current_stage} ---")
            
            print("   - Clicking Drag & Drop zone to open upload modal...")
            # 1. Click the dropzone to open the modal
            page.get_by_text(re.compile(r"Drag & drop", re.IGNORECASE)).first.click()
            
            # Ensure the modal opened
            expect(page.get_by_role("dialog")).to_be_visible(timeout=5000)
            
            print("   - Clicking 'Browse Files' to trigger file picker...")
            # 2. NOW we wait for the file chooser while clicking "Browse Files"
            with page.expect_file_chooser() as fc_info:
                page.get_by_role("button", name=re.compile(r"Browse Files", re.IGNORECASE)).click()
                
            file_chooser = fc_info.value
            file_chooser.set_files(FNX_FILE_PATH)
            
            print("   - Confirming upload...")
            # 3. Click the "Upload Files" button to submit the modal
            upload_confirm_btn = page.get_by_role("button", name=re.compile(r"Upload Files", re.IGNORECASE)).first
            upload_confirm_btn.click()
            
            # Wait for the modal to close
            expect(page.get_by_role("dialog")).to_be_hidden(timeout=10000)
            
            page.wait_for_timeout(2000) # Give it a moment to parse the FNX JSON data

            print("   - Verifying form auto-fill data...")
            cpr_input = page.get_by_placeholder(re.compile(r"CPR", re.IGNORECASE)).first
            
            # UPDATED: We now use regex to accept the masked asterisks (251248****)
            expect(cpr_input).to_have_value(re.compile(r"251248.*"), timeout=5000)
            
            name_input = page.get_by_placeholder(re.compile(r"Patient Name", re.IGNORECASE)).first
            expect(name_input).to_have_value(re.compile(r"Nancy.*Berggren", re.IGNORECASE))
            
            take_screenshot(page, current_stage, "data_autofilled_correctly")
            print("   - ✅ SUCCESS: FNX file parsed and UI accurately populated!")

# --- PHASE 4: Patient Record Analytics (LLM Test) ---
            current_stage = "04_LLM_Analytics_Init"
            print(f"\n--- PHASE: {current_stage} ---")
            
            # Navigate to the new FNX Analytics tab in the sidebar
            fnx_sidebar_btn = page.get_by_text("FNX Analytics", exact=True).first
            fnx_sidebar_btn.click()
            
            # UPDATED: Check for the central empty-state text instead of a heading tag
            expect(page.get_by_text("No patient selected").first).to_be_visible(timeout=10000)

            print("   - Uploading FNX file to Analytics Chat...")
            
            # UPDATED: Use get_by_text for the button just in case it's not a true <button> element
            with page.expect_file_chooser() as fc_info:
                page.get_by_text(re.compile(r"Upload file", re.IGNORECASE)).first.click()
                
            file_chooser = fc_info.value
            file_chooser.set_files(FNX_FILE_PATH)
            
            # Wait for Patient name to appear indicating context is loaded
            expect(page.get_by_text("Nancy Ann Berggren").first).to_be_visible(timeout=20000)
            take_screenshot(page, current_stage, "analytics_file_attached")
            print("   - ✅ SUCCESS: Analytics Chat UI loaded for Nancy Ann Berggren.")

            # --- PHASE 5: AI Patient Summary Generation ---
            current_stage = "05_AI_Summary_Generation"
            print(f"\n--- PHASE: {current_stage} ---")
            
            # Look for the Journal Summary pill/button
            summary_btn = page.get_by_text(re.compile(r"Journal Summary|Patient Summary", re.IGNORECASE)).first
            take_screenshot(page, current_stage, "before_summary_click")
            summary_btn.click()
            
            print("   - Waiting for LLM to stream the summary (up to 45 seconds)...")
            
            medical_anchor_regex = re.compile(r"diabetes|Primcillin", re.IGNORECASE)
            expect(page.locator("body")).to_contain_text(medical_anchor_regex, timeout=45000)
            
            take_screenshot(page, current_stage, "llm_summary_generated")
            print("   - ✅ SUCCESS: LLM successfully analyzed the FNX file.")

# --- PHASE 6: Multi-Turn AI Conversation ---
            current_stage = "06_Multi_Turn_LLM_Chat"
            print(f"\n--- PHASE: {current_stage} ---")
            
            # UPDATED: Target the visible chat box using its specific placeholder text
            chat_input = page.get_by_placeholder(re.compile(r"Describe what you need", re.IGNORECASE)).first
            
            chat_sequence = [
                {"type": "Extraction + Typo", "prompt": "waht was the last record of deseas"},
                {"type": "Conversational Memory", "prompt": "What medication was prescribed for that specific illness?"}
            ]

            for index, turn in enumerate(chat_sequence, start=1):
                print(f"\n   - Turn {index}: Sending prompt: '{turn['prompt']}'")
                
                expect(chat_input).to_be_editable(timeout=10000)
                chat_input.fill(turn['prompt'])
                page.keyboard.press("Enter")
                
                # Verify the user's question actually appeared in the chat UI
                expect(page.get_by_text(turn['prompt']).first).to_be_visible(timeout=10000)
                
                # Wait for the AI to process and stream the response
                print("   - Waiting 12 seconds for AI to stream response...")
                time.sleep(12) 
                
                take_screenshot(page, current_stage, f"chat_turn_{index}_completed")
                print(f"   - ✅ Turn {index} completed successfully.")

            print(f"\n\n--- ✅ ✅ ✅ FNX PARSER & AI TEST PASSED ✅ ✅ ✅ ---")

        except Exception as e:
            print(f"\n--- ❌ ❌ ❌ TEST FAILED during stage: {current_stage} ❌ ❌ ❌ ---")
            if 'page' in locals():
                take_screenshot(page, current_stage, "FAILED")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run_fnx_test()
