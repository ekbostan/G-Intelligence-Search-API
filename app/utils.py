from geopy.distance import geodesic
from pykml import parser
import hashlib
import json

# In-memory cache
cache = {}

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

def find_nearest_station(location, stations):
    # Create a unique key for the location
    location_key = hashlib.md5(json.dumps(location).encode()).hexdigest()

    # Check the in-memory cache
    if location_key in cache:
        return cache[location_key]

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

    # Cache the result
    cache[location_key] = result

    return result
