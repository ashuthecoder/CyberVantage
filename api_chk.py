import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key from .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ GOOGLE_API_KEY not found in .env file")
    exit()

# Configure the Gemini client
genai.configure(api_key=api_key)

try:
    # Send a simple request to gemini-2.5-pro
    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content("Say 'Hello, Gemini!' if you can read this.")
    
    print("✅ API key works!")
    print("Model response:", response.text)

except Exception as e:
    print("❌ Error:", e)
