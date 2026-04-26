# AI Interview Assistant

This project is an AI-powered interview assistant designed to simulate a conversation with a non-technical executive and provide feedback on your communication skills.

## Features
- **Speech-to-Text**: Uses OpenAI's `whisper` to transcribe spoken answers from the microphone.
- **Interviewer Agent**: Powered by Claude 3 Haiku, acts as a non-technical executive asking clarifying follow-up questions about your technical abstract.
- **Evaluator Agent**: Powered by Claude 3 Sonnet, analyzes the interview transcript and provides detailed feedback on clarity, tone, jargon usage, and improvement suggestions.

## Setup Instructions

1. **Activate the Virtual Environment**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

2. **Environment Variables**:
   Copy the `.env.example` file to `.env` and add your Anthropic API key.
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

3. **Install Dependencies** (if not already done):
   ```powershell
   pip install -r requirements.txt
   ```
   *Note: Whisper may require [FFmpeg](https://ffmpeg.org/download.html) to be installed on your system and added to your system PATH.*

## Running the Application

Execute the main script:
```powershell
python main.py
```

1. Enter a brief technical abstract or context when prompted.
2. When prompted, press Enter to start recording your response (10 seconds per turn).
3. The Interviewer Agent will reply with a follow-up question.
4. After 3 turns, the Evaluator Agent will provide detailed feedback.
