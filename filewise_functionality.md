# AI Interview Assistant - Filewise Functionality

This document outlines the current architecture and functionality of each file in the project.

## 📂 Root Directory
The root directory contains the core CLI integrated application, environment configuration, and dependency management.

- **`main.py`**  
  The primary entry point for the integrated Voice CLI application. It orchestrates the interview workflow, combining local microphone input (STT), backend agent logic (Interviewing/Evaluating), and Deepgram for Text-to-Speech (TTS) output.
- **`audio_capture.py`**  
  Handles microphone interactions and Speech-to-Text (STT) capabilities. Utilizes `sounddevice` for recording and `openai-whisper` for transcribing the captured audio locally.
- **`integration_client.py`** *(Deprecated)*  
  The legacy script used before the project was compacted into `main.py`. Previously handled HTTP interactions with the backend API.
- **`.env`** & **`.env.example`**  
  Environment variable configuration files. Stores API keys for LLM providers (Groq/Anthropic) and external services (Deepgram).
- **`requirements.txt`**  
  Manages Python dependencies, locking versions for stability (e.g., locking Deepgram SDK to v3.4.0).
- **`STATUS.md`**  
  A general status tracker or notes file.

---

## 📂 `backend/`
The backend directory contains the core intelligence, session management, and API endpoints for the web/FastAPI architecture.

- **`main_backend.py`**  
  The entry point for the FastAPI server (previously named `main.py`). Mounts the API routes to allow web clients to interact with the assistant over HTTP.
- **`config.py`**  
  Centralized configuration file. Handles the `LLM_PROVIDER` toggle (switching between Groq and Anthropic) and defines the exact models and token limits used by the agents.
- **`llm_client.py`**  
  An abstraction layer for Large Language Model communication. Ensures the agents have a uniform way to prompt the LLM, dynamically routing requests to either Groq or Anthropic based on `config.py`.
- **`session_store.py`**  
  An in-memory state manager. Stores the interview transcripts, source text (abstracts), and turn counts for active sessions.
- **`schemas.py`**  
  Defines Pydantic data models used across the application. Provides strict type-checking for API requests/responses and ensures the LLM's structured JSON outputs (like the Evaluation Report) match expectations.
- **`file_parser.py`**  
  A utility module supporting the `/session/start-from-file` API endpoint. Extracts plain text from various uploaded file formats (PDF, DOCX, PPTX, TXT) to be used as context.
- **`samples.py`**  
  Contains hardcoded, sample technical abstracts (e.g., RAG, ML Fraud Detection). Used by the frontend UI to quickly load context for demonstrations.

### 📂 `backend/agents/`
Contains the AI personas and prompt logic.

- **`interviewer.py`**  
  The "Executive Persona" agent. Takes the user's abstract and transcript history to ask ONE non-technical follow-up question per turn. Enforces the conversational rules.
- **`evaluator.py`**  
  The "Communication Coach" agent. Runs at the end of an interview. Analyzes the entire transcript to score the user on clarity, tone, and jargon usage, returning structured JSON feedback.

### 📂 `backend/routes/`
Contains the FastAPI HTTP routing definitions.

- **`session.py`**  
  Defines the API endpoints (`/session/start`, `/session/message`, `/session/{id}/evaluate`, etc.). Maps web requests to the underlying `session_store` and `agents` logic.
