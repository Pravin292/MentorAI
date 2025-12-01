from flask import Flask, render_template, request
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# API Keys from environment variables
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Debug: Print key status on startup
print("=" * 50)
print("🔑 API Key Status:")
print(f"OpenRouter Key Loaded: {bool(OPENROUTER_API_KEY)}")
if OPENROUTER_API_KEY:
    print(f"OpenRouter Key Preview: {OPENROUTER_API_KEY[:15]}...")
print(f"Gemini Key Loaded: {bool(GEMINI_API_KEY)}")
if GEMINI_API_KEY:
    print(f"Gemini Key Preview: {GEMINI_API_KEY[:15]}...")
print("=" * 50)

def student_agent(user_input):
    """
    Student Agent - Uses OpenRouter API with Llama model
    """
    try:
        if not OPENROUTER_API_KEY:
            return "Error: OPENROUTER_API_KEY not found in environment variables"
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "meta-llama/llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "You are a student trying to solve the task."},
                {"role": "user", "content": user_input}
            ]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    
    except Exception as e:
        return f"Error in Student Agent: {str(e)}"

def teacher_agent(user_input, student_response):
    """
    Teacher Agent - Uses Google Gemini API to evaluate student's answer
    """
    try:
        if not GEMINI_API_KEY:
            return "Error: GEMINI_API_KEY not found in environment variables"
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        
        prompt = f"""You are a teacher evaluating a student's answer.

Original Question/Task:
{user_input}

Student's Answer:
{student_response}

Please evaluate the student's answer and provide:
1. Corrections (if any mistakes found)
2. Improvements (suggestions to make it better)
3. Score (out of 10)
4. Summary (brief overall assessment)

Format your response clearly with sections."""

        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    
    except Exception as e:
        return f"Error in Teacher Agent: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def index():
    student_output = ""
    teacher_feedback = ""
    user_input = ""
    
    if request.method == 'POST':
        user_input = request.form.get('user_input', '')
        
        if user_input.strip():
            # Step 1: Student generates answer
            student_output = student_agent(user_input)
            
            # Step 2: Teacher evaluates student's answer
            teacher_feedback = teacher_agent(user_input, student_output)
    
    return render_template('index.html', 
                         user_input=user_input,
                         student_output=student_output, 
                         teacher_feedback=teacher_feedback)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
