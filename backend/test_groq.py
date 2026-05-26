from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GROQ_API_KEY')
print(f"API Key: {api_key[:15]}...")

# Test different model names
models_to_try = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-8b-8192",
    "openai/gpt-oss-20b"  # Your original model
]

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
)

print("\n🔍 Testing available models...")
try:
    models = client.models.list()
    print("✅ Available models:")
    for model in models.data:
        print(f"  - {model.id}")
except Exception as e:
    print(f"❌ Cannot list models: {e}")

print("\n🧪 Testing chat completions with different models...")
for model in models_to_try:
    try:
        print(f"\n📝 Testing: {model}")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say 'Hello, I am an AI assistant for merchant onboarding!'"}
            ],
            temperature=0.1,
            max_tokens=50
        )
        print(f"✅ Success! Response: {response.choices[0].message.content}")
        print(f"🎯 USE THIS MODEL: {model}")
        break
    except Exception as e:
        print(f"❌ Failed: {e}")