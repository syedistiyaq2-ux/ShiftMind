import os
import sys

# Check required packages
try:
    from dotenv import load_dotenv
    from groq import Groq
except ImportError as e:
    print(f"❌ Missing package: {e.name}")
    print("Run: pip install groq python-dotenv")
    sys.exit(1)

# Load .env
load_dotenv()

# Get Groq API key
api_key = (os.getenv("GROQ_API_KEY") or "").strip().strip('"').strip("'")

if not api_key:
    print("❌ GROQ_API_KEY is missing.")
    print("Check your .env file.")
    sys.exit(1)

# Create Groq client
client = Groq(api_key=api_key)

# Models to try
models = [
    os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

# Test each model
for model in models:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": "Say exactly: ShiftMind Groq connection successful."
                }
            ],
            timeout=30,
        )

        print(f"✅ Model used: {model}")
        print(response.choices[0].message.content)
        sys.exit(0)

    except Exception as e:
        msg = str(e)

        if "401" in msg or "invalid_api_key" in msg.lower():
            print("❌ Invalid Groq API key.")
            print("Check the GROQ_API_KEY in your .env file.")
            sys.exit(1)

        elif "429" in msg:
            print(f"⏳ Rate limited on {model}. Try again later.")
            sys.exit(1)

        elif "404" in msg or "model" in msg.lower():
            print(f"⚠️ Model '{model}' unavailable. Trying next model...")
            continue

        else:
            print(f"❌ Error with {model}:")
            print(msg)
            sys.exit(1)

print("❌ None of the Groq models worked.")