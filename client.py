from typing import Dict
from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from models import WorkspaceAction, WorkspaceObservation, WorkspaceState

class WorkspaceEnv(EnvClient[WorkspaceAction, WorkspaceObservation, WorkspaceState]):
    def _step_payload(self, action: WorkspaceAction) -> Dict:
        return {
            "cmd": action.cmd,
            "params": action.params,
        }

    def _parse_result(self, payload: Dict) -> StepResult[WorkspaceObservation]:
        obs_data = payload.get("observation", {})
        # Use .get() with defaults to avoid KeyErrors
        reward = payload.get("reward")
        done = payload.get("done", False)
        
        observation = WorkspaceObservation(
            current_app=obs_data.get("current_app", "inbox"),
            view_data=obs_data.get("view_data", ""),
            last_action_status=obs_data.get("last_action_status", ""),
            error_message=obs_data.get("error_message"),
            done=done if done is not None else False,
            reward=float(reward) if reward is not None else 0.0,
        )
        return StepResult(observation=observation, reward=observation.reward, done=observation.done)

    def _parse_state(self, payload: Dict) -> WorkspaceState:
        return WorkspaceState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            inbox=payload.get("inbox", []),
            calendar=payload.get("calendar", []),
            contacts=payload.get("contacts", []),
            sheets=payload.get("sheets", {}),
            task_id=payload.get("task_id", "easy")
        )