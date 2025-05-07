<a href="https://livekit.io/">
  <img src="./.github/assets/livekit-mark.png" alt="LiveKit logo" width="100" height="100">
</a>

# Jarvis Backend API

<p>
  <a href="https://cloud.livekit.io/projects/p_/sandbox"><strong>Deploy a sandbox app</strong></a>
  •
  <a href="https://docs.livekit.io/agents/overview/">LiveKit Agents Docs</a>
  •
  <a href="https://livekit.io/cloud">LiveKit Cloud</a>
  •
  <a href="https://blog.livekit.io/">Blog</a>
</p>

A robust, Python-based voice agent backend that leverages LiveKit for real-time communication capabilities.

## Overview

The Jarvis Backend API provides a comprehensive solution for managing voice agent interactions, including room recordings, session management, and file access. Built with Python and integrated with LiveKit, this API offers a powerful foundation for developing voice-enabled applications.

## Features

- **Voice Agent Integration**: Seamlessly interact with the voice pipeline
- **Room Recording**: Start and stop recording sessions via the Egress API
- **File Management**: List and download recorded sessions
- **Health Monitoring**: Simple endpoint to verify system status

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Virtual environment (recommended)
- AWS account for storage functionality
- API keys for required services

### Installation

1. Clone the repository
2. Set up the virtual environment:

```console
# Linux/macOS
python3 -m venv ghost
source ghost/bin/activate
pip install -r requirements.txt
```

<details>
  <summary>Windows instructions (click to expand)</summary>
  
```cmd
:: Windows (CMD/PowerShell)
python -m venv ghost
ghost\Scripts\activate
pip install -r requirements.txt
```
</details>

3. Set up your environment variables:

Copy `.env.example` to `.env.local` and configure the following required values:

```
LIVEKIT_URL=<your LiveKit server URL>
LIVEKIT_API_KEY=<your API Key>
LIVEKIT_API_SECRET=<your API Secret>
AWS_ACCESS_KEY_ID=<your AWS access key>
AWS_SECRET_ACCESS_KEY=<your AWS secret key>
AWS_REGION=<your AWS region>
AWS_BUCKET_NAME=<your S3 bucket name>
DEEPGRAM_API_KEY=<your Deepgram API key>
CARTESIA_API_KEY=<your Cartesia API key>
```

4. Download required files:

```console
python agent.py download-files
```

5. Start the development server:

```console
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Reference

### Health Check
`GET /`
- Returns: `{ "message": "Welcome to the Jarvis Backend API" }`

### Start Room Recording (Egress)
`POST /egress/start`
- Query parameters:
  - `user_id` (str, required): Unique user/session identifier
  - `room_name` (str, required): Name of the LiveKit room to record
  - `audio_only` (bool, Optional): To record only audio or both ?
- Returns: `{ "message": ..., "info": ... }`
- Errors: 500 if egress manager is not initialized or backend error

### Stop Room Recording (Egress)
`POST /egress/stop`
- Query parameters:
  - `egress_id` (str, required): ID of the egress session to stop
- Returns: `{ "message": ..., "info": ... }`
- Errors: 500 if egress manager is not initialized or backend error

### List Recordings for User
`GET /list`
- Query parameters:
  - `user_id` (str, required): User/session identifier
- Returns: `{ "recordings": [...] }`
- Errors: 500 on backend error, 422 if missing user_id

### Get Download URL for Recording
`GET /get_file_url`
- Query parameters:
  - `file_key` (str, required): Key or path of the file
  - `expiration` (int, optional): Expiration time in seconds
- Returns: `{ "url": ... }`
- Errors: 500 on backend error, 422 if missing file_key

## Testing

Run the test suite using pytest:

```bash
pytest test_main.py
```

The test suite covers all API endpoints and error handling scenarios.

## Example Usage

```bash
# Start a recording
curl -X POST "http://localhost:8000/egress/start?user_id=test&room_name=myroom"

# List recordings
curl "http://localhost:8000/list?user_id=test"

# Get a download URL
curl "http://localhost:8000/get_file_url?file_key=sessions/test/file1.mp4"
```

## Frontend Integration

This API is designed to work with a frontend application. You can:

- Use one of the example frontends from [livekit-examples](https://github.com/livekit-examples/)
- Create your own using [LiveKit client quickstarts](https://docs.livekit.io/realtime/quickstarts/)
- Test with hosted [Sandbox](https://cloud.livekit.io/projects/p_/sandbox) frontends
