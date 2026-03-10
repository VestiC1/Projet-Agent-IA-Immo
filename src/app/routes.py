from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import onnxruntime as rt
from config import DEPLOYED_MODEL_PATH
from src.utils.geo import validate_and_geocode_address
import numpy as np
import pandas as pd
import pickle
from src.app.monitoring.prometheus_metrics import track_inference_time
import time

router = APIRouter()
templates = Jinja2Templates(directory="src/app/templates")

#session = rt.InferenceSession(str(DEPLOYED_MODEL_PATH))
#input_names = session.get_inputs()

with open("model/deploy/best_model3.pkl", "rb") as f:
    pipeline = pickle.load(f)


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
    # Prepare template context
    # Server-side address validation
    is_valid, geocode_data = validate_and_geocode_address(address)
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Adresse introuvable. Veuillez vérifier l'adresse saisie."
        )
    
    # Use validated data
    validated_address = geocode_data['address']
    validated_lat = geocode_data['latitude']
    validated_lon = geocode_data['longitude']
    
    # Prepare for ML model
    model_input = {
        'Type local': [type_local.title()],
        'latitude': [validated_lat],
        'longitude': [validated_lon],
        'Surface habitable': [surface_habitable],
        'Nombre pieces principales': [nombre_pieces],
        'Surface terrain': [surface_terrain],
        'Type de voie': ['RUE'],
        'densite': [1200]
    }
    inference_start=time.time()
    prediction = np.exp(pipeline.predict(pd.DataFrame(model_input, index=[0]))[0])
    inference_time=time.time()-inference_start
    track_inference_time(inference_time*1000)
    print(prediction)
    
    # TODO: Call your ML model
    # from your_model import predict_price
    # prediction = predict_price(model_input)
    

    confidence_margin = int(prediction * 0.05)
    
    # Prepare template context
    context = {
        "request": request,
        "input": {
            "type": type_local,
            "address": validated_address,
            "surface_habitable": surface_habitable,
            "nombre_pieces": nombre_pieces,
            "surface_terrain": surface_terrain
        },
        "coordinates": {
            "latitude": validated_lat,
            "longitude": validated_lon,
            "commune": geocode_data.get('citycode')
        },
        "estimation": {
            "price": prediction,
            "price_per_m2": int(prediction / surface_habitable),
            "confidence_interval": {
                "min": prediction - confidence_margin,
                "max": prediction + confidence_margin
            },
            "confidence_level": "high" if geocode_data.get('type') == "housenumber" else "medium"
        },
        "metadata": {
            "address_score": geocode_data['score'],
            "address_type": geocode_data.get('type')
        }
    }
    return templates.TemplateResponse("prediction.html", context)