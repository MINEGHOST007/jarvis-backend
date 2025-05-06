from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional
import os
import subprocess
import logging
from egress_service import EgressSession

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)

def run_agent():
    try:
        subprocess.Popen(["python3", "agent.py", "dev"], cwd=BASE_DIR)
        logger.info("Agent subprocess started")
    except Exception as e:
        logger.error(f"Error starting agent: {e}")

run_agent()

egress_manager: Optional[EgressSession] = None

# FastAPI startup/shutdown events
def startup_event():
    global egress_manager
    egress_manager = EgressSession()
    logger.info("EgressSession initialized")

async def shutdown_event():
    if egress_manager:
        await egress_manager.close()
        logger.info("EgressSession closed")

app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

# Root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Jarvis Backend API"}

# Start egress for a room
@app.post("/egress/start")
async def start_egress(session_id: str = Query(...), room_name: str = Query(...)):
    if not egress_manager:
        raise HTTPException(status_code=500, detail="Egress manager not initialized")
    try:
        info = await egress_manager.start_room_composite(room_name)
        # Tag with your session ID
        info["session_id"] = session_id
        return {"message": f"Egress started for session {session_id}", "info": info}
    except Exception as e:
        logger.error(f"Failed to start egress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Stop egress by egress_id
@app.post("/egress/stop")
async def stop_egress(egress_id: str = Query(...)):
    if not egress_manager:
        raise HTTPException(status_code=500, detail="Egress manager not initialized")
    try:
        result = await egress_manager.stop_egress(egress_id)
        return {"message": f"Egress {egress_id} stopped", "info": result}
    except Exception as e:
        logger.error(f"Failed to stop egress: {e}")
        raise HTTPException(status_code=500, detail=str(e))
