from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import bmemcached
from dotenv import load_dotenv
import os
import json
import hashlib
from utils import find_nearest_station, load_kml_data, get_google_maps_directions
from starlette.concurrency import run_in_threadpool
from security import authenticate, SecurityHeadersMiddleware
from models import LocationRequest
import logging
from cache import memcached_client
import uvicorn

load_dotenv()

# Load KML data
stations = load_kml_data('../SEPTARegionalRailStations2016/doc.kml')


app = FastAPI()

logging.basicConfig(level=logging.INFO)
app.state.memcached_client = memcached_client


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(SecurityHeadersMiddleware)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger("uvicorn.access")
    logger.info(f"Request: {request.method} {request.url} Headers: {request.headers}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Endpoint to find the nearest station
@app.post("/nearest_station", dependencies=[Depends(authenticate)])
async def nearest_station(request: LocationRequest):
    location = (request.latitude, request.longitude)
    
    location_key = hashlib.sha256(json.dumps(location).encode('utf-8')).hexdigest()

    cached_result = await run_in_threadpool(app.state.memcached_client.get, location_key)
    if cached_result:
        nearest_station_geojson = json.loads(cached_result)
    else:
        nearest_station_geojson = find_nearest_station(location, stations, app.state.memcached_client)

        if nearest_station_geojson is None:
            raise HTTPException(status_code=429, detail="Another process is handling this request, please try again shortly.")

        # Cache the result using `run_in_threadpool`
        await run_in_threadpool(app.state.memcached_client.set, location_key, json.dumps(nearest_station_geojson), 00)

    response_data = {
        "status": "success",
        "nearest_station": nearest_station_geojson,
        "directions": None
    }

    if request.include_directions:
        directions = await run_in_threadpool(get_google_maps_directions, location, nearest_station_geojson)
        response_data["directions"] = directions

    return JSONResponse(content=response_data)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
