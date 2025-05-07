import os
import time
import logging
from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=".env.local")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class EgressSession:
    """
    Manages LiveKit egress operations: start, list, stop.

    Instantiates a single LiveKitAPI client and keeps it open until close().
    """
    def __init__(self):
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")
        livekit_url = os.getenv("LIVEKIT_URL")
        if not all([api_key, api_secret, livekit_url]):
            raise ValueError("Missing LiveKit environment variables: API_KEY, API_SECRET, or URL")
        self.lkapi = api.LiveKitAPI(api_key=api_key, api_secret=api_secret, url=livekit_url)
        self.active_egresses = {}

    async def start_room_composite(self, room_name: str, user_id:str, audio_only:bool=False) -> dict:
        """
        Start a composite egress for the given room and return metadata.
        """
        timestamp = int(time.time())
        filename = f"recording_{room_name}_{timestamp}"
        if(audio_only):
            request = api.RoomCompositeEgressRequest(
                room_name=room_name,
                audio_only=True,
                file_outputs=[
                    api.EncodedFileOutput(
                    file_type=api.EncodedFileType.OGG,
                    filepath=f"sessions/{user_id}" + "/" + filename,
                    s3=api.S3Upload(
                        bucket=os.getenv("AWS_BUCKET_NAME"),
                        region=os.getenv("AWS_REGION"),
                        access_key=os.getenv("AWS_ACCESS_KEY_ID"),
                        secret=os.getenv("AWS_SECRET_ACCESS_KEY"),
                        force_path_style=True,
                    ),
                )
                ],
                preset=api.EncodingOptionsPreset.H264_720P_30,
            )
        else:
            request = api.RoomCompositeEgressRequest(
                room_name=room_name,
                audio_only=False,
                file_outputs=[
                    api.EncodedFileOutput(
                    file_type=api.EncodedFileType.MP4,
                    filepath=f"sessions/{user_id}" + "/" + filename,
                    s3=api.S3Upload(
                        bucket=os.getenv("AWS_BUCKET_NAME"),
                        region=os.getenv("AWS_REGION"),
                        access_key=os.getenv("AWS_ACCESS_KEY_ID"),
                        secret=os.getenv("AWS_SECRET_ACCESS_KEY"),
                        force_path_style=True,
                    ),
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
            "user_id": user_id,
            "started_at": timestamp
        }
        print(f"Composite egress started: {egress_id}")
        self.active_egresses[egress_id] = metadata
        return metadata

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
        self.active_egresses.pop(egress_id, None)
        return result

    async def close(self):
        """
        Close the underlying LiveKit API client to avoid unclosed sessions.
        """
        if self.lkapi:
            await self.lkapi.aclose()
            self.lkapi = None
