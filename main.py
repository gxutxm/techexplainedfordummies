import os
import sys
from dotenv import load_dotenv

# Add backend to path so we can import its modules directly
# This allows us to use the shared backend logic without a separate server process
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
if backend_path not in sys.path:
    sys.path.append(backend_path)

import session_store
import file_parser
from agents import interviewer, evaluator
from audio_capture import record_audio, transcribe_audio
import tempfile
import json
import sounddevice as sd
import soundfile as sf
from deepgram import DeepgramClient
from deepgram.clients.speak.v1 import SpeakOptions

# Load environment variables (API keys)
load_dotenv()

# Initialize Deepgram client
deepgram = DeepgramClient(api_key=os.environ.get("DEEPGRAM_API_KEY"))

def speak(text):
    """Interviewer speaks the response using Deepgram TTS."""
    print(f"\n[Interviewer]: {text}")
    try:
        options = SpeakOptions(
            model="aura-orion-en", # Professional male voice
        )
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        deepgram.speak.v("1").save(tmp_path, {"text": text}, options)

        data, fs = sf.read(tmp_path)
        sd.play(data, fs)
        sd.wait()
    except Exception as e:
        print(f"[TTS Error - check DEEPGRAM_API_KEY]: {e}")
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

def load_profiles():
    profile_path = os.path.join(backend_path, 'agents', 'interviewer_profiles.json')
    with open(profile_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    print("="*60)
    print("      AI Interview Assistant (Integrated Voice Mode)      ")
    print("="*60)
    
    profiles = load_profiles()
    profile_keys = list(profiles.keys())
    
    print("\nAvailable Interviewer Profiles:")
    for i, key in enumerate(profile_keys, 1):
        print(f"{i}. {profiles[key]['name']} - {profiles[key]['description']}")
        
    while True:
        try:
            choice = input(f"\nSelect a profile (1-{len(profile_keys)}):\n> ")
            profile_idx = int(choice) - 1
            if 0 <= profile_idx < len(profile_keys):
                selected_profile_key = profile_keys[profile_idx]
                selected_profile = profiles[selected_profile_key]
                break
            else:
                print(f"Invalid choice, please select a number between 1 and {len(profile_keys)}.")
        except ValueError:
            print("Please enter a valid number.")

    system_prompt = f"""You are acting as the following persona: {selected_profile['name']}
{selected_profile['description']}

Role details:
{selected_profile['evaluation_prompt']}

Your job in this interview:
- Probe for clarity based on your persona.
- Ask ONE short, focused follow-up question at a time.
- Keep your responses SHORT (2–4 sentences max): a brief reaction + one question.
- Never summarize or repeat back what was said at length.
- Do NOT use bullet points, numbered lists, or headers.
- Sound natural and conversational, like a real person speaking.
"""

    print(f"\nWelcome! I'll act as a {selected_profile['name']} interviewing you about your project.")
    
    input_choice = input(
        "\nChoose input method:\n"
        "1. Type abstract manually\n"
        "2. Upload file (PDF / DOCX / PPTX / TXT)\n"
        "Enter 1 or 2:\n> "
    ).strip()

    if input_choice == "2":
        file_path = input("\nEnter full file path:\n> ").strip()

        if not os.path.exists(file_path):
            print("Error: File not found.")
            return

        print("\n[Parsing file...]")
        try:
            with open(file_path, "rb") as f:
                contents = f.read()
                
            ext = file_parser._get_extension(file_path)
            if ext == ".pdf":
                context = file_parser._parse_pdf(contents)
            elif ext == ".docx":
                context = file_parser._parse_docx(contents)
            elif ext == ".pptx":
                context = file_parser._parse_pptx(contents)
            elif ext == ".txt":
                context = contents.decode("utf-8", errors="ignore").strip()
            else:
                print(f"Error: Unsupported file type '{ext}'. Supported: .pdf, .docx, .pptx, .txt")
                return
        except Exception as e:
            print(f"Error parsing file: {str(e)}")
            return
            
        if not context or len(context.strip()) < 20:
            print("Error: Extracted text is too short or empty. Please provide a more detailed document.")
            return
    else:
        context = input("\nPlease provide a brief context or abstract for your presentation:\n> ")
        
        if not context or len(context.strip()) < 20:
            print("Please provide a more detailed abstract to begin.")
            return

    # 1. Initialize a session using the backend logic
    session = session_store.create_session(source_text=context.strip())
    session_id = session.session_id
    
    # 2. START FLOW: Request user's initial explanation
    print("\n" + "-"*40)
    print("READY: Please provide your initial explanation or pitch now.")
    print("-"*40)
    
    audio, fs = record_audio(duration=60)
    initial_pitch = transcribe_audio(audio, fs)
    
    if not initial_pitch:
        print("No audio detected. Exiting.")
        return

    print(f"\n[You]: {initial_pitch}")
    session_store.append_turn(session_id, role="user", content=initial_pitch)

    # 3. Main Interview Loop
    while True:
        current_session = session_store.get_session(session_id)
        
        # Check if interview is complete (based on turn count)
        if interviewer.is_interview_complete(current_session.turn_count):
            break
            
        # Get next follow-up question from AI based on the last user turn
        print("\n[Interviewer thinking...]")
        transcript_data = [msg.model_dump() if hasattr(msg, 'model_dump') else msg.dict() for msg in current_session.transcript]
        
        agent_reply = interviewer.get_next_question(
            source_text=context,
            transcript=transcript_data,
            turn_count=current_session.turn_count,
            system_prompt=system_prompt
        )
        
        session_store.append_turn(session_id, role="assistant", content=agent_reply)
        speak(agent_reply)

        # Capture user's response to the AI's question
        audio, fs = record_audio(duration=60)
        candidate_text = transcribe_audio(audio, fs)
        
        print(f"\n[You]: {candidate_text}")
        
        if not candidate_text:
            print("I didn't catch that. Could you please repeat?")
            # Force a retry by not appending a turn and looping back
            continue
            
        session_store.append_turn(session_id, role="user", content=candidate_text)

    # 4. Final Closing Remark
    current_session = session_store.get_session(session_id)
    transcript_data = [msg.model_dump() if hasattr(msg, 'model_dump') else msg.dict() for msg in current_session.transcript]
    
    closing_remark = interviewer.get_next_question(
        source_text=context,
        transcript=transcript_data,
        turn_count=current_session.turn_count,
        system_prompt=system_prompt
    )
    speak(closing_remark)
    
    print("\n" + "="*60)
    print("                Interview Complete!               ")
    print("="*60)
    
    # 8. Generate Evaluator Feedback
    print("\nGenerating feedback from the Evaluator Agent...")
    feedback = evaluator.evaluate_transcript(
        source_text=context,
        transcript=current_session.transcript
    )
    
    print("\n" + "="*45)
    print("          COMMUNICATION FEEDBACK          ")
    print("="*45)
    print(f"Clarity:      {feedback.clarity}/10")
    print(f"Tone:         {feedback.tone}/10")
    print(f"Jargon Score: {feedback.jargon_score}/10")
    
    if feedback.jargon_terms:
        print("\nJargon detected:")
        for item in feedback.jargon_terms:
            print(f"- '{item.term}': try '{item.suggestion}'")
            
    print(f"\nSummary: {feedback.summary}")
    print(f"Top Tip: {feedback.top_fix}")
    print("="*45 + "\n")

if __name__ == "__main__":
    main()
