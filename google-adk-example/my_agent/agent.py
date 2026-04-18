from google.adk.agents.llm_agent import Agent
from pydantic import BaseModel


class SkillsList(BaseModel):
    languages: list[str]
    libraries: list[str]
    frameworks: list[str]


root_agent = Agent(
    model="gemini-2.0-flash",
    name="root_agent",
    description="Extracts a list of required skills from a job vacancy description.",
    instruction="You are a helpful assistant. When given a job vacancy description, extract technical skills grouped into: programming languages, libraries, and frameworks. Ignore soft skills, experience levels, and other non-technical requirements.",
    output_schema=SkillsList,
)

