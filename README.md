---
title: Workspace AI Agent Environment
emoji: 🏢
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 8000
tags:
  - openenv
---

# Workspace Env: Real-World Business Task Simulation

Workspace Env is a standardized environment built for the **Meta OpenEnv Hackathon**. It simulates a modern "Google Workspace" style office environment, forcing AI agents to manage emails, contacts, spreadsheets, and calendars to solve complex business workflows.

## 🚀 Environment Overview
Unlike toy problems (games/puzzles), Workspace Env focuses on **Functional Utility**. Agents must interact with multiple simulated "apps" and maintain state across steps to succeed.

### Key Features:
- **Typed Models:** Full compliance with `openenv` using Pydantic for Actions and Observations.
- **Dynamic Observation:** A text-based UI representation including an **Episode Progress Checklist** and a **Clipboard** for data persistence.
- **Programmatic Grading:** Deterministic scoring (0.0 to 1.0) for every task.
- **Dense Rewards:** Incremental feedback for navigation and sub-goal completion to prevent sparse-reward stagnation.

---

## 🛠 Action & Observation Space

### Action Space (JSON)
Agents interact via the following command schema:
| Command | Parameters | Description |
| :--- | :--- | :--- |
| `NAV` | `{"app": "inbox" \| "calendar"..."}` | Switch between workspace applications. |
| `READ_EMAIL` | `{"id": "bid"}` | View content of a specific email in the Inbox. |
| `ADD_CONTACT` | `{"name": "...", "email": "..."}` | Save a new contact to the address book. |
| `CREATE_EVENT` | `{"title": "...", "start": "HH:MM"}` | Schedule a meeting on the calendar. |
| `REPLY` | `{"body": "..."}` | Send an email response (Ends task in Easy mode). |

### Observation Space
The environment returns a `view_data` string containing:
1. **System Time:** Current simulated time (e.g., Monday, 09:00 AM).
2. **Clipboard:** Persistent storage for extracted data (e.g., Project Codes).
3. **Episode Progress:** A real-time checklist of completed/remaining sub-tasks.
4. **App View:** The current UI content (List of emails, Spreadsheet rows, etc.).

---

## 📋 Task Suite & Difficulty

| Task | ID | Difficulty | Objective |
| :--- | :--- | :--- | :--- |
| **Email Triage** | `easy` | Easy | Read a policy email, find the price in Sheets, and reply with the value. |
| **Smart Scheduler** | `medium` | Medium | Read a meeting request, check the calendar for conflicts, and schedule at the first free slot. |
| **Project Onboarding** | `hard` | Hard | Extract a project code from Sheets, add the sender to Contacts, and schedule a project kickoff. |

---

## 📈 Reward Function & Grading
- **Incremental Reward:** `+0.01` for navigation, `+0.05` for reading emails, `+0.1` for intermediate steps (adding contacts).
- **Penalty:** `-0.2` for destructive actions (e.g., scheduling a meeting over an existing event).
- **Final Score:** A programmatic grader evaluates the final state and assigns a score in the range `[0.0, 1.0]`.

---

## 💻 Usage Instructions

### Local Development
1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   uv lock