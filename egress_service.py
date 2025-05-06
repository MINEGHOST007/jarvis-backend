import os
import time
import logging
from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv(dotenv_path=".env.local")

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class EgressSession:
    """
    Manages LiveKit egress operations: start, list, stop.

    Instantiates a single LiveKitAPI client and keeps it open until close().
    """
    def __init__(self):
        # Load LiveKit credentials from environment
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")
        livekit_url = os.getenv("LIVEKIT_URL")
        if not all([api_key, api_secret, livekit_url]):
            raise ValueError("Missing LiveKit environment variables: API_KEY, API_SECRET, or URL")

        # Initialize the LiveKit API client once
        self.lkapi = api.LiveKitAPI(api_key=api_key, api_secret=api_secret, url=livekit_url)
        self.active_egresses = {}

    async def start_room_composite(self, room_name: str) -> dict:
        """
        Start a composite egress for the given room and return metadata.
        """
        timestamp = int(time.time())
        filename = f"recording_{room_name}_{timestamp}.mp4"
        output_path = os.path.join(os.getenv("EGRESS_OUTPUT_DIR", "/app/recordings"), filename)

        request = api.RoomCompositeEgressRequest(
            room_name=room_name,
            file_outputs=[
                api.EncodedFileOutput(
                    filepath=output_path,
                    file_type=api.EncodedFileType.MP4
                )
            ],
            preset=api.EncodingOptionsPreset.H264_720P_30,
        )
        logger.debug("Starting composite egress: %s", request)
        response = await self.lkapi.egress.start_room_composite_egress(request)
        egress_id = response.egress_id
        logger.info("Composite egress started: %s", egress_id)

        metadata = {
            "egress_id": egress_id,
            "room_name": room_name,
            "output_path": output_path,
            "started_at": timestamp
        }
        self.active_egresses[egress_id] = metadata
        return metadata

    async def list_egresses(self) -> list:
        """
        List all active and past egresses.
        """
        logger.debug("Listing all egresses...")
        response = await self.lkapi.egress.list_egress()
        egresses = []
        for e in response.items:
            entry = {
                "egress_id": e.egress_id,
                "room_name": getattr(e, 'room_name', None),
                "status": e.status,
                "started_at": e.started_at,
                "ended_at": e.ended_at,
                "output": [o.to_dict() for o in getattr(e, 'output', [])]
            }
            egresses.append(entry)
        return egresses

    async def stop_egress(self, egress_id: str) -> dict:
        """
        Stop a running egress by its ID.
        """
        logger.debug("Stopping egress: %s", egress_id)
        request = api.StopEgressRequest(egress_id=egress_id)
        response = await self.lkapi.egress.stop_egress(request)
        logger.info("Egress stopped: %s", egress_id)

        result = {
            "egress_id": response.egress_id,
            "room_name": getattr(response, 'room_name', None),
            "status": response.status,
            "stopped_at": int(time.time())
        }
        # Clean up local state
        self.active_egresses.pop(egress_id, None)
        return result

    async def close(self):
        """
        Close the underlying LiveKit API client to avoid unclosed sessions.
        """
        if self.lkapi:
            await self.lkapi.aclose()
            self.lkapi = None
