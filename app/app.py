from flask import Flask, request, jsonify, abort
from flask_inputs import Inputs
from flask_inputs.validators import JsonSchema
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import requests
from utils import find_nearest_station, load_kml_data, get_google_maps_directions
from config import Config

# Load KML data
stations = load_kml_data('../SEPTARegionalRailStations2016/doc.kml')

# Create the Flask application
app = Flask(__name__)
CORS(app)  
app.config.from_object(Config)

# Initialize the limiter
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

# JSON Schema for input validation
request_schema = {
    'type': 'object',
    'properties': {
        'latitude': {'type': 'number'},
        'longitude': {'type': 'number'},
        'include_directions': {'type': 'boolean'},
    },
    'required': ['latitude', 'longitude']
}

class LocationInputs(Inputs):
    json = [JsonSchema(schema=request_schema)]

@app.before_request
def authenticate():
    api_key = request.headers.get('X-API-KEY')
    if api_key not in app.config['VALID_API_KEYS']:
        abort(401, description="Unauthorized: Invalid API Key")

@app.route('/nearest_station', methods=['POST'])
@limiter.limit("10 per minute")
def nearest_station():
    print("Received request at /nearest_station")
    inputs = LocationInputs(request)

    if not inputs.validate():
        return jsonify(success=False, errors=inputs.errors), 400

    data = request.json
    location = (data['latitude'], data['longitude'])

    # Find the nearest station
    nearest_station_geojson = find_nearest_station(location, stations)

    # Initialize response data
    response_data = {
        "status": "success",
        "nearest_station": nearest_station_geojson,
        "directions": None
    }

    if data.get('include_directions', False):
        directions = get_google_maps_directions(location, nearest_station_geojson)
        response_data["directions"] = directions

    return jsonify(response_data), 200


def get_walking_directions(start, end):
    start_coords = f"{start[1]},{start[0]}"
    end_coords = f"{end['geometry']['coordinates'][1]},{end['geometry']['coordinates'][0]}"
    directions_url = f"https://api.mapbox.com/directions/v5/mapbox/walking/{start_coords};{end_coords}?access_token={app.config['MAPBOX_API_KEY']}"
    response = requests.get(directions_url)
    return response.json()

if __name__ == '__main__':
    print("Starting Flask application...")
    app.run(debug=True)


