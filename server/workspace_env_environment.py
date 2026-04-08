import uuid
from typing import Optional, Dict, Any, List
from openenv.core.env_server import Environment
from models import WorkspaceAction, WorkspaceObservation, WorkspaceState
from .graders import grade_easy, grade_medium, grade_hard

class WorkspaceEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True
    TASKS = ["easy", "medium", "hard"]

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "tasks": [
                {"id": "easy", "description": "Email reply task"},
                {"id": "medium", "description": "Calendar scheduling task"},
                {"id": "hard", "description": "Multi-app onboarding task"}
            ]
        }

    def __init__(self):
        self._db = WorkspaceState()
        self._current_app = "inbox"
        self._selected_id = None 
        self._found_code = False
        self._last_reward = 0.1
        self._last_done = False

    @property
    def reward(self) -> float:
        return self._last_reward

    @property
    def done(self) -> bool:
        return self._last_done

    def reset(self, task_id: str = "easy", **kwargs) -> WorkspaceObservation:
        if task_id not in self.TASKS:
            task_id = "easy"
        self._db = WorkspaceState(task_id=task_id, step_count=0, episode_id=str(uuid.uuid4()))
        self._current_app = "inbox"
        self._selected_id = None
        self._found_code = False
        self._last_done = False
        self._last_reward = 0.1
        
        if task_id == "easy":
            self._db.inbox = [{"id": "e1", "from": "hr@co.com", "subject": "Policy", "body": "Remote price in Rules sheet", "read": False}]
            self._db.sheets = {"Rules": [["Remote", "$50"]]}
        elif task_id == "medium":
            self._db.inbox = [{"id": "e2", "from": "dev@co.com", "subject": "Sync", "body": "Meet at 2pm?", "read": False}]
            self._db.calendar = [{"id": "c1", "title": "Lunch", "start": "12:00"}]
        elif task_id == "hard":
            # NOTE: Domain fixed to @pt.com to match grader
            self._db.inbox = [{"id": "e3", "from": "client@pt.com", "subject": "Project", "body": "Add contact, find code in Active_Projects, set 9am", "read": False}]
            self._db.sheets = {"Active_Projects": [["Name", "Code"], ["X", "PX-99"]]}
            self._db.contacts = [{"name": "Admin", "email": "admin@co.com"}]

        return self._generate_obs(reward=0.1, done=False)

    def step(self, action: WorkspaceAction, **kwargs) -> WorkspaceObservation:
        self._db.step_count += 1
        reward = 0.1
        done = False
        status = "success"
        
        cmd = action.cmd.upper()
        p = action.params or {}

        try:
            if cmd == "NAV":
                target = (p.get("app") or "inbox").lower()
                self._current_app = target
                if target == "sheets": self._found_code = True
                reward = 0.15
            elif cmd == "READ_EMAIL":
                email_id = p.get("id") or p.get("email_id")
                email = next((e for e in self._db.inbox if e["id"] == email_id), None)
                if email:
                    email["read"] = True
                    self._selected_id = email["id"]
                    reward = 0.2
            elif cmd == "ADD_CONTACT":
                if p.get("name") and p.get("email"):
                    self._db.contacts.append({"name": p["name"], "email": p["email"]})
                    reward = 0.3
            elif cmd == "CREATE_EVENT":
                start = p.get("start") or p.get("time")
                if start:
                    self._db.calendar.append({"title": p.get("title", "Meeting"), "start": start})
                    if self._db.task_id in ["medium", "hard"]: done = True
            elif cmd == "REPLY":
                if self._selected_id and self._db.task_id == "easy": done = True

            if self._db.step_count >= 10: done = True

            if done:
                if self._db.task_id == "easy": reward = grade_easy(self._db)
                elif self._db.task_id == "medium": reward = grade_medium(self._db)
                else: reward = grade_hard(self._db)

        except Exception as e:
            status = f"error: {str(e)}"
            reward = 0.05
            done = True

        # STRICTOR RANGE: Ensures (0, 1)
        self._last_reward = max(0.01, min(0.99, float(reward)))
        self._last_done = done
        
        return self._generate_obs(reward=self._last_reward, done=done, status=status)

    def _generate_obs(self, reward: float, done: bool, status: str = "success") -> WorkspaceObservation:
        view = f"TIME: 09:00 AM | APP: {self._current_app.upper()}\n"
        if self._found_code:
            view += f"CLIPBOARD: {'$50' if self._db.task_id == 'easy' else 'PX-99'}\n"
        
        return WorkspaceObservation(
            current_app=self._current_app, 
            view_data=view,
            reward=reward, 
            done=done,
            last_action_status=status
        )
    
    @property
    def state(self) -> WorkspaceState:
        return self._db