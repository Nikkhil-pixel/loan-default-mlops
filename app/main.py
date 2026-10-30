"""FastAPI serving application for the configured champion model."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated, Any

import mlflow
import mlflow.sklearn
import pandas as pd
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.logger import log_prediction
from app.schemas import PredictionInput
from src.config import load_config, project_path

CONFIG = load_config()
REGISTRY = CONFIG["registry"]
STATE: dict[str, Any] = {"model": None, "version": None, "run_id": None, "data_version": None, "error": "Model not loaded."}


def reload_model() -> dict[str, Any]:
    """Load the champion from MLflow, falling back to the portable deployment model."""
    try:
        mlflow.set_tracking_uri(REGISTRY["tracking_uri"])
        alias = REGISTRY["champion_alias"]
        uri = f"models:/{REGISTRY['model_name']}@{alias}"

        model = mlflow.sklearn.load_model(uri)
        from mlflow import MlflowClient

        version = MlflowClient(
            tracking_uri=REGISTRY["tracking_uri"]
        ).get_model_version_by_alias(REGISTRY["model_name"], alias)

        STATE.update({
            "model": model,
            "version": str(version.version),
            "run_id": version.tags.get("run_id"),
            "data_version": version.tags.get("data_version"),
            "error": None,
        })

        return {
            "status": "loaded",
            "model_name": REGISTRY["model_name"],
            "version": str(version.version),
            "alias": alias,
            "source": "mlflow",
        }

    except Exception as mlflow_error:
        try:
            model_path = project_path("models/deployment_model")
            model = mlflow.sklearn.load_model(str(model_path))

            STATE.update({
                "model": model,
                "version": "3",
                "run_id": None,
                "data_version": None,
                "error": None,
            })

            return {
                "status": "loaded",
                "model_name": REGISTRY["model_name"],
                "version": "3",
                "alias": REGISTRY["champion_alias"],
                "source": "deployment_model",
            }

        except Exception as fallback_error:
            error = (
                f"MLflow loading failed: {mlflow_error}; "
                f"deployment model loading failed: {fallback_error}"
            )
            STATE.update({
                "model": None,
                "version": None,
                "run_id": None,
                "data_version": None,
                "error": error,
            })
            return {"status": "unavailable", "error": error}


@asynccontextmanager
async def lifespan(_: FastAPI):
    reload_model()
    yield


app = FastAPI(title=CONFIG["project"]["name"], lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://loan-default-mlops-frontend.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _risk_band(probability: float) -> str:
    bands = CONFIG["api"]["risk_bands"]
    if probability < bands["low_max"]:
        return bands["low_label"]
    if probability < bands["medium_max"]:
        return bands["medium_label"]
    return bands["high_label"]


def _score(payload: dict[str, Any]) -> dict[str, Any]:
    if STATE["model"] is None:
        raise HTTPException(status_code=503, detail=f"Champion model unavailable: {STATE['error']}")
    frame = pd.DataFrame([payload], columns=CONFIG["project"]["feature_columns"])
    model = STATE["model"]
    positive_index = list(model.classes_).index(CONFIG["project"]["positive_class"])
    probability = float(model.predict_proba(frame)[0, positive_index])
    result = {
        "default_probability": probability,
        "risk_band": _risk_band(probability),
        "decision_flag": probability >= CONFIG["models"]["decision_threshold"],
    }
    log_prediction(project_path(CONFIG["api"]["request_log_path"]), {
        "input": payload,
        **result,
        "model_version": STATE["version"],
        "run_id": STATE["run_id"],
        "data_version": STATE["data_version"],
    })
    return result


def health() -> dict[str, Any]:
    if STATE["model"] is None:
        return {"status": "degraded", "model_loaded": False, "error": STATE["error"]}
    return {"status": "ok", "model_loaded": True, "version": STATE["version"]}


def predict(request: PredictionInput) -> dict[str, Any]:
    return _score(request.model_dump())


def predict_batch(requests: Annotated[list[PredictionInput], Body()]) -> dict[str, Any]:
    return {"predictions": [_score(request.model_dump()) for request in requests]}


def model_info() -> dict[str, Any]:
    if STATE["model"] is None:
        raise HTTPException(status_code=503, detail=f"Champion model unavailable: {STATE['error']}")
    return {
        "model_name": REGISTRY["model_name"],
        "version": STATE["version"],
        "alias": REGISTRY["champion_alias"],
        "run_id": STATE["run_id"],
        "data_version": STATE["data_version"],
    }


app.add_api_route(CONFIG["api"]["routes"]["health"], health, methods=["GET"])
app.add_api_route(CONFIG["api"]["routes"]["predict"], predict, methods=["POST"])
app.add_api_route(CONFIG["api"]["routes"]["batch"], predict_batch, methods=["POST"])
app.add_api_route(CONFIG["api"]["routes"]["model_info"], model_info, methods=["GET"])
app.add_api_route(CONFIG["api"]["routes"]["reload"], reload_model, methods=["POST"])
