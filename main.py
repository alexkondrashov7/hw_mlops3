from inference import ModelRunner
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict,Any
import os

MODEL_PATH = os.getenv("MODEL_PATH", "model.pkl")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0")

model = ModelRunner(model_path=MODEL_PATH, version=MODEL_VERSION)
app = FastAPI()


class Features(BaseModel):
    features : Dict[str, Any]


@app.get('/health')
def health():
    return{ "status" : "ok", "version" : model.version}


@app.post("/predict")
def predict (req : Features):
    y, prob = model.predict(req.features)
    return {"predict" : y,
            "prob" : prob,
            "model_version" : model.version}