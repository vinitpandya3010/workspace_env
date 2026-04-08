from typing import Dict
from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from models import WorkspaceAction, WorkspaceObservation, WorkspaceState

class WorkspaceEnv(EnvClient[WorkspaceAction, WorkspaceObservation, WorkspaceState]):
    def _step_payload(self, action: WorkspaceAction) -> Dict:
        return {"cmd": action.cmd, "params": action.params}

    def _parse_result(self, payload: Dict) -> StepResult[WorkspaceObservation]:
        obs_data = payload.get("observation", {})
        # Reward/Done are usually at top level in server response
        reward = payload.get("reward", obs_data.get("reward", 0.1))
        done = payload.get("done", obs_data.get("done", False))
        
        observation = WorkspaceObservation(**obs_data)
        return StepResult(observation=observation, reward=float(reward), done=bool(done))

    def _parse_state(self, payload: Dict) -> WorkspaceState:
        return WorkspaceState(**payload)