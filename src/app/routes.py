from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import onnxruntime as rt
from config import DEPLOYED_MODEL_PATH, MODEL
from src.utils.geo import validate_and_geocode_address
import numpy as np
import pandas as pd
from src.inference.model import get_model, get_estimation
from src.app.monitoring.prometheus_metrics import track_inference_time
import time

from pydantic import BaseModel

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]

router = APIRouter()
templates = Jinja2Templates(directory="src/app/templates")

#session = rt.InferenceSession(str(DEPLOYED_MODEL_PATH))
#input_names = session.get_inputs()

pipeline = get_model(model_path=MODEL)


@router.get("/", tags=["Home"], response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/healthcheck", tags=["Health"], response_class=JSONResponse)
async def home(request: Request):
    return {'status' : 'OK'}

@router.post("/predict", tags=["Prediction"])
async def predict(
    request : Request,
    type_local: str = Form(...),
    address: str = Form(...),
    surface_habitable: float = Form(...),
    nombre_pieces: int = Form(...),
    
    surface_terrain: Optional[float] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    address_type: Optional[str] = Form(None),
    ):
    print(type_local, address, surface_habitable, nombre_pieces, surface_terrain, latitude, longitude, address_type)
 
    context = get_estimation(
        pipeline,
        address,
        type_local,
        surface_habitable,
        surface_terrain,
        nombre_pieces
    )

    context['request'] = request
    
    return templates.TemplateResponse("prediction.html", context)

@router.get("/chatbot", tags=["Chat"], response_class=HTMLResponse)
async def chatbot(request: Request):
    return templates.TemplateResponse("chatbot.html", {"request": request})

@router.post("/chat", tags=["Chat"], response_class=JSONResponse)
async def chatbot(request : ChatRequest):
    return JSONResponse(content={"message": request.messages[-1].content})