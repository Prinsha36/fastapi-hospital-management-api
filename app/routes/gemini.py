import os

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_admin
from app.schemas.gemini import GeminiChatRequest, GeminiTestOut, GeminiTestRequest

MODEL = "gemini-3.6-flash"
GENERATE_CONTENT_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

router = APIRouter(prefix="/gemini", tags=["Gemini"])


def gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


@router.get("/status", dependencies=[Depends(require_admin)], summary="Check Gemini configuration")
async def gemini_status() -> dict[str, bool]:
    return {"configured": bool(gemini_api_key())}


async def generate_text(contents: list[dict], max_output_tokens: int) -> str:
    api_key = gemini_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured")

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            response = await client.post(
                GENERATE_CONTENT_URL,
                headers={"x-goog-api-key": api_key},
                json={
                    "contents": contents,
                    "generationConfig": {
                        "maxOutputTokens": max_output_tokens,
                        "thinkingConfig": {"thinkingLevel": "low"},
                    },
                },
            )
    except httpx.ConnectTimeout:
        raise HTTPException(status_code=504, detail="The server timed out connecting to Gemini")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Gemini did not respond in time. Try again shortly")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not connect to the Gemini API")

    if response.status_code == 503:
        raise HTTPException(status_code=503, detail="Google's Gemini service is temporarily unavailable. Try again shortly")
    if response.status_code == 504:
        raise HTTPException(status_code=504, detail="Google's Gemini service timed out. Try again shortly")

    if not response.is_success:
        try:
            error_payload = response.json()
        except ValueError:
            error_payload = {}
        error = error_payload.get("error") if isinstance(error_payload, dict) else None
        detail = error.get("message") if isinstance(error, dict) else None
        if not isinstance(detail, str) or not detail:
            detail = "The provider returned an error"
        raise HTTPException(
            status_code=502,
            detail=f"Gemini API returned HTTP {response.status_code}: {detail[:500]}",
        )

    try:
        result = response.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Gemini API returned invalid JSON")

    candidates = result.get("candidates") if isinstance(result, dict) else None
    if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
        raise HTTPException(status_code=502, detail="Gemini API returned no response candidate")

    content = candidates[0].get("content")
    parts = content.get("parts") if isinstance(content, dict) else None
    text_parts = [
        part["text"]
        for part in parts or []
        if isinstance(part, dict)
        and isinstance(part.get("text"), str)
        and not part.get("thought", False)
    ]
    generated_text = "\n".join(text_parts).strip()
    if not generated_text:
        raise HTTPException(status_code=502, detail="Gemini API returned no text response")
    return generated_text


@router.post(
    "/test",
    response_model=GeminiTestOut,
    dependencies=[Depends(require_admin)],
    summary="Test the Gemini API",
    description="Use synthetic, non-sensitive text only. Free-tier prompts may be used to improve Google's products.",
)
async def test_gemini(body: GeminiTestRequest):
    generated_text = await generate_text(
        [{"parts": [{"text": body.prompt}]}],
        max_output_tokens=128,
    )
    return GeminiTestOut(model=MODEL, response=generated_text)


@router.post(
    "/chat",
    response_model=GeminiTestOut,
    dependencies=[Depends(require_admin)],
    summary="Chat with Gemini",
    description="Use synthetic, non-sensitive text only. Free-tier prompts may be used to improve Google's products.",
)
async def chat_with_gemini(body: GeminiChatRequest):
    contents = [
        {"role": message.role, "parts": [{"text": message.text}]}
        for message in body.messages
    ]
    generated_text = await generate_text(contents, max_output_tokens=512)
    return GeminiTestOut(model=MODEL, response=generated_text)
