from openai import AsyncOpenAI

MODEL = "gpt-4o-mini"


def get_client() -> AsyncOpenAI:
    return AsyncOpenAI()
