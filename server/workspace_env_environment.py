import uuid
from typing import Optional, Tuple, Dict, Any, List
from openenv.core.env_server import Environment
# Import from the root models file
from models import WorkspaceAction, WorkspaceObservation, WorkspaceState
# Import from the same directory
from graders import grade_easy, grade_medium, grade_hard

class WorkspaceEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True
    TASKS = ["easy", "medium", "hard"]

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "tasks": [
                {"id": "easy", "description": "Read email and reply with price"},
                {"id": "medium", "description": "Schedule meeting avoiding conflicts"},
                {"id": "hard", "description": "Cross-app project onboarding"}
            ]
        }

    def __init__(self):
        self._db = WorkspaceState()
        self._current_app = "inbox"
        self._last_status = "System Ready"
        self._selected_id = None 
        self._found_code = False

    def reset(self, task_id: str = "easy", **kwargs) -> WorkspaceObservation:
        if task_id not in self.TASKS:
            task_id = "easy"
        self._db = WorkspaceState(task_id=task_id, step_count=0, episode_id=str(uuid.uuid4()))
        self._current_app = "inbox"
        self._selected_id = None
        self._found_code = False
        self._last_status = "Task Started"
        
        if task_id == "easy":
            self._db.inbox = [{"id": "e1", "from": "hr@co.com", "subject": "Policy", "body": "Remote price in Rules sheet", "read": False}]
            self._db.sheets = {"Rules": [["Remote", "$50"]]}
        elif task_id == "medium":
            self._db.inbox = [{"id": "e2", "from": "dev@co.com", "subject": "Sync", "body": "Meet today at 2pm?", "read": False}]
            self._db.calendar = [{"id": "c1", "title": "Lunch", "start": "12:00"}]
        elif task_id == "hard":
            self._db.inbox = [{"id": "e3", "from": "client@pt.com", "subject": "Project", "body": "Add contact, find code in Active_Projects, set 9am", "read": False}]
            self._db.sheets = {"Active_Projects": [["Name", "Code"], ["X", "PX-99"]]}
            self._db.contacts = [{"name": "Admin", "email": "admin@co.com"}]

        obs = self._generate_obs()
        obs.reward = 0.05
        obs.done = False
        return obs

    def step(self, action: WorkspaceAction, **kwargs) -> WorkspaceObservation:
        self._db.step_count += 1
        reward = 0.01
        done = False
        error = None
        
        cmd = action.cmd.upper()
        p = action.params

        try:
            if cmd == "NAV":
                target_app = (p.get("app") or "inbox").lower()
                if target_app in ["inbox", "calendar", "contacts", "sheets"]:
                    self._current_app = target_app
                    reward = 0.02
                    if target_app == "sheets": self._found_code = True
                else:
                    error = f"App '{target_app}' not found."
            
            elif cmd == "READ_EMAIL":
                email_id = p.get("id") or p.get("email_id")
                email = next((e for e in self._db.inbox if e["id"] == email_id), None)
                if email:
                    email["read"] = True
                    self._selected_id = email["id"]
                    reward = 0.06
                else:
                    reward = 0.01

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
                if self._selected_id and self._db.task_id == "easy":
                    done = True

            if self._db.step_count >= 15: done = True

            if done:
                if self._db.task_id == "easy":
                    reward = grade_easy(self._db)
                elif self._db.task_id == "medium":
                    reward = grade_medium(self._db)
                else:
                    reward = grade_hard(self._db)

        except Exception as e:
            error = str(e)
            reward = 0.01
            done = True

        reward = max(0.01, min(0.99, reward))
        obs = self._generate_obs(error)
        obs.reward = float(reward)
        obs.done = bool(done)
        return obs

    def _generate_obs(self, error=None) -> WorkspaceObservation:
        view = f"SYSTEM TIME: 09:00 AM\n"
        if self._found_code:
            view += f"CLIPBOARD: {'$50' if self._db.task_id == 'easy' else 'PX-99'}\n"
        view += f"CURRENT APP: {self._current_app.upper()}\n"
        if error: view += f"ERROR: {error}\n"
        return WorkspaceObservation(current_app=self._current_app, view_data=view)
    
    @property
    def state(self) -> WorkspaceState:
        return self._db