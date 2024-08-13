from fastapi import FastAPI, HTTPException, Depends,status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
import hashlib
from utils import find_nearest_station, get_google_maps_directions, load_all_stations
from starlette.concurrency import run_in_threadpool
from security import authenticate, SecurityHeadersMiddleware
from models import LocationRequest
import logging
from cache import memcached_client
import uvicorn
from middlewares import limit_request_size ,log_requests

load_dotenv()

# Load KML data
try:
    stations = load_all_stations('../SEPTARegionalRailStations2016/doc.kml', '../DCMetroStations/Metro_Stations_Regional.geojson')
except Exception as e:
    logging.error(f"Failed to load station data: {e}")
    stations = []

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
app.middleware("http")(limit_request_size)  
app.middleware("http")(log_requests) 

# Endpoint to find the nearest station
@app.post("/nearest_station", dependencies=[Depends(authenticate)])
async def nearest_station(request: LocationRequest):
    location = (request.latitude, request.longitude)
    
    location_key = hashlib.sha256(json.dumps(location).encode('utf-8')).hexdigest()

    try:
        # Try to fetch the result from the cache
        cached_result = await run_in_threadpool(app.state.memcached_client.get, location_key)
        if cached_result:
            nearest_station_geojson = json.loads(cached_result)
        else:
            # Find the nearest station
            nearest_station_geojson = find_nearest_station(location, stations, app.state.memcached_client)

            if nearest_station_geojson is None:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Another process is handling this request, please try again shortly."
                )

            await run_in_threadpool(
                app.state.memcached_client.set,
                location_key,
                json.dumps(nearest_station_geojson),
                84600
            )

        response_data = {
            "status": "success",
            "nearest_station": nearest_station_geojson,
            "directions": None
        }

        if request.include_directions:
            directions = await run_in_threadpool(get_google_maps_directions, location, nearest_station_geojson)
            response_data["directions"] = directions

        return JSONResponse(content=response_data)

    except Exception as e:
        logging.error(f"Error processing nearest_station request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request."
        )


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
