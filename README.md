# 🏥 Peoples Clinic Quality Assurance Suite

[![10-Minute Smoke Test](https://github.com/Rammeshgar/PC-test-automation/actions/workflows/smoke_test.yml/badge.svg)](https://github.com/Rammeshgar/PC-test-automation/actions/workflows/smoke_test.yml?v=1)
[![Hourly UI/API Regression Test](https://github.com/Rammeshgar/PC-test-automation/actions/workflows/regression_test.yml/badge.svg)](https://github.com/Rammeshgar/PC-test-automation/actions/workflows/regression_test.yml?v=1)
[![FNX AI & Parser Test](https://github.com/Rammeshgar/PC-test-automation/actions/workflows/fnx_test.yml/badge.svg)](https://github.com/Rammeshgar/PC-test-automation/actions/workflows/fnx_test.yml?v=1)

A robust, fully automated E2E testing and monitoring infrastructure for the **Peoples Clinic** platform. Built with **Playwright**, **Python**, and **GitHub Actions**, this suite continuously verifies core infrastructure, clinical workflows, and advanced LLM AI features.

---

## 📊 Live Monitoring Dashboard
All test executions are continuously logged to a live, interactive web dashboard built with ECharts and Three.js. 

**👉 [View the Live Status Dashboard Here](https://rammeshgar.github.io/PC-test-automation/) 👈**

*   **Neon 2D & 3D WebGL Matrices:** Visualize test stability over time. Click on any data point to view execution details and screenshots from that exact run.
*   **Execution Data Table:** Switch to the Data Table view to see a detailed history of all workflow runs.
*   **Export Capabilities:** QA Leads and managers can instantly export historical execution logs to **CSV (Excel)**, **JSON**, or **Plain Text**.

<table align="center">
  <tr>
    <td align="center">
      <img width="600" alt="Dashboard 2D View" src="https://github.com/user-attachments/assets/38e755c6-f894-47bc-80f2-241b2c562b44" />
    </td>
    <td align="center">
      <img width="600" alt="Dashboard 3D View" src="https://github.com/user-attachments/assets/1a61c819-b945-4345-9776-a8126285b756" />
    </td>
    <td align="center">
      <img width="600" alt="Dashboard Data Table" src="https://github.com/user-attachments/assets/8f55b24a-7f7f-4ce1-b030-caae36c4c74e" />
    </td>
  </tr>
</table>

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

<table align="center">
  <tr>
    <td align="center">
      <img width="1920" height="1080" alt="Email Alert Screenshot" src="https://github.com/user-attachments/assets/803143af-173a-46b1-9d5d-c3630a294501" />
    </td>
    <td align="center">
      <img width="1899" height="976" alt="Failure Artifact Screenshot" src="https://github.com/user-attachments/assets/02f6b2c1-a00a-4fad-bb8b-53f12d0cdce1" />
    </td>
  </tr>
</table>

---

## 🛠️ Setup & Local Execution

### 1. Requirements
*   Python 3.11+
*   Playwright
*   Ensure `test-audio.webm` and the `test_data/` folder exist in your root directory.

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/Rammeshgar/PC-test-automation.git
cd PC-test-automation

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium --with-deps
```

### 3. Environment Variables (.env)
To run the tests locally, create a `.env` file in the root directory with the following credentials:
```env
# Smoke Test Credentials
TEST_USERNAME=your_test_user@peoplesdoctor.ai
TEST_PASSWORD=your_password

# Regression & FNX Test Credentials
ADMIN_USERNAME=your_admin_user@peoplesdoctor.ai
ADMIN_PASSWORD=your_admin_password
```

### 4. Running the Tests
```bash
# Run the Smoke Test
python smoke_test.py

# Run the Regression Workflow
python test_regression.py

# Run the AI / FNX Workflow
python test_fnx_ai.py
```
