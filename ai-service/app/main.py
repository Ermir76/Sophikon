import json
import logging
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.schema.contracts import ChatRequest, EstimateRequest, SuggestionsRequest
from app.service.brain_service import build_estimates, build_suggestions, stream_chat_events
from app.service.model_catalog import get_catalog_payload

# Intentional small-service exception: keep routing and endpoint definitions in a
# single module while the AI service surface remains tiny and easy to scan.
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
)

logger = logging.getLogger(__name__)


def verify_service_secret(
    x_ai_service_secret: Annotated[str | None, Header()] = None,
) -> None:
    if x_ai_service_secret != settings.AI_SERVICE_SHARED_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service credentials",
        )


@app.get("/health")
async def health():
    return {"status": "ok", "mode": settings.AI_MODE}


@app.get("/v1/brain/models")
async def list_models(
    _: Annotated[None, Depends(verify_service_secret)],
):
    return get_catalog_payload()


@app.post("/v1/brain/chat")
async def chat(
    body: ChatRequest,
    _: Annotated[None, Depends(verify_service_secret)],
):
    async def event_stream():
        try:
            async for event in stream_chat_events(body):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:
            logger.exception("AI chat pipeline failed")
            payload = {"type": "error", "error": "AI chat pipeline failed"}
            yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/v1/brain/estimate")
async def estimate(
    body: EstimateRequest,
    _: Annotated[None, Depends(verify_service_secret)],
):
    # This helper is intentionally synchronous: it does in-process computation only.
    return build_estimates(body)


@app.post("/v1/brain/suggestions")
async def suggestions(
    body: SuggestionsRequest,
    _: Annotated[None, Depends(verify_service_secret)],
):
    # This helper is intentionally synchronous: it does in-process computation only.
    return build_suggestions(body)
