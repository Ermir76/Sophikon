"""
Shared PATCH-schema validation helpers.

This module centralizes explicit-null validation so we do not duplicate
the same validator across every update schema.
"""

from typing import Any, ClassVar

from pydantic import BaseModel, model_validator
from sqlalchemy import inspect


def reject_explicit_nulls_for_fields_set(model: BaseModel) -> None:
    """
    Reject explicit `null` for fields the client actually sent.

    Why this exists:
    - PATCH schemas use `T | None` for static typing correctness.
    - We still need to distinguish omitted fields (allowed) from explicit null
      (can be invalid depending on field semantics).
    - `model_fields_set` tells us which keys were provided in the payload.
    """

    for field_name in model.model_fields_set:
        if getattr(model, field_name) is None:
            raise ValueError(f"{field_name} cannot be null")


def reject_explicit_nulls_for_non_nullable_columns(
    model: BaseModel,
    *,
    sa_model: type[Any],
) -> None:
    """
    Reject explicit `null` only for NOT NULL SQLAlchemy columns.

    Midnight-debugging note:
    - If an update endpoint suddenly starts accepting invalid nulls, check this
      function first.
    - If a column's nullability changes in a migration/model, behavior updates
      automatically here because we inspect SQLAlchemy metadata at runtime.
    """

    mapper = inspect(sa_model)
    for field_name in model.model_fields_set:
        if getattr(model, field_name) is not None:
            continue
        column = mapper.columns.get(field_name)
        if column is None or column.primary_key:
            continue
        if not column.nullable:
            raise ValueError(f"{field_name} cannot be null")


class ModelPatchSchema(BaseModel):
    """
    Base class for model-backed PATCH request schemas.

    Subclasses must set `__sa_model__` to the SQLAlchemy model whose
    nullability rules should be enforced for explicit `null` values.
    """

    __sa_model__: ClassVar[type[Any]]
    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "ModelPatchSchema":
        reject_explicit_nulls_for_non_nullable_columns(self, sa_model=self.__sa_model__)
        return self
