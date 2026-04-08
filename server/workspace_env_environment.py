import uuid
from typing import Optional, Tuple, Dict, Any
from openenv.core.env_server import Environment
from models import WorkspaceAction, WorkspaceObservation, WorkspaceState
# Relative import from the same directory (server/)
from .graders import grade_easy, grade_medium, grade_hard

class WorkspaceEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True
    TASKS = ["easy", "medium", "hard"]

    @property
    def __init__(self):
        self._db = WorkspaceState()
        self._current_app = "inbox"
        self._last_status = "Ready"
        self._selected_id = None 
        self._found_code = False

    @property
    def metadata(self) -> Dict[str, Any]:
        """Discovery metadata for the validator."""
        return {
            "tasks": [
                {"id": "easy", "description": "Reply to email"},
                {"id": "medium", "description": "Schedule meeting"},
                {"id": "hard", "description": "Onboard project"}
            ]
        }

    def reset(self, task_id: str = "easy", **kwargs) -> WorkspaceObservation:
        # Crucial: Normalize task_id
        if task_id not in self.TASKS:
            task_id = "easy"
            
        self._db = WorkspaceState(
            task_id=task_id, 
            step_count=0, 
            episode_id=str(uuid.uuid4())
        )
        self._current_app = "inbox"
        self._selected_id = None
        self._found_code = False
        self._last_status = f"Task {task_id} started"
        
        # Initialize different data per task
        if task_id == "easy":
            self._db.inbox = [{"id": "e1", "from": "hr@co.com", "subject": "Policy", "body": "Remote price in Rules sheet", "read": False}]
            self._db.sheets = {"Rules": [["Remote", "$50"]]}
        elif task_id == "medium":
            self._db.inbox = [{"id": "e2", "from": "dev@co.com", "subject": "Sync", "body": "Meet at 2pm?", "read": False}]
            self._db.calendar = [{"id": "c1", "title": "Lunch", "start": "12:00"}]
        elif task_id == "hard":
            self._db.inbox = [{"id": "e3", "from": "client@pt.com", "subject": "Project", "body": "Add contact, code in Active_Projects, set 9am", "read": False}]
            self._db.sheets = {"Active_Projects": [["Name", "Code"], ["X", "PX-99"]]}
            self._db.contacts = [{"name": "Admin", "email": "admin@co.com"}]

        obs = self._generate_obs()
        obs.reward = 0.05  # STDOUT strictly > 0
        return obs

    def step(self, action: WorkspaceAction, **kwargs) -> WorkspaceObservation:
        self._db.step_count += 1
        reward = 0.01 # Base reward
        done = False
        
        cmd = action.cmd.upper()
        p = action.params

        try:
            if cmd == "NAV":
                target = (p.get("app") or "inbox").lower()
                if target in ["inbox", "calendar", "contacts", "sheets"]:
                    self._current_app = target
                    reward = 0.02
                    if target == "sheets": self._found_code = True
            
            elif cmd == "READ_EMAIL":
                email_id = p.get("id") or p.get("email_id")
                email = next((e for e in self._db.inbox if e["id"] == email_id), None)
                if email:
                    email["read"] = True
                    self._selected_id = email["id"]
                    reward = 0.06

            elif cmd == "ADD_CONTACT":
                if p.get("name") and p.get("email"):
                    self._db.contacts.append({"name": p["name"], "email": p["email"]})
                    reward = 0.15

            elif cmd == "CREATE_EVENT":
                start = p.get("start") or p.get("time")
                if start:
                    self._db.calendar.append({"title": p.get("title", "Meeting"), "start": start})
                    if self._db.task_id in ["medium", "hard"]: done = True

            elif cmd == "REPLY":
                if self._selected_id and self._db.task_id == "easy": done = True

            if self._db.step_count >= 15: done = True

            if done:
                if self._db.task_id == "easy": reward = grade_easy(self._db)
                elif self._db.task_id == "medium": reward = grade_medium(self._db)
                else: reward = grade_hard(self._db)

        except Exception:
            reward = 0.01
            done = True

        # Mandatory: Strictly 0 < reward < 1
        reward = max(0.01, min(0.99, reward))
        
        obs = self._generate_obs()
        obs.reward = float(reward)
        obs.done = bool(done)
        return obs

    def _generate_obs(self, error=None) -> WorkspaceObservation:
        view = "================================================\n"
        view += "SYSTEM TIME: Monday, 09:00 AM\n"
        if self._found_code:
            if self._db.task_id == "easy":
                view += "CLIPBOARD: Remote Policy Price = $50\n"
            else:
                view += "CLIPBOARD: Project Code = PX-99\n"

        if self._selected_id:
            e = next(e for e in self._db.inbox if e["id"] == self._selected_id)
            view += f"ACTIVE GOAL: {e['body']}\n"
            view += f"SENDER INFO: {e['from']}\n"
        else:
            view += "GOAL: You have 1 UNREAD email. Use READ_EMAIL to begin.\n"

        view += "\nEPISODE PROGRESS:\n"
        email_opened = self._selected_id is not None
        view += f"- [ {'X' if email_opened else ' '} ] 1. Read the UNREAD email\n"

        if self._db.task_id == "easy":
            view += f"- [ {'X' if self._found_code else ' '} ] 2. Find Price in Sheets\n"
            view += f"- [   ] 3. REPLY to the email with the price\n"
        elif self._db.task_id == "medium":
            view += f"- [ {'X' if self._current_app == 'calendar' else ' '} ] 2. Check Calendar for Conflicts\n"
            view += f"- [   ] 3. CREATE_EVENT at the requested time\n"
        elif self._db.task_id == "hard":
            contact_done = any("client@partner.com" in c["email"].lower() for c in self._db.contacts)
            view += f"- [ {'X' if contact_done else ' '} ] 2. Add Sender to Contacts\n"
            view += f"- [ {'X' if self._found_code else ' '} ] 3. Find Project Code in Sheets\n"
            view += f"- [   ] 4. CREATE_EVENT at 09:00 with Project Code\n"

        view += "================================================\n\n"
        view += f"CURRENT APP: {self._current_app.upper()}\n"
        
        if self._current_app == "inbox":
            if self._selected_id:
                e = next(e for e in self._db.inbox if e["id"] == self._selected_id)
                view += f"--- EMAIL VIEW ---\nFROM: {e['from']}\nSUBJECT: {e['subject']}\nBODY: {e['body']}\n"
            else:
                view += "--- INBOX LIST ---\n"
                view += "\n".join([f"[BID: {e['id']}] From: {e['from']} | Sub: {e['subject']} {'(READ)' if e['read'] else '(UNREAD)'}" for e in self._db.inbox])
        elif self._current_app == "sheets":
            view += "--- SPREADSHEET DATA ---\n"
            for name, rows in self._db.sheets.items():
                view += f"Sheet: '{name}'\nContent: {rows}\n"
            view += "\n[SYSTEM: Information captured to CLIPBOARD.]"
        elif self._current_app == "calendar":
            view += "--- CALENDAR ---\n"
            events = [f"{e['start']}: {e['title']}" for e in self._db.calendar]
            view += "\n".join(events) if events else "(No events)"
        elif self._current_app == "contacts":
            view += "--- CONTACTS ---\n"
            contacts = [f"{c['name']} | {c['email']}" for c in self._db.contacts]
            view += "\n".join(contacts) if contacts else "(Empty)"

        if error: view += f"\n\n!!! ERROR: {error}"
        return WorkspaceObservation(current_app=self._current_app, view_data=view, last_action_status=self._last_status, error_message=error)

    @property
    def state(self) -> WorkspaceState:
        return self._db