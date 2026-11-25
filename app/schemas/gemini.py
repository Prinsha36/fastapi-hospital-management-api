from typing import Annotated
from typing import Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator


class GeminiTestRequest(BaseModel):
    prompt: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
    ] = "Reply exactly: Gemini API is connected."


class GeminiTestOut(BaseModel):
    model: str
    response: str


class GeminiChatMessage(BaseModel):
    role: Literal["user", "model"]
    text: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=1000),
    ]


class GeminiChatRequest(BaseModel):
    messages: list[GeminiChatMessage] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def validate_conversation(self):
        if self.messages[0].role != "user" or self.messages[-1].role != "user":
            raise ValueError("Conversation must start and end with a user message")
        if any(left.role == right.role for left, right in zip(self.messages, self.messages[1:])):
            raise ValueError("Conversation messages must alternate between user and model")
        return self
