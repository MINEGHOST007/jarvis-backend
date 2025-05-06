import logging
from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    llm,
    metrics,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import (
    cartesia,
    google,
    deepgram,
    noise_cancellation,
    silero,
    turn_detector,
)

from livekit.agents.cli.cli import run_worker
from livekit.agents.cli.proto import CliArgs

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")

class AgentSession:
    def __init__(self, session_id,log_level="INFO"):
        self.session_id = session_id
        self.runner = None
        self.log_level = log_level

    def prewarm(self, proc: JobProcess):
        proc.userdata["vad"] = silero.VAD.load()

    async def entrypoint(self, ctx: JobContext):
        initial_ctx = llm.ChatContext().append(
            role="system",
            text=(
                "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
                "You should use short and concise responses, and avoiding usage of unpronouncable punctuation. "
                "You were created as a demo to showcase the capabilities of LiveKit's agents framework."
            ),
        )
        logger.info(f"connecting to room {ctx.room.name}")
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        participant = await ctx.wait_for_participant()
        logger.info(f"starting voice assistant for participant {participant.identity}")
        agent = VoicePipelineAgent(
            vad=ctx.proc.userdata["vad"],
            stt=deepgram.STT(),
            llm=google.LLM(model="gemini-2.0-flash"),
            tts=cartesia.TTS(),
            turn_detector=turn_detector.EOUModel(),
            min_endpointing_delay=0.5,
            max_endpointing_delay=5.0,
            noise_cancellation=noise_cancellation.BVC(),
            chat_ctx=initial_ctx,
        )
        usage_collector = metrics.UsageCollector()
        @agent.on("metrics_collected")
        def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
            metrics.log_metrics(agent_metrics)
            usage_collector.collect(agent_metrics)
        agent.start(ctx.room, participant)
        await agent.say("Hey, how can I help you today?", allow_interruptions=True)

    def connect(self):
        if self.runner is None:
            opts = WorkerOptions(
                entrypoint_fnc=self.entrypoint,
                prewarm_fnc=self.prewarm,
            )
            args = CliArgs(
                opts=opts,
                log_level=self.log_level,
                devmode=False,
                asyncio_debug=False,
                watch=False,
                drain_timeout=60,
            )
            run_worker(args)
        return self.runner

    def disconnect(self):
        if self.runner is not None:
            self.runner.stop()
            self.runner = None

# Global session manager
global_agent_sessions = {}

def get_agent_session(session_id):
    if session_id not in global_agent_sessions:
        global_agent_sessions[session_id] = AgentSession(session_id)
    return global_agent_sessions[session_id]

if __name__ == "__main__":
    session = get_agent_session("default")
    session.connect()
