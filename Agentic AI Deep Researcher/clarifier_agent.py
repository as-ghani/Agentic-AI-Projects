from pydantic import BaseModel, Field
from agents import Agent
import os 
from dotenv import load_dotenv

load_dotenv(override=True)

MODEL_NAME = "gpt-5.4-mini"

INSTRUCTIONS = f"""
You are a helpful assistant. 
Given a user's research query you come up with 3 clarifying questions.

Rules:
    - Keep the questions short (one sentence each question).
    - Do not answer the questions yourself
    - Ask exactly 3 questions 
    - Return JSON _Only
    - End a question with '?'
"""

class Clarification(BaseModel):
    question: list[str] = Field(description= "A list of exactly 3 questions", min_items = 3, max_items = 3 )

clarifier_agent = Agent(name = "Clarify Agent", instructions=INSTRUCTIONS, model = MODEL_NAME, output_type=Clarification)