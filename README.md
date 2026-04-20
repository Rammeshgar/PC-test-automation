# 🏥 Peoples Clinic Quality Assurance Suite

[![10-Minute Smoke Test](https://github.com/Rammeshgar/PC-test-automation/actions/workflows/smoke_test.yml/badge.svg)](https://github.com/Rammeshgar/PC-test-automation/actions/workflows/smoke_test.yml)
[![Hourly UI/API Regression Test](https://github.com/Rammeshgar/PC-test-automation/actions/workflows/regression_test.yml/badge.svg)](https://github.com/Rammeshgar/PC-test-automation/actions/workflows/regression_test.yml)
[![FNX AI & Parser Test](https://github.com/Rammeshgar/PC-test-automation/actions/workflows/fnx_test.yml/badge.svg)](https://github.com/Rammeshgar/PC-test-automation/actions/workflows/fnx_test.yml)

A robust, fully automated E2E testing and monitoring infrastructure for the **Peoples Clinic** platform. Built with **Playwright**, **Python**, and **GitHub Actions**, this suite continuously verifies core infrastructure, clinical workflows, and advanced LLM AI features.

---

## 📊 Live Monitoring Dashboard
All test executions are continuously logged to a live, interactive 3D web dashboard built with ECharts and Three.js. 

**👉 [View the Live Status Dashboard Here](https://rammeshgar.github.io/PC-test-automation/) 👈**

<img width="1906" height="972" alt="Screenshot 2026-04-20 192121" src="https://github.com/user-attachments/assets/38e755c6-f894-47bc-80f2-241b2c562b44" />
<img width="1905" height="975" alt="Screenshot 2026-04-20 192257" src="https://github.com/user-attachments/assets/1a61c819-b945-4345-9776-a8126285b756" />
<img width="1907" height="971" alt="Screenshot 2026-04-20 192322" src="https://github.com/user-attachments/assets/8f55b24a-7f7f-4ce1-b030-caae36c4c74e" />

---

## 🏗️ Architecture & Test Suites

This repository executes three distinct automated workflows, each designed to monitor different layers of the application.

### 1. 💨 10-Minute Smoke Test (`smoke_test.py`)
*   **Frequency:** Runs every 10 minutes (`*/10 * * * *`).
*   **Purpose:** Verifies core infrastructure uptime and basic routing.
*   **Execution:** Simulates a user logging in, verifying the dashboard loads (handling bilingual EN/DK UI), opening the profile menu, and logging out successfully.

### 2. 🔍 Hourly E2E Regression (`test_regression.py`)
*   **Frequency:** Runs at the top of every hour (`0 * * * *`).
*   **Purpose:** Validates the entire clinical consultation workflow.
*   **Execution:** 
    *   Generates a dynamic patient profile (Unique CPR via timestamp).
    *   Initiates a live direct consultation.
    *   Injects a real `.webm` audio payload directly into the backend API using session cookies.
    *   Validates the AI Clinical Note generation (SOAP).
    *   Approves the note, submits feedback, and verifies the consultation appears on the recent activity dashboard.

### 3. 🧠 FNX AI & Parser (`test_fnx_ai.py`)
*   **Frequency:** Runs every 2 hours (`15 */2 * * *`).
*   **Purpose:** Tests the proprietary `.FNX` medical file parsing engine and the context-aware LLM chatbot.
*   **Execution:**
    *   Uploads a reference `.FNX` file and asserts the frontend UI successfully extracts and auto-fills the patient details.
    *   Uploads the file to the Patient Analytics module.
    *   Forces the LLM to generate an "AI Patient Summary" and asserts that specific medical anchor words (e.g., *Primcillin*, *Diabetes*) were successfully parsed.
    *   Conducts a multi-turn conversation, validating contextual memory and formatting instructions.

---

## 🚨 Automated Alerting System

The suite is configured to prevent alert fatigue while ensuring critical failures are flagged immediately. 

*   **Failure Screenshots:** If any test fails, Playwright captures screenshots of the exact moment of failure. These are uploaded as GitHub Artifacts and rendered dynamically on the web dashboard.
*   **Working Hours Email Alerts:** If a test fails between **04:00 UTC and 16:00 UTC**, an email is automatically dispatched via SMTP containing:
    *   Direct links to the raw GitHub action logs.
    *   A link to the live dashboard.
    *   The failure screenshots attached directly to the email.
*   **Cooldown Logic:** The 10-Minute Smoke test implements a strict 1-hour cooldown cache for emails. If the platform goes down for 3 hours, the team will only receive 3 emails, not 18.

![Email Alert Screenshot](INSERT_YOUR_EMAIL_ALERT_IMAGE_URL_HERE)

---

## 🛠️ Setup & Local Execution

### 1. Requirements
*   Python 3.11+
*   Playwright

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/Rammeshgar/PC-test-automation.git
cd YOUR_REPO_NAME

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium --with-deps
```

### 3. Environment Variables (.env)
To run the tests locally, create a .env file in the root directory with the following credentials:
```
# Smoke Test Credentials
TEST_USERNAME=your_test_user@peoplesdoctor.ai
TEST_PASSWORD=your_password

# Regression & FNX Test Credentials
ADMIN_USERNAME=your_admin_user@peoplesdoctor.ai
ADMIN_PASSWORD=your_admin_password
```
### 4. Running the Tests
```
# Run the Smoke Test
python smoke_test.py

# Run the Regression Workflow
python test_regression.py

# Run the AI / FNX Workflow
python test_fnx_ai.py
```
