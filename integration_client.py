import pyttsx3
import requests
import time
from audio_capture import record_audio, transcribe_audio

# Initialize TTS engine for the Interviewer's voice
engine = pyttsx3.init()
engine.setProperty('rate', 160) # Natural speaking pace

def speak(text):
    """Interviewer speaks the response."""
    print(f"\n[Interviewer]: {text}")
    engine.say(text)
    engine.runAndWait()

def run_integrated_session(api_base_url="http://localhost:8000"):
    print("=== AI Interview Assistant (Integrated Voice + Backend) ===")
    
    # 1. Start Session with the Backend
    context = input("Enter your technical abstract/context: ")
    try:
        response = requests.post(f"{api_base_url}/session/start", json={"source_text": context})
        response.raise_for_status()
        data = response.json()
        session_id = data["session_id"]
        first_question = data["first_question"]
        
        # Interviewer speaks the first question
        speak(first_question)
        
        while True:
            # 2. Capture and Transcribe User Voice (STT)
            input("\n[Press Enter then speak for 10 seconds...]")
            audio, fs = record_audio(duration=10)
            user_text = transcribe_audio(audio, fs)
            print(f"\n[You (Transcribed)]: {user_text}")
            
            if not user_text:
                print("No speech detected, please try again.")
                continue

            # 3. Send Message to Backend
            msg_response = requests.post(f"{api_base_url}/session/message", json={
                "session_id": session_id,
                "user_message": user_text
            })
            msg_response.raise_for_status()
            msg_data = msg_response.json()
            
            agent_reply = msg_data["agent_reply"]
            interview_complete = msg_data["interview_complete"]
            
            # 4. Interviewer speaks the reply (TTS)
            speak(agent_reply)
            
            if interview_complete:
                print("\n--- Interview Finished ---")
                break
        
        # 5. Final Evaluation
        print("\nRequesting final communication report...")
        eval_response = requests.post(f"{api_base_url}/session/{session_id}/evaluate")
        eval_response.raise_for_status()
        report = eval_response.json()
        
        print("\n" + "="*40)
        print("          EVALUATOR REPORT          ")
        print("="*40)
        print(f"Clarity Score: {report['clarity']}/10")
        print(f"Tone Score:    {report['tone']}/10")
        print(f"Jargon Score:  {report['jargon_score']}/10")
        print(f"\nSummary: {report['summary']}")
        print(f"Top Tip: {report['top_fix']}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not connect to backend at {api_base_url}. Make sure the server is running!")

if __name__ == "__main__":
    run_integrated_session()
