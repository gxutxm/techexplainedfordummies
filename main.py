from audio_capture import record_audio, transcribe_audio
from agents import interviewer_agent, evaluator_agent
from dotenv import load_dotenv
import os

def main():
    # Load environment variables
    load_dotenv()
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not found in environment variables.")
        print("Please create a .env file and add your Anthropic API key.")
        return

    print("="*50)
    print("      AI Interview Assistant (Voice Enabled)      ")
    print("="*50)
    
    print("\nWelcome! Please provide a brief context or abstract for your technical presentation.")
    context = input("Context: ")
    
    print("\nGreat! Let's start the interview. The Executive Interviewer will ask you a question.")
    print("You will have a few turns to speak.")
    
    num_turns = 3
    conversation_history = []
    
    for turn in range(num_turns):
        print(f"\n{'-'*20} Turn {turn + 1}/{num_turns} {'-'*20}")
        
        # 1. Record and transcribe candidate's answer
        input("\nPress Enter to start recording (10 seconds)...")
        audio, fs = record_audio(duration=10)
        candidate_text = transcribe_audio(audio, fs)
        
        print(f"\n[Candidate (You)]: {candidate_text}")
        if not candidate_text:
            print("No speech detected. Please try again.")
            continue
            
        # 2. Get interviewer's response
        print("\n[Interviewer thinking...]")
        interviewer_reply = interviewer_agent(context, candidate_text, conversation_history)
        print(f"\n[Interviewer]: {interviewer_reply}")
        
        # 3. Update history
        conversation_history.append({"role": "user", "content": candidate_text})
        conversation_history.append({"role": "assistant", "content": interviewer_reply})
        
    print("\n" + "="*50)
    print("                Interview Complete!               ")
    print("="*50)
    
    print("\nGenerating feedback from the Evaluator Agent...")
    
    # Evaluate the transcript
    feedback = evaluator_agent(conversation_history)
    print("\n" + "="*50)
    print("                Evaluator Feedback                ")
    print("="*50 + "\n")
    print(feedback)

if __name__ == "__main__":
    main()
