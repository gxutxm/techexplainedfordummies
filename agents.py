import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize the Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def interviewer_agent(context, user_text, conversation_history):
    system_prompt = f"""You are a non-technical executive interviewer.
The candidate is presenting the following technical abstract/context:
{context}

Your job is to ask a simple, clarifying follow-up question based on what the candidate just said.
You are not technical, so focus on business impact, clarity, and practical applications.
Keep your question concise, natural, and conversational (1-2 sentences). Do not use complex jargon.
"""
    
    # Prepare the message list
    messages = conversation_history + [{"role": "user", "content": user_text}]
    
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=200,
        system=system_prompt,
        messages=messages
    )
    
    return response.content[0].text

def evaluator_agent(transcript):
    system_prompt = """You are an expert communication coach and evaluator.
Analyze the following interview transcript between a candidate and a non-technical executive.
Provide structured, constructive feedback on the candidate's performance across these 4 areas:
1. Clarity: Was the explanation easy to follow?
2. Tone: Was the tone appropriate for an executive interview?
3. Jargon usage: Did the candidate use too much technical jargon without explaining it?
4. Improvement suggestions: What specific advice would you give the candidate?

Format your response clearly with headings for each point.
"""
    
    # Format the transcript for the evaluator
    transcript_text = ""
    for msg in transcript:
        role = "Candidate" if msg["role"] == "user" else "Interviewer"
        transcript_text += f"{role}: {msg['content']}\n"

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Here is the transcript:\n\n{transcript_text}"}]
    )
    
    return response.content[0].text
