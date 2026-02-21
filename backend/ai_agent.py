# backend/ai_agent.py
import requests
import os

# Pull config from your .env file, with sensible defaults for local Ollama
LLM_URL = os.getenv("LLM_URL", "http://ollama-llm:11434/api/generate")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")

def analyze_logs_with_ai(server_id: str, log_context: list, error_line: str):
    """
    Takes a chunk of logs and the triggering error line, sends it to the LLM,
    and prints/handles the recommendation.
    """
    print(f"[{server_id}] AI Agent Triggered by: {error_line}")
    
    # Combine the list of logs into a single string block
    log_text = "\n".join(log_context)
    
    prompt = f"""
    You are an expert game server administrator monitoring a Docker-based server.
    An error just occurred. 
    
    Here are the last 50 lines of the server logs leading up to the error:
    --- LOGS START ---
    {log_text}
    --- LOGS END ---
    
    The specific error line detected was: "{error_line}"
    
    Task: 
    1. Identify the root cause of the error.
    2. Provide a short, actionable recommendation on how to fix it.
    Keep your response under 3 sentences.
    """

    try:
        response = requests.post(LLM_URL, json={
            "model": LLM_MODEL, 
            "prompt": prompt,
            "stream": False
        }, timeout=60) # Good practice to add a timeout for LLM calls
        
        if response.status_code == 200:
            ai_recommendation = response.json().get("response", "").strip()
            
            # Print to your backend console
            print(f"\n[{server_id}] --- AI RECOMMENDATION ---")
            print(ai_recommendation)
            print("-" * 30 + "\n")
            
            # Return it in case you want to use it synchronously elsewhere
            return ai_recommendation
        else:
            print(f"[{server_id}] AI Provider returned error: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"[{server_id}] AI Analysis network failure: {e}")
    except Exception as e:
        print(f"[{server_id}] Unexpected AI Error: {e}")
        
    return None