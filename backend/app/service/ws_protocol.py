"""
Pure websocket protocol parsing helpers.
"""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from pydantic import ValidationError

from app.service.contracts.realtime import (
    PresenceClientMessage,
    PresenceEntityType,
    PresenceStatus,
    RealtimeChannel,
    RealtimeErrorPayload,
    SubscribeClientMessage,
)


@dataclass(frozen=True, slots=True)
class ProjectSubscribeParsed:
    kind: Literal["subscribe"]
    channels: set[RealtimeChannel]


@dataclass(frozen=True, slots=True)
class ProjectPresenceParsed:
    kind: Literal["presence"]
    status: PresenceStatus
    entity_type: PresenceEntityType
    entity_id: UUID | None


@dataclass(frozen=True, slots=True)
class ProjectUnknownParsed:
    kind: Literal["unknown"]


@dataclass(frozen=True, slots=True)
class ProjectMalformedParsed:
    kind: Literal["malformed"]


ProjectClientMessageParsed = (
    ProjectSubscribeParsed
    | ProjectPresenceParsed
    | ProjectUnknownParsed
    | ProjectMalformedParsed
)


@dataclass(frozen=True, slots=True)
class NotificationUnknownParsed:
    kind: Literal["unknown"]


@dataclass(frozen=True, slots=True)
class NotificationMalformedParsed:
    kind: Literal["malformed"]


NotificationClientMessageParsed = (
    NotificationUnknownParsed | NotificationMalformedParsed
)


def build_error_payload(code: str, message: str) -> dict[str, str]:
    return RealtimeErrorPayload(code=code, message=message).model_dump(mode="json")


def parse_project_client_message(payload: object) -> ProjectClientMessageParsed:
    if not isinstance(payload, dict):
        return ProjectMalformedParsed(kind="malformed")

    message_type = payload.get("type")

    if message_type == "subscribe":
        try:
            message = SubscribeClientMessage.model_validate(payload)
        except ValidationError:
            return ProjectMalformedParsed(kind="malformed")
        return ProjectSubscribeParsed(kind="subscribe", channels=set(message.channels))

    if message_type == "presence":
        try:
            message = PresenceClientMessage.model_validate(payload)
        except ValidationError:
            return ProjectMalformedParsed(kind="malformed")
        return ProjectPresenceParsed(
            kind="presence",
            status=message.status,
            entity_type=message.entity_type,
            entity_id=message.entity_id,
        )

    return ProjectUnknownParsed(kind="unknown")


def parse_notification_client_message(
    payload: object,
) -> NotificationClientMessageParsed:
    if not isinstance(payload, dict):
        return NotificationMalformedParsed(kind="malformed")
    return NotificationUnknownParsed(kind="unknown")
