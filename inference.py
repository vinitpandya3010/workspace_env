import os
import json
import re
import asyncio
from typing import List, Optional
from openai import OpenAI
from client import WorkspaceEnv
from models import WorkspaceAction

# Mandatory environment variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
# Task name can be passed via env var or default to 'easy'
TASK_NAME = os.getenv("TASK_ID", "easy") 
BENCHMARK = "workspace_env"

SYSTEM_PROMPT = """You are a Google Workspace AI Agent.
Your goal is to complete the 'EPISODE PROGRESS' checklist by executing the first [ ] item.

SOP (Standard Operating Procedure):
1. If 'Read the UNREAD email' is [ ], use READ_EMAIL with the BID (e.g., 'e1').
2. If 'Find Price in Sheets' or 'Find Project Code in Sheets' is [ ]:
   - Use NAV with params {"app": "sheets"}.
3. If 'Add Sender to Contacts' is [ ]:
   - Use NAV to 'contacts' if not there, then use ADD_CONTACT with the sender's info.
4. If 'Check Calendar for Conflicts' is [ ]:
   - Use NAV to 'calendar'.
5. If the last [ ] is REPLY:
   - Use REPLY with the answer found in the CLIPBOARD.
6. If the last [ ] is CREATE_EVENT:
   - Use CREATE_EVENT with the time requested and the info from the CLIPBOARD.

Rules:
- Output ONLY valid JSON.
- Never use the Subject as an ID; always use the BID (e.g., e1, e2).
- 2 PM = 14:00. 9 AM = 09:00.

COMMANDS:
{"cmd": "NAV", "params": {"app": "inbox" | "calendar" | "contacts" | "sheets"}}
{"cmd": "READ_EMAIL", "params": {"id": "bid"}}
{"cmd": "ADD_CONTACT", "params": {"name": "Name", "email": "email"}}
{"cmd": "CREATE_EVENT", "params": {"title": "title", "start": "HH:MM"}}
{"cmd": "REPLY", "params": {"body": "text"}}
"""

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

async def main():
    if not HF_TOKEN:
        print("Error: Please set HF_TOKEN environment variable.")
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    
    # Using your existing WorkspaceEnv
    # Note: If your client is sync, we use it directly. 
    # If using the openenv-core client, .sync() context manager is standard.
    env_instance = WorkspaceEnv(base_url="http://localhost:8000")
    
    rewards = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        with env_instance.sync() as env:
            result = env.reset(task_id=TASK_NAME)
            obs = result.observation
            
            for step in range(1, 9): # Max 8 steps
                steps_taken = step
                
                # Call LLM
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Status: {obs.last_action_status}\n\n{obs.view_data}"}
                    ],
                    max_tokens=150,
                    temperature=0.1
                )

                llm_text = response.choices[0].message.content.strip()
                match = re.search(r'\{.*\}', llm_text, re.DOTALL)
                
                if match:
                    try:
                        action_dict = json.loads(match.group(0))
                        action = WorkspaceAction(cmd=action_dict['cmd'], params=action_dict['params'])
                        
                        # Execute step
                        result = env.step(action)
                        obs = result.observation
                        
                        reward = result.reward
                        done = result.done
                        error = obs.error_message
                        
                        rewards.append(reward)
                        log_step(step, f"{action.cmd}", reward, done, error)
                        
                        if done:
                            # In your env, final reward 1.0 signifies success
                            score = reward if reward > score else score
                            break
                    except Exception as e:
                        log_step(step, "parse_error", 0.0, True, str(e))
                        break
                else:
                    log_step(step, "no_json", 0.0, True, "No JSON found")
                    break

            success = score >= 0.9 # 1.0 is full success
            # Ensure score is normalized [0, 1]
            score = min(max(score, 0.0), 1.0)

    except Exception as exc:
        print(f"[DEBUG] Runtime error: {exc}")
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())