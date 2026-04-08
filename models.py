from typing import List, Optional, Dict, Any
from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field

class WorkspaceAction(Action):
    """Action for the Workspace environment."""
    cmd: str = Field(..., description="Action: NAV, READ_EMAIL, SEND_EMAIL, SEARCH_CONTACTS, CREATE_EVENT, READ_SHEET")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters like {'id': 'e1'} or {'to': 'user@example.com'}")

class WorkspaceObservation(Observation):
    """What the agent sees on its screen."""
    current_app: str = Field(default="inbox")
    view_data: str = Field(default="", description="Text representation of the current screen")
    last_action_status: str = Field(default="")
    error_message: Optional[str] = None

class WorkspaceState(State):
    """The full internal state for grading."""
    inbox: List[Dict[str, Any]] = []
    calendar: List[Dict[str, Any]] = []
    contacts: List[Dict[str, Any]] = []
    sheets: Dict[str, List[List[str]]] = {}
    task_id: str = "easy"