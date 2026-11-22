# Peoples Clinic Quality Assurance Suite (Archived)

> **Archived since November 2026.** I developed this monitoring suite during my previous work at FRAIA. Scheduled tests and alerts have been disabled. The repository and dashboard are retained as historical examples of QA automation; they do not report the current health of Peoples Clinic.

[View the archived dashboard](https://rammeshgar.github.io/PC-test-automation/) · [Read the project case study](https://rammeshgar.github.io/qa-suite/)

## What the suite did

The system used Python, Playwright and GitHub Actions to schedule browser and API workflow checks, save results and capture evidence for review. An ECharts and Three.js dashboard brought run history, charts, screenshots and exports together.

| Historical check | Former schedule | Status |
| --- | --- | --- |
| Smoke monitoring | Every 10 minutes | Disabled |
| UI/API regression | Hourly | Disabled |
| FNX AI and parser validation | Every 2 hours | Disabled |

The earlier alerting logic collected failure screenshots and used email notifications with cooldowns. These features are no longer running. The source is kept for reference; do not re-enable these workflows or execute the tests against the former employer's systems without their authorization.

## Archived dashboard

The dashboard now shows the last recorded pass or failure and its timestamp. It no longer refreshes on a timer. The timeline opens at the final saved run, and visitors can inspect historical charts, execution records and available screenshots.

<table align="center">
  <tr>
    <td align="center"><img width="1910" height="977" alt="Historical Peoples Clinic monitoring dashboard, April 2026" src="https://github.com/user-attachments/assets/bf7be5da-973e-4cb6-9265-e43e71f61c60" /></td>
    <td align="center"><img width="1905" height="973" alt="Historical stability matrix, April 2026" src="https://github.com/user-attachments/assets/6dace373-8021-410f-a5eb-4418d58cb681" /></td>
    <td align="center"><img width="1907" height="972" alt="Historical dashboard alternative view, April 2026" src="https://github.com/user-attachments/assets/6ac3b839-8708-4a2b-b75a-07359876b17f" /></td>
  </tr>
</table>

These images are from the original active setup. The published dashboard is now explicitly labelled as archived.

## Current independent monitoring project

I applied what I learned from this work to my own R/Shiny currency application, Exchange Universe, and built a separate monitor for it. That project remains active and collects its own test evidence.

[Exchange Universe Monitor dashboard](https://rammeshgar.github.io/exchange-universe-monitor/) · [Source code](https://github.com/Rammeshgar/exchange-universe-monitor) · [Case study](https://rammeshgar.github.io/exchange-universe-monitor-case/)
