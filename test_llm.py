import os
from dotenv import load_dotenv
from google import genai

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
client = genai.Client()

cevap = client.models.generate_content(model="gemini-3.5-flash", contents="Merhaba de.")
print(cevap.text)