from openenv.core.env_server import create_fastapi_app
from .workspace_env_environment import WorkspaceEnvironment
from models import WorkspaceAction, WorkspaceObservation

# Pass the CLASS, not an instance, to support concurrent sessions
app = create_fastapi_app(
    WorkspaceEnvironment, 
    WorkspaceAction, 
    WorkspaceObservation,
    max_concurrent_envs=10
)

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

    