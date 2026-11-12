from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3,
)

print("Sending request to Groq...")

response = llm.invoke("Reply with only: Groq is working.")

print("\nGroq response:")
print(response.content)
