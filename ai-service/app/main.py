import json
import logging
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.schema.contracts import CompleteRequest
from app.service.brain_service import complete_stream
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


@app.post("/v1/complete")
async def complete(
    body: CompleteRequest,
    _: Annotated[None, Depends(verify_service_secret)],
):
    async def event_stream():
        try:
            async for event in complete_stream(body):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:
            logger.exception("AI complete pipeline failed")
            payload = {"type": "error", "error": "AI complete pipeline failed"}
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
