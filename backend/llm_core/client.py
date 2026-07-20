import json
import os

from dotenv import load_dotenv
from google import genai

from llm_core.prompts.classify import CLASSIFY_SYSTEM_PROMPT, CLASSIFY_USER_PROMPT
from llm_core.prompts.reply import REPLY_SYSTEM_PROMPT, REPLY_USER_PROMPT

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-2.5-flash"


def classify_message(message: str) -> bool:
    """メッセージの緊急度を判定する。緊急ならTrue、通常ならFalseを返す。"""
    response = client.models.generate_content(
        model=MODEL,
        config=genai.types.GenerateContentConfig(
            system_instruction=CLASSIFY_SYSTEM_PROMPT,
            response_mime_type="application/json",
        ),
        contents=CLASSIFY_USER_PROMPT.format(message=message),
    )
    result = json.loads(response.text)
    return result["is_urgent"]


def generate_reply(message: str, listing_info: str) -> str:
    """ゲストへの返信文を生成する。"""
    response = client.models.generate_content(
        model=MODEL,
        config=genai.types.GenerateContentConfig(
            system_instruction=REPLY_SYSTEM_PROMPT,
            response_mime_type="application/json",
        ),
        contents=REPLY_USER_PROMPT.format(message=message, listing_info=listing_info),
    )
    result = json.loads(response.text)
    return result["reply"]
