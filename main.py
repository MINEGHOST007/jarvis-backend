from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional
import os
import subprocess
import logging
from egress_service import EgressSession
from aws_service import get_all_files, get_file_url

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
app = FastAPI(
    title="Jarvis Backend API",
    description="""
    ## Overview
    This API provides endpoints to manage LiveKit voice agent sessions, egress (recording) operations, and file access for recorded sessions. It is designed to be used with a compatible frontend or client application.

    ### Main Features
    - Start and stop egress (recording) for a LiveKit room
    - List all recordings for a user
    - Generate secure download URLs for recorded files
    - Health check endpoint
    """,
    version="1.0.0",
)

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

@app.get("/", summary="API Health Check", tags=["Utility"])
async def read_root():
    """
    Health check endpoint to verify the API is running.
    """
    return {"message": "Welcome to the Jarvis Backend API"}

@app.post("/egress/start", summary="Start Room Recording (Egress)", tags=["Egress"])
async def start_egress(user_id: str = Query(..., description="Unique user/session identifier for the recording."), room_name: str = Query(..., description="Name of the LiveKit room to record."), audio_only: Optional[bool] = Query(False, description="Whether to record audio only (default is False).")):
    """
    Start a composite egress (recording) for a given LiveKit room.

    - **user_id**: Unique identifier for the user/session.
    - **room_name**: Name of the LiveKit room to record.
    
    Returns metadata about the started egress session.
    """
    if not egress_manager:
        raise HTTPException(status_code=500, detail="Egress manager not initialized")
    try:
        info = await egress_manager.start_room_composite(room_name, user_id, audio_only)
        return {"message": f"Egress started for session {user_id}", "info": info}
    except Exception as e:
        logger.error(f"Failed to start egress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/egress/stop", summary="Stop Room Recording (Egress)", tags=["Egress"])
async def stop_egress(egress_id: str = Query(..., description="ID of the egress session to stop.")):
    """
    Stop an active egress (recording) session by its egress ID.

    - **egress_id**: The unique identifier of the egress session to stop.
    
    Returns information about the stopped egress.
    """
    if not egress_manager:
        raise HTTPException(status_code=500, detail="Egress manager not initialized")
    try:
        result = await egress_manager.stop_egress(egress_id)
        return {"message": f"Egress {egress_id} stopped", "info": result}
    except Exception as e:
        logger.error(f"Failed to stop egress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list", summary="List Recordings for User", tags=["Files"])
def get_list_recordings(user_id: str = Query(..., description="User/session identifier to list recordings for.")):
    """
    List all available recordings for a given user/session.

    - **user_id**: The user/session identifier whose recordings should be listed.
    
    Returns a list of recording file metadata.
    """
    try:
        recordings = get_all_files(user_id)
        return {"recordings": recordings}
    except Exception as e:
        logger.error(f"Failed to list recordings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_file_url", summary="Get Download URL for Recording", tags=["Files"])
async def download_file(file_key: str = Query(..., description="Key or path of the file to download."), expiration: Optional[int] = Query(None, description="Expiration time (seconds) for the download URL. Default is provider-specific.")):
    """
    Generate a secure, time-limited download URL for a given recording file.

    - **file_key**: The key or path of the file to generate a download URL for.
    - **expiration**: Optional expiration time (in seconds) for the URL.
    
    Returns a signed URL for downloading the file.
    """
    try:
        url = get_file_url(file_key, expiration)
        return {"url": url}
    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))