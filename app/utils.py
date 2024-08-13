from geopy.distance import geodesic
from pykml import parser
import hashlib
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def load_all_stations(septa_kml_path, dc_metro_geojson_path):
    try:
        septa_stations = load_kml_data(septa_kml_path)
        dc_metro_stations = load_geojson_data(dc_metro_geojson_path)
        return septa_stations + dc_metro_stations
    except Exception as e:
        print(f"Error loading stations: {e}")
        return []

def load_kml_data(filepath):
    stations = []
    try:
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
    except FileNotFoundError:
        print(f"Error: KML file not found at {filepath}")
    except Exception as e:
        print(f"Error parsing KML file at {filepath}: {e}")
    return stations

def load_geojson_data(filepath):
    stations = []
    try:
        with open(filepath, 'r') as f:
            geojson = json.load(f)
            for feature in geojson['features']:
                coords = feature['geometry']['coordinates']
                name = feature['properties']['NAME']
                stations.append({
                    "name": name,
                    "longitude": coords[0],
                    "latitude": coords[1]
                })
    except FileNotFoundError:
        print(f"Error: GeoJSON file not found at {filepath}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from GeoJSON file at {filepath}")
    except Exception as e:
        print(f"Error parsing GeoJSON file at {filepath}: {e}")
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
            # Serve the requested data from the cache reducing the load on the server
            memcached_client.set(location_key, json.dumps(result), time=86400)

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

