import json
from geopy.distance import geodesic
from pykml import parser

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
    except Exception as e:
        print(f"Error loading KML data: {e}")
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
    except Exception as e:
        print(f"Error loading GeoJSON data: {e}")
    return stations

def find_outermost_stations(stations):
    northernmost = max(stations, key=lambda s: s['latitude'])
    southernmost = min(stations, key=lambda s: s['latitude'])
    easternmost = max(stations, key=lambda s: s['longitude'])
    westernmost = min(stations, key=lambda s: s['longitude'])
    
    return {
        "northernmost": northernmost,
        "southernmost": southernmost,
        "easternmost": easternmost,
        "westernmost": westernmost
    }

def save_outliers_to_json(file_path, data):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Outermost stations have been written to '{file_path}'.")
    except Exception as e:
        print(f"Error writing to file {file_path}: {e}")

def main():
    septa_stations = load_kml_data('../SEPTARegionalRailStations2016/doc.kml')
    dc_metro_stations = load_geojson_data('Metro_Stations_Regional.geojson')

    septa_outermost_stations = find_outermost_stations(septa_stations)
    dc_metro_outermost_stations = find_outermost_stations(dc_metro_stations)

    save_outliers_to_json('septa_outermost_stations.json', septa_outermost_stations)
    save_outliers_to_json('dc_metro_outermost_stations.json', dc_metro_outermost_stations)

if __name__ == "__main__":
    main()
