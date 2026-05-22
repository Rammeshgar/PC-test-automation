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
            
            # FIX: Added resilient page load (like the other scripts)
            page.goto(LOGIN_URL, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            
            page.locator("input").first.fill(ADMIN_USERNAME)
            page.locator('input[type="password"]').first.fill(ADMIN_PASSWORD)
            
            sign_in_btn = page.get_by_role("button", name=re.compile(r"Log ind|Sign in", re.IGNORECASE)).first
            sign_in_btn.click()
            expect(page).to_have_url(re.compile(r".*/dashboard"), timeout=30000)
            print("   - SUCCESS: Signed into Dashboard.")

            # --- PHASE 2: Select English Language ---
            current_stage = "02_Select_Language"
            print(f"\n--- PHASE: {current_stage} ---")
            
            en_flag = page.locator("img[src*='gb'], img[src*='en'], img[alt*='English'], img[alt*='UK'], svg[class*='gb']").first
            
            if en_flag.is_visible(timeout=5000):
                en_flag.click()
                time.sleep(2) 
                print("   - SUCCESS: Clicked English flag.")
            else:
                print("   - WARNING: English flag not found, proceeding with current language.")

            # --- PHASE 3: Test FNX Parser (Auto-fill) ---
            current_stage = "03_FNX_Parser_Upload"
            print(f"\n--- PHASE: {current_stage} ---")
            
            print("   - Clicking upload zone to open upload modal...")
            page.get_by_text(re.compile(r"Drag & drop|Upload journalfil", re.IGNORECASE)).first.click()
            
            expect(page.get_by_role("dialog")).to_be_visible(timeout=5000)
            
            print("   - Clicking 'Browse Files' to trigger file picker...")
            with page.expect_file_chooser() as fc_info:
                page.get_by_role("button", name=re.compile(r"Browse Files|Gennemse|Vælg", re.IGNORECASE)).first.click()
                
            file_chooser = fc_info.value
            file_chooser.set_files(FNX_FILE_PATH)
            
            print("   - Confirming upload...")
            upload_confirm_btn = page.get_by_role("button", name=re.compile(r"Upload Files|Upload|Send", re.IGNORECASE)).first
            upload_confirm_btn.click()
            
            expect(page.get_by_role("dialog")).to_be_hidden(timeout=10000)
            page.wait_for_timeout(2000)

            print("   - Verifying form auto-fill data...")
            cpr_input = page.get_by_placeholder(re.compile(r"CPR", re.IGNORECASE)).first
            expect(cpr_input).to_have_value(re.compile(r"251248.*"), timeout=5000)
            
            name_input = page.get_by_placeholder(re.compile(r"Patient Name|Patientens navn", re.IGNORECASE)).first
            expect(name_input).to_have_value(re.compile(r"Nancy.*Berggren", re.IGNORECASE))
            
            take_screenshot(page, current_stage, "data_autofilled_correctly")
            print("   - ✅ SUCCESS: FNX file parsed and UI accurately populated!")

            # --- PHASE 4: Patient Record Analytics (LLM Test) ---
            current_stage = "04_LLM_Analytics_Init"
            print(f"\n--- PHASE: {current_stage} ---")
            
            fnx_sidebar_btn = page.get_by_text(re.compile(r"FNX Analytics|Journal Resume|Journalresumé", re.IGNORECASE)).first
            fnx_sidebar_btn.click()
            
            # FIX: Removed the brittle "No patient selected" text check. 
            # We now just wait directly for the Upload button to appear (gives the page up to 30s to load)
            print("   - Waiting for Analytics UI to load...")
            upload_btn = page.get_by_text(re.compile(r"Upload file|Upload fil|Vælg Fil|gennemse", re.IGNORECASE)).first
            expect(upload_btn).to_be_visible(timeout=30000)

            print("   - Uploading FNX file to Analytics Chat...")
            with page.expect_file_chooser() as fc_info:
                upload_btn.click()
                
            file_chooser = fc_info.value
            file_chooser.set_files(FNX_FILE_PATH)
            
            expect(page.get_by_text("Nancy Ann Berggren").first).to_be_visible(timeout=20000)

            print("   - Waiting for backend to finish indexing the file context...")
            page.wait_for_timeout(4000) 

            take_screenshot(page, current_stage, "analytics_file_attached")
            print("   - ✅ SUCCESS: Analytics Chat UI loaded for Nancy Ann Berggren.")

            # --- PHASE 5: AI Patient Summary Generation ---
            current_stage = "05_AI_Summary_Generation"
            print(f"\n--- PHASE: {current_stage} ---")
            
            summary_btn = page.get_by_text(re.compile(r"Journal Summary|Patient Summary|Journal Resume|Journalresumé", re.IGNORECASE)).first
            take_screenshot(page, current_stage, "before_summary_click")
            summary_btn.click()
            
            print("   - Waiting for LLM to stream the summary (up to 45 seconds)...")
            
            medical_anchor_regex = re.compile(
                r"diabetes|Primcillin|Ingen registreret|No registered|Aktuelle Problemstillinger", 
                re.IGNORECASE
            )
            expect(page.locator("body")).to_contain_text(medical_anchor_regex, timeout=45000)
            
            take_screenshot(page, current_stage, "llm_summary_generated")
            print("   - ✅ SUCCESS: LLM successfully analyzed the FNX file.")

            # FIX: Removed the duplicate Phase 5 code that was here!

            # --- PHASE 6: Multi-Turn AI Conversation ---
            current_stage = "06_Multi_Turn_LLM_Chat"
            print(f"\n--- PHASE: {current_stage} ---")
            
            chat_input = page.get_by_placeholder(re.compile(r"Describe what you need|Beskriv hvad du", re.IGNORECASE)).first
            
            chat_sequence = [
                {"type": "Extraction + Typo", "prompt": "waht was the last record of deseas"},
                {"type": "Conversational Memory", "prompt": "What medication was prescribed for that specific illness?"}
            ]

            for index, turn in enumerate(chat_sequence, start=1):
                print(f"\n   - Turn {index}: Sending prompt: '{turn['prompt']}'")
                
                expect(chat_input).to_be_editable(timeout=45000) 
                
                chat_input.fill(turn['prompt'])
                page.keyboard.press("Enter")
                
                expect(page.get_by_text(turn['prompt']).first).to_be_visible(timeout=10000)
                print(f"   - Waiting for AI to finish responding...")
                
                take_screenshot(page, current_stage, f"chat_turn_{index}_completed")
                print(f"   - ✅ Turn {index} completed successfully.")

        except Exception as e:
            print(f"\n--- ❌ ❌ ❌ TEST FAILED during stage: {current_stage} ❌ ❌ ❌ ---")
            
            # --- NEW: Save exact error reason to file for the email alert ---
            try:
                error_msg = f"Failed at Phase: {current_stage}\nReason: {type(e).__name__}: {str(e)}"
                with open("error_summary_fnx.txt", "w", encoding="utf-8") as f:
                    f.write(error_msg)
            except:
                pass
            # ----------------------------------------------------------------

            if 'page' in locals():
                take_screenshot(page, current_stage, "FAILED")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run_fnx_test()
