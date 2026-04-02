"""Base agent class for all Noor AI agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import anthropic

from src.utils.config import settings


@dataclass
class AgentResponse:
    """Standard response from any agent."""
    text: str
    text_ar: str  # Arabic response
    action: str | None = None  # Optional action taken
    data: dict | None = None  # Optional structured data


class BaseAgent(ABC):
    """Base class for all AI agents in Noor."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-6"

    @abstractmethod
    async def handle(self, merchant_id: int, message: str, context: dict) -> AgentResponse:
        """Process a message and return a response."""
        ...

    async def ask_claude(self, system_prompt: str, user_message: str) -> str:
        """Send a message to Claude and get a response."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text
