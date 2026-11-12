import os
import time

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()


def get_llm():
    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.2,
    )


def build_chain(system_prompt: str):
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", "{text}")]
    )

    return prompt | llm | StrOutputParser()


def extract_action_items(transcript: str) -> str:
    chain = build_chain("""
You are an AI meeting assistant. Extract the following from the transcript:

1. Actionable Items: Tasks, assigned persons, and deadlines.
2. Decisions: Final decisions made during the meeting.
3. Open Questions: Unanswered questions or unresolved issues.

Rules:
- Use only information from the transcript.
- Do not invent details.
- Mention "Not specified" if an owner or deadline is missing.
- Write "None" if a category has no results.
- Keep everything concise.

Output Format:

## Actionable Items
## Decisions
## Open Questions
""")

    print("Extracting actionable items...")
    result = chain.invoke({"text": transcript})
    print("Action items extracted successfully.")

    return result


def extract_decisions(transcript: str) -> str:
    chain = build_chain("""
You are an AI meeting assistant. Extract all final decisions made during the meeting.

Rules:
- Use only information from the transcript.
- Include important decisions and their context.
- Do not include suggestions or unconfirmed proposals.
- Do not invent details.
- Keep everything concise.
- Write "None" if no decisions were made.

Output Format:

## Decisions
""")

    print("Extracting key decisions...")
    time.sleep(5)
    result = chain.invoke({"text": transcript})
    print("Decisions extracted successfully.")

    return result


def extract_questions(transcript: str) -> str:
    chain = build_chain("""
You are an AI meeting assistant. Extract unanswered questions and unresolved issues from the transcript.

Rules:
- Use only information from the transcript.
- Include questions that need further discussion.
- Exclude questions that were already answered.
- Do not invent details.
- Keep everything concise.
- Write "None" if no open questions exist.

Output Format:

## Open Questions
""")

    print("Extracting open questions...")
    time.sleep(5)
    result = chain.invoke({"text": transcript})
    print("Open questions extracted successfully.")

    return result
