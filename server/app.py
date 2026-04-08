from openenv.core.env_server import create_fastapi_app
from .workspace_env_environment import WorkspaceEnvironment
from models import WorkspaceAction, WorkspaceObservation
from fastapi.responses import HTMLResponse # Add this import

# Create the base app
app = create_fastapi_app(
    WorkspaceEnvironment, 
    WorkspaceAction, 
    WorkspaceObservation,
    max_concurrent_envs=10
)

# --- ADD THIS PART TO FIX THE 404 ---
@app.get("/", response_class=HTMLResponse)
@app.get("/web", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
            <h1>🏢 Workspace AI Agent Env</h1>
            <p>Status: 🟢 Running</p>
            <p>This is an OpenEnv API server. There is no human UI here.</p>
            <a href="/docs" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">View API Documentation</a>
            <br><br>
            <p>Created for the Meta OpenEnv Hackathon</p>
        </body>
    </html>
    """
# ------------------------------------

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()