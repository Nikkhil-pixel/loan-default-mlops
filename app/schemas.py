"""Build request validation models directly from the shared parameter file."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

from src.config import load_config


def build_request_model(config: dict[str, Any] | None = None) -> type[BaseModel]:
    """Create a strict prediction schema using configured feature names and constraints."""
    config = config or load_config()
    project = config["project"]
    numeric = set(project["numeric_features"])
    categorical = set(project["categorical_features"])
    fields: dict[str, tuple[Any, Any]] = {}
    for name in project["feature_columns"]:
        if name in categorical:
            choices = tuple(project["categories"][name])
            annotation = Literal.__getitem__(choices)
            field = Field(..., description=f"Allowed values: {', '.join(choices)}")
        elif name in numeric:
            annotation = float
            lower, upper = project["value_ranges"][name]
            field = Field(..., ge=lower, le=upper, description=f"Configured range: {lower} to {upper}.")
        else:
            raise ValueError(f"Configured feature {name!r} has no numeric or categorical type.")
        fields[name] = (annotation, field)

    class RequestBase(BaseModel):
        model_config = ConfigDict(extra="forbid")

    return create_model("PredictionInput", __base__=RequestBase, **fields)


PredictionInput = build_request_model()
