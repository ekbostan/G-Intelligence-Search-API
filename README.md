# Nearest Train Station API

This API takes a geographical location and finds the nearest SEPTA Regional Rail train station or DC Metro station. It returns the nearest station in GeoJSON format and provides optional walking directions to the station using the Google Maps Directions API: https://developers.google.com/maps/documentation/directions/overview.

## Features

- Finds the nearest train station (SEPTA or DC Metro) based on a given location.
- Returns the nearest location in GeoJSON format.
- Provides optional walking directions to the nearest station using Google Map API.
- Distinguishes between SEPTA and DC Metro stations, ensuring accuracy for each region.

## Setup Instructions

### Prerequisites

- Python 3.7+
- `pip` package manager
- Google Maps API Key

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/nearest-station-api.git
   cd nearest-station-api
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   Create a `.env` file in the root of the project and add your Google Maps API Key:

   ```plaintext
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   ```

5. **Prepare the dataset:**

   - Download the SEPTA dataset from [SEPTA Regional Rail Data](https://drive.google.com/file/d/11ZfHYz3w77-aM4ZQnQIxSSdxcGnWcFjA/view?usp=drive_link) and the DC Metro dataset from [DC Metro Data](https://drive.google.com/file/d/1_Dlbd-5YhivitQ1dLgejW3_RKp0yNS7n/view?usp=drive_link).
   - Place these files in the appropriate directories:
     - SEPTA: `../SEPTARegionalRailStations2016/doc.kml`
     - DC Metro: `../Metro_Stations_Regional.geojson`
   - Generate the outlier stations JSON files by running the appropriate scripts or manually preparing them.

6. **Run the application:**

   ```bash
   uvicorn app:app --reload
   ```

7. **Make API requests:**

   You can make requests to the API using `curl`, Postman, or any HTTP client. Example request:

   ```bash
   curl -X POST http://127.0.0.1:8000/nearest_station \
       -H "Content-Type: application/json" \
       -H "X-API-KEY: test_api_key_1" \
       -d '{
         "latitude": 40.7128,
         "longitude": -74.0060,
         "include_directions": true
       }'
   ```

## Answering the Questions

### 1. Function to Find Nearest SEPTA Station

- **Implementation**: The function uses geospatial data from the SEPTA and DC Metro datasets to find the nearest station and returns the station's details in GeoJSON format.
- **Walking Directions**: The function integrates with Google Maps API to fetch walking directions.

### 2. Expose Function via HTTP API

- **Implementation**: The function is exposed via a FastAPI endpoint, `/nearest_station`. It accepts a POST request with location data (latitude and longitude) and returns the nearest station's details in GeoJSON format.

### 3. Avoid Duplicate Searches

- **Implementation**: The API uses caching with Memcached, utilizing the Redis free tier. Before performing a search, the API checks if the location has been searched recently; if so, it returns the cached result. It also caches directions to the same location to avoid repeated calls to the Google API. Assuming that the bulk of API usage—approximately 90%—will occur during rush hours (6-9 AM and 4-7 PM), caching the results for both directions and searches would significantly improve efficiency.

### 4. Cost-Effective API

- **Considerations**:

  - **Caching**:

    - **Assumptions**:

      - API volume is around 3 million requests per day.
      - Google Maps API charges approximately $0.002 per request.
      - Without caching, the daily cost could be around $6,000.
      - Monthly costs could therefore be $180,000.

    - **Caching Strategy**:
      - By caching results with a 3-decimal point precision (which effectively caches locations within approximately 364 feet), we significantly reduce duplicate requests.
      - Given that 90% of API calls are expected during peak hours (6-9 AM and 4-7 PM), caching helps reduce costs during these periods, potentially cutting costs by half or more.
      - For locations far from the service area grid (defined by the furthest stations), the API will not request directions as walking distances over 100 miles are impractical.

  - **Rate Limiting**: Throttling requests to prevent abuse and manage API costs effectively.

  - **Load Balancing**:

    - **Assumptions**:

      - We anticipate around 3 million requests, with 90% occurring during peak hours.
      - This translates to roughly 2.7 million requests during these periods.
      - Each peak hour (3 hours in the morning and 3 hours in the evening) could see approximately 1.35 million requests.

    - **Calculating Users**:

      - Assuming each individual makes about 5 requests during their session:
      - **Total Users**:
        \[
        \text{Total Users} = \frac{3,000,000 \text{ requests}}{5 \text{ requests/user}} \approx 600,000 \text{ users/day}
        \]

    - **Instance Handling Capacity**:

      - A **t3.medium** instance can handle around 1000-2000 concurrent users.
      - **Peak Requests (90%)**:
        \[
        \text{Peak Requests} = 3,000,000 \times 0.9 = 2,700,000 \text{ requests during peak hours}
        \]
      - **Concurrent Users at Peak (estimated)**:
        \[
        \text{Concurrent Users} = \frac{2,700,000 \text{ peak requests}}{3 \times 60 \times 60 \text{ seconds}} \approx 250 \text{ users at peak per second}
        \]
      - **Required Instances**:
        \[
        \text{Required Instances} = \frac{250 \text{ peak users per second}}{1000 \text{ concurrent users per instance}} \approx 1 \text{ to } 3 \text{ t3.medium instances needed during peak hours}
        \]

    - **Cost Calculation**:
      - Each **t3.medium** instance costs approximately **$0.0416 per hour**.
      - During peak hours (6 hours a day), the cost per instance would be:
        \[
        \text{Daily Peak Hour Cost per Instance} = 0.0416 \times 6 = 0.2496 \text{ USD per instance per day}
        \]
      - With 3 instances during peak hours:
        \[
        \text{Total Daily Peak Hour Cost} = 0.2496 \times 2.5 = 0.624 \text{ USD per day}
        \]
      - Over a month (30 days), the peak hour cost would be:
        \[
        \text{Monthly Peak Hour Cost} = 0.624 \times 30 = 18.72 \text{ USD}
        \]

  - **Monitoring**: I've also implemented a simple metric system that tracks cache hits, misses, and API calls. This system allows for testing and analyzing the effectiveness of the current caching strategy. By reviewing the ratio of cache hits to misses and the overall API call volume, we can identify opportunities to adjust and further optimize caching strategies.

### 5. Global Sensible Responses

- **Implementation**: The API considers extreme outliers (northernmost, southernmost, etc.) and determines if the request is within the service area (SEPTA or DC Metro). If not, it returns a sensible message indicating the location is too far for the service.

### 6. Scalability for Millions of Requests

- **Implementation**:
  - **Caching and Database**: Use a distributed cache and database to handle high traffic.
  - **Load Balancing**: Implement load balancing to distribute requests across multiple instances.
  - **Asynchronous Processing**: Utilize FastAPI’s asynchronous capabilities to handle multiple requests efficiently.

### 7. Protecting Against Malicious Users

- **Implementation**:
  - **Rate Limiting**: Prevents abuse by limiting the number of requests per user/IP.
  - **API Key Authentication**: Ensures only authorized users can access the API.
  - **Input Validation**: Sanitize and validate inputs to prevent injection attacks.
  - **Logging and Monitoring**: Track usage patterns and detect potential attacks in real-time.

### 8. Adding DC Metro and Backward Compatibility

- **Implementation**: The API is designed to handle multiple datasets. Adding DC Metro was done by integrating another dataset while keeping the original SEPTA functionality intact. The service area determination ensures backward compatibility.
