import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()


def get_llm():
    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3,
    )


def split_transcript(transcript: str) -> list:
    splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)
    return splitter.split_text(transcript)


def summarize(transcript: str) -> str:
    llm = get_llm()

    map_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert meeting summarizer. "
                "Summarize this portion of a meeting transcript concisely. "
                "Preserve important information, key points, and context.",
            ),
            ("human", "{text}"),
        ]
    )

    map_chain = map_prompt | llm | StrOutputParser()

    chunks = split_transcript(transcript)

    print(f"Total text chunks: {len(chunks)}")

    chunk_summaries = []

    for i, chunk in enumerate(chunks):
        print(f"Summarizing chunk {i + 1}/{len(chunks)}...")

        summary = map_chain.invoke({"text": chunk})
        chunk_summaries.append(summary)

        print(f"Chunk {i + 1} summarized successfully.")

    combined = "\n\n".join(chunk_summaries)

    print("Generating final meeting summary...")

    combined_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert meeting summarizer. "
                "Combine these partial summaries into one professional meeting summary. "
                "Use clear bullet points and organize related information together. "
                "Do not invent information.",
            ),
            ("human", "{text}"),
        ]
    )

    combined_chain = combined_prompt | llm | StrOutputParser()

    final_summary = combined_chain.invoke({"text": combined})

    print("Meeting summary generated successfully.")

    return final_summary


def generate_title(transcript: str) -> str:
    llm = get_llm()

    title_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Generate a short professional meeting title "
                "based on the transcript. Maximum 8 words. "
                "Return only the title.",
            ),
            ("human", "{text}"),
        ]
    )

    title_chain = title_prompt | llm | StrOutputParser()

    title = title_chain.invoke({"text": transcript[:2000]})

    return title.strip()
