import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

print("Gemini API key loaded successfully!")

# Create Gemini client
client = genai.Client(api_key=api_key)

print("Gemini client created successfully!")

# Simple test request
response = client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents="Say hello to my customer segmentation project in one sentence."
)

print("\nGemini response:")
print(response.text)