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
       -H "X-API-KEY: [TEST_API_KEY]" \
       -d '{
         "latitude": 40.7128,
         "longitude": -74.0060,
         "include_directions": true
       }'
   ```

## Answering the Questions

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
      - Assuming that 90% of API calls are expected during peak hours (6-9 AM and 4-7 PM), caching helps reduce costs during these periods, potentially cutting costs by half or more.
      - For locations far from the service area grid (defined by the furthest stations), the API will not request directions as walking distances over 100 miles are impractical.

  - **Rate Limiting**: Throttling requests to 10 to prevent abuse and manage API costs effectively.

  - **Load Balancing**:

  - **Assumptions**:
    - We anticipate around 3 million requests, with 90% occurring during peak hours.
    - This is roughly 2.7 million requests during peak hours.
    - Each peak hour (3 hours in the morning and 3 hours in the evening) can have approximately 1.35 million requests.

- **Calculating Users**:

  - Assuming each individual makes about 5 requests during their session:

  ```
  Total Users = 3,000,000 / 5 which is approx 600,000 users/day
  ```

- **Instance Handling Capacity**:
  - A t3.micro instance can handle around 200-300 concurrent users.
  - **Peak Requests (90%)**:
    ```
    Peak Requests = 3,000,000 * 0.9 = 2,700,000 requests during peak hours
    ```
  - **Concurrent Users at Peak (estimated)**:
    ```
    Concurrent Users = 2,700,000 peak requests / (3 * 60 * 60 seconds) = approx 250 users at peak per second
    ```
  - **Required Instances**:
    ```
    Required Instances = 250 peak users per second / 250 concurrent users per instance = approx 1 to 2 t3.micro instances needed during peak hours, preferably 2
    ```

### Cost Calculation:

- Each t3.micro instance costs approximately $0.0104 per hour.
- During peak hours (6 hours a day), the cost per instance would be:
  ```
  Daily Hour Cost per Instance = 0.0104 * 6 = 0.0624 USD per instance per day
  ```
- With 2 instances during peak hours:
  ```
  Total Daily Peak Hour Cost = 0.0624 * 2 = 0.1248 USD per day
  ```
- Over a month (30 days), the peak hour cost would be:
  ```
  Monthly Peak Hour Cost = 0.1248 * 30 = 3.744 USD
  ```
- **Monitoring**:
  I've also implemented a simple metric system that tracks cache hits, misses, and API calls. This allows for testing and analyzing the effectiveness of the current caching strategy. By reviewing the ratio of cache hits to misses and the overall API call volume, we can identify opportunities for further optimizations in our caching strategy.

### 5. Global Sensible Responses

- **Implementation**: The API considers outliers (northernmost, southernmost, etc.) and determines if the request is within the service area (SEPTA or DC Metro). If not, it returns a message indicating that the area is too far away to get walking directions.

### 6. Scalability for Millions of Requests

- **Implementation**:
  - **Caching and Database**: Used distributed cache to handle high traffic and prevent multiple searches of the same location.
  - **Load Balancing**: Ideally implement load balancing stratgey mentioned above.
  - **Asynchronous Processing**: Utilized FastAPI’s asynchronous capabilities to handle multiple requests effectively.

### 7. Protecting Against Malicious Users

- **Implementation**:
  - **Rate Limiting**: Limits how many requests each user or IP can make to stop overuse.
  - **API Key Authentication**: Makes sure only people with a valid key can use the API.
  - **Input Validation**: Cleans and checks user inputs to prevent harmful data from getting through.
  - **Logging and Monitoring**: Tracks how the API is being used to catch any unusual activity.
  - **AWS Shield**: Provides DDoS protection to safeguard the API.

# Production Build Overview

For the purposes of this application and given the limit, I used an AWS EC2 `t2.micro` free tier instance with Docker and Docker Swarm. It provides a scalable, lightweight infrastructure for deploying and managing the API.

## Infrastructure Details

- **Instance Type**: AWS EC2 `t2.micro`
- **Orchestration**: Docker Swarm
- **Containerization**: Docker
- **Operating System**: Amazon Linux 2

## Deployment Design

- **Infrastructure**:
  - AWS EC2 `t2.micro`
  - Amazon Linux 2
  - Docker & Docker Swarm
- **Load Balancing**:
  - Managed by Docker Swarm for even distribution across containers.
- **Caching**:
  - Implemented using Memcached to reduce API load.
- **Rate Limiting**:
  - Limits requests to prevent abuse.
- **Environment Variables**:
  - Managed securely to protect sensitive data using GitHub Secrets for CI/CD pipeline.
- **Monitoring**:
  - Logs and metrics collected for usage and performance analysis.
- **CI/CD Pipeline**:
  - A GitHub Actions pipeline automates the build, test, and deployment processes, ensuring continuous integration and delivery. The pipeline securely manages environment variables and automates the deployment to the AWS EC2 instance.


### Testing the Production Build

- **API Endpoint**: Test with `curl`:

  ```bash
  curl -X POST http://3.86.237.39:8000/nearest_station \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: [TEST_API_KEY]" \
  -d '{
    "latitude": 38.826454124031571,
    "longitude": -76.911466463474113,
    "include_directions": true
  }'
  ```
![Untitled Diagram drawio (2)](https://github.com/user-attachments/assets/bdcb6224-52d4-4338-b2c6-8587b629b457)


  
