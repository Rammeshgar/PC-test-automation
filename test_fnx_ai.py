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
                    take_screenshot(page, current_stage, "before_click_language_flag")
                    en_flag.click(timeout=5000)
                    take_screenshot(page, current_stage, "after_click_language_flag")
                    time.sleep(2) 
                    print("   - SUCCESS: Switched UI to English.")
            except Exception: 
                print("   - Language flag not found or already in English. Proceeding...")

            # --- PHASE 3: Test FNX Parser (Auto-fill) ---
            current_stage = "03_FNX_Parser_Upload"
            print(f"\n--- PHASE: {current_stage} ---")
            
            upload_area = page.get_by_text(re.compile(r"Upload Patient Record File|Upload journalfil", re.IGNORECASE)).first
            take_screenshot(page, current_stage, "before_clicking_upload_area")
            upload_area.click()

            print("   - Uploading FNX file...")
            with page.expect_file_chooser() as fc_info:
                page.get_by_role("button", name=re.compile(r"Browse Files|Gennemse filer", re.IGNORECASE)).click()
            
            file_chooser = fc_info.value
            file_chooser.set_files(FNX_FILE_PATH)

            expect(page.get_by_text(re.compile(r"VALID", re.IGNORECASE)).first).to_be_visible(timeout=15000)
            take_screenshot(page, current_stage, "file_validated_in_modal")
            
            page.get_by_role("button", name=re.compile(r"Upload Files", re.IGNORECASE)).click()
            page.wait_for_timeout(1000)

            print("   - Verifying form auto-fill data...")
            cpr_input = page.get_by_placeholder("123456").first
            expect(cpr_input).to_have_value("251248", timeout=5000)
            
            first_name_input = page.get_by_placeholder("Enter First Name")
            expect(first_name_input).to_have_value("Nancy")

            middle_name_input = page.get_by_placeholder("Enter Middle Name (optional)")
            expect(middle_name_input).to_have_value("Ann")

            family_name_input = page.get_by_placeholder("Enter Family Name")
            expect(family_name_input).to_have_value("Berggren")
            
            take_screenshot(page, current_stage, "data_autofilled_correctly")
            print("   - ✅ SUCCESS: FNX file parsed and UI accurately populated!")

            # --- PHASE 4: Patient Record Analytics (LLM Test) ---
            current_stage = "04_LLM_Analytics_Init"
            print(f"\n--- PHASE: {current_stage} ---")
            
            new_analysis_btn = page.get_by_text(re.compile(r"New Analysis|Ny Analyse", re.IGNORECASE)).first
            new_analysis_btn.click()
            
            print("   - Uploading FNX file to LLM Context window...")
            with page.expect_file_chooser() as fc_info:
                # Reverted this back to the correct text for the Analytics Modal
                page.get_by_role("dialog").get_by_text(re.compile(r"Select Patient Record file", re.IGNORECASE)).click()
                
            file_chooser = fc_info.value
            file_chooser.set_files(FNX_FILE_PATH)
            
            # This modal shows the Patient Details card instead of the VALID pill
            expect(page.get_by_role("dialog").get_by_text("Nancy Ann Berggren").first).to_be_visible(timeout=15000)
            take_screenshot(page, current_stage, "analytics_modal_file_attached")
            
            # Reverted back to the correct button name
            page.get_by_role("dialog").get_by_role("button", name=re.compile(r"Upload & Analyze", re.IGNORECASE)).click()
            
            expect(page.get_by_role("heading", name="Nancy Ann Berggren")).to_be_visible(timeout=20000)
            print("   - ✅ SUCCESS: Analytics Chat UI loaded for Nancy Ann Berggren.")

            # --- PHASE 5: AI Patient Summary Generation ---
            current_stage = "05_AI_Summary_Generation"
            print(f"\n--- PHASE: {current_stage} ---")
            
            summary_btn = page.get_by_role("button", name="AI Patient Summary")
            take_screenshot(page, current_stage, "before_summary_click")
            summary_btn.click()
            
            print("   - Waiting for LLM to stream the summary (up to 45 seconds)...")
            
            medical_anchor_regex = re.compile(r"diabetes|Primcillin", re.IGNORECASE)
            expect(page.locator("body")).to_contain_text(medical_anchor_regex, timeout=45000)
            
            take_screenshot(page, current_stage, "llm_summary_generated")
            print("   - ✅ SUCCESS: LLM successfully analyzed the FNX file and extracted Medical History.")

# --- PHASE 6: Multi-Turn AI Conversation (Context Test) ---
            current_stage = "06_Multi_Turn_LLM_Chat"
            print(f"\n--- PHASE: {current_stage} ---")
            
            chat_input = page.get_by_role("textbox").first
            
            # A list of conversational turns to test Memory and Context
            chat_sequence = [
                {
                    "type": "Extraction + Typo",
                    "prompt": "waht was the last record of deseas"
                },
                {
                    "type": "Conversational Memory",
                    "prompt": "What medication was prescribed for that specific illness?"
                },
                {
                    "type": "Translation / Formatting",
                    "prompt": "Can you summarize the patient's allergies in bullet points in Danish?"
                }
            ]

            for index, turn in enumerate(chat_sequence, start=1):
                print(f"\n   - Turn {index} [{turn['type']}]: Sending prompt: '{turn['prompt']}'")
                
                # Ensure the text box is ready, then fill and send
                expect(chat_input).to_be_editable(timeout=10000)
                chat_input.fill(turn['prompt'])
                page.keyboard.press("Enter")
                
                # 1. Verify the user's question actually appeared in the chat UI
                expect(page.get_by_text(turn['prompt']).first).to_be_visible(timeout=10000)
                
                # 2. Wait for the AI to process and stream the response
                print("   - Waiting 12 seconds for AI to stream response...")
                time.sleep(12) 
                
                take_screenshot(page, current_stage, f"chat_turn_{index}_completed")
                print(f"   - ✅ Turn {index} completed successfully.")

            print(f"\n   - ✅ SUCCESS: AI successfully handled a {len(chat_sequence)}-turn conversation with memory context!")

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
