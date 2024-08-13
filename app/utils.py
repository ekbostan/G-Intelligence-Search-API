from geopy.distance import geodesic
from pykml import parser
import hashlib
import json
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def load_kml_data(filepath):
    stations = []
    with open(filepath) as f:
        doc = parser.parse(f).getroot()
        for placemark in doc.Document.Folder.Placemark:
            name = placemark.name.text
            coords = placemark.Point.coordinates.text.strip().split(',')
            stations.append({
                "name": name,
                "longitude": float(coords[0]),
                "latitude": float(coords[1])
            })
    return stations

def find_nearest_station(location, stations, memcached_client):
    location_key = hashlib.md5(json.dumps(location).encode()).hexdigest()
    lock_key = f"lock:{location_key}"

    # Acquire a lock
    if memcached_client.add(lock_key, "locked", time=10):
        try:
            # Check the cache
            cached_result = memcached_client.get(location_key)
            if cached_result:
                return json.loads(cached_result)

            # Calculate nearest station
            nearest_station = None
            min_distance = float('inf')
            for station in stations:
                station_location = (station['latitude'], station['longitude'])
                distance = geodesic(location, station_location).miles
                if distance < min_distance:
                    min_distance = distance
                    nearest_station = station

            result = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [nearest_station['longitude'], nearest_station['latitude']]
                },
                "properties": {
                    "name": nearest_station['name'],
                    "distance_miles": min_distance
                }
            }
            #Serve the requested data from the cache reducing the load on the server
            memcached_client.set(location_key, json.dumps(result), time=3600)

            return result
        finally:

            memcached_client.delete(lock_key)
    else:
        return None


def get_google_maps_directions(start, end, mode='walking'):
    """
    Get directions from Google Maps Directions API.
    
    :param start: Tuple (latitude, longitude) of the start location.
    :param end: Tuple (latitude, longitude) of the end location.
    :param mode: Mode of transportation, e.g., 'walking', 'driving', 'transit'.
    :return: JSON response from Google Maps API with directions.
    """
    start_coords = f"{start[0]},{start[1]}"
    end_coords = f"{end['geometry']['coordinates'][1]},{end['geometry']['coordinates'][0]}"
    
    directions_url = (
        f"https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={start_coords}"
        f"&destination={end_coords}"
        f"&mode={mode}"
        f"&key={os.getenv('GOOGLE_MAPS_API_KEY')}"
    )
    
    response = requests.get(directions_url)
    return response.json()
