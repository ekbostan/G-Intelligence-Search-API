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

def main():
    septa_stations = load_kml_data('/SEPTARegionalRailStations2016/doc.kml')
    dc_metro_stations = load_geojson_data('Metro_Stations_Regional.geojson')
    all_stations = septa_stations + dc_metro_stations

    outermost_stations = find_outermost_stations(all_stations)

    with open('outermost_stations.json', 'w') as f:
        json.dump(outermost_stations, f, indent=4)
    
    print("Outermost stations have been written to 'outermost_stations.json'.")

if __name__ == "__main__":
    main()
