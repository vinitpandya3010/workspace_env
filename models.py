from typing import List, Optional, Dict, Any
from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field

class WorkspaceAction(Action):
    """Action for the Workspace environment."""
    cmd: str = Field(..., description="Action: NAV, READ_EMAIL, ADD_CONTACT, CREATE_EVENT, REPLY")
    params: Dict[str, Any] = Field(default_factory=dict)

class WorkspaceObservation(Observation):
    """What the agent sees on its screen."""
    current_app: str = Field(default="inbox")
    view_data: str = Field(default="")
    last_action_status: str = Field(default="success")
    error_message: Optional[str] = None
    reward: float = Field(default=0.1) # Added this
    done: bool = Field(default=False)   # Added this

class WorkspaceState(State):
    """The full internal state for grading."""
    inbox: List[Dict[str, Any]] = []
    calendar: List[Dict[str, Any]] = []
    contacts: List[Dict[str, Any]] = []
    sheets: Dict[str, List[List[str]]] = {}
    task_id: str = "easy"
    step_count: int = 0
    episode_id: str = ""