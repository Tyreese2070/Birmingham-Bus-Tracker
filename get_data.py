from google.transit import gtfs_realtime_pb2
import requests
import csv
from geopy.distance import distance
from dotenv import load_dotenv
import os
import subprocess
import zipfile

load_dotenv(dotenv_path="keys.env")

APP_ID = os.getenv("APP_ID")
APP_KEY = os.getenv("APP_KEY")

GTFS_DIR = 'tfwm_gtfs'
ZIP_FILENAME = 'tfwm_gtfs.zip'

# Check if the GTFS directory exists, download if it doesn't.
if not os.path.isdir(GTFS_DIR):
    print(f"Directory '{GTFS_DIR}' not found. Running download script...")
    try:
        subprocess.run(['python', 'tfwm_gtfs_download.py'], check=True)
        print("Download script finished successfully.")
        
        print(f"Unzipping '{ZIP_FILENAME}'...")
        with zipfile.ZipFile(ZIP_FILENAME, 'r') as zip_ref:
            zip_ref.extractall(GTFS_DIR)
        print("Unzip complete.")
        
        print(f"Removing '{ZIP_FILENAME}'...")
        os.remove(ZIP_FILENAME)
        
    except FileNotFoundError:
        print("Error: 'tfwm_gtfs_download.py' not found. Please ensure it is in the same directory.")
        exit()
    except subprocess.CalledProcessError:
        print("Error: The download script failed.")
        exit()
else:
    print(f"Directory '{GTFS_DIR}' found. Skipping download.")

ROUTES_FILE = "tfwm_gtfs/routes.txt"
STOPS_FILE = "tfwm_gtfs/stops.txt"
STOP_TIMES_FILE = "tfwm_gtfs/stop_times.txt"
TRIPS_FILE = "tfwm_gtfs/trips.txt"

positions_url = f"http://api.tfwm.org.uk/gtfs/vehicle_positions?app_id={APP_ID}&app_key={APP_KEY}"

response = requests.get(positions_url)
response.raise_for_status()

feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(response.content)

# Load stops.txt
stops = {}
with open(STOPS_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        stops[row["stop_id"]] = {
            "name": row["stop_name"],
            "lat": float(row["stop_lat"]),
            "lon": float(row["stop_lon"])
        }

# Load stop_times.txt
trip_stop_sequences = {}
with open(STOP_TIMES_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        trip_id = row["trip_id"]
        stop_id = row["stop_id"]
        if trip_id not in trip_stop_sequences:
            trip_stop_sequences[trip_id] = []
        trip_stop_sequences[trip_id].append(stop_id)

def find_closest_stop(trip_id, vehicle_lat, vehicle_lon):
    if trip_id not in trip_stop_sequences:
        return None

    closest_stop = None
    min_dist = float("inf")

    for stop_id in trip_stop_sequences[trip_id]:
        if stop_id not in stops:
            continue
        stop_info = stops[stop_id]
        stop_coords = (stop_info["lat"], stop_info["lon"])
        vehicle_coords = (vehicle_lat, vehicle_lon)
        dist = distance(stop_coords, vehicle_coords).meters
        if dist < min_dist:
            min_dist = dist
            closest_stop = stop_info["name"]

    return closest_stop if min_dist <= 100 else None  # only consider stops within 100m

def all_routes():
    """
    Returns a list of all routes.
    """
    routes = []
    with open(ROUTES_FILE, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            routes.append({
                "route_name": row["route_short_name"],
            })
    return routes

def all_stops_for_route(route_name):
    """
    Returns a list of all stops for a given route (by route_short_name).
    """
    # 1. Find route_id from route_short_name
    route_ids = set()
    with open(ROUTES_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["route_short_name"] == route_name:
                route_ids.add(row["route_id"])

    if not route_ids:
        return []

    # 2. Get trip_ids from trips.txt
    trip_ids = set()
    with open(TRIPS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["route_id"] in route_ids:
                trip_ids.add(row["trip_id"])

    # 3. Get stop_ids from stop_times.txt
    stop_ids = set()
    with open(STOP_TIMES_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["trip_id"] in trip_ids:
                stop_ids.add(row["stop_id"])

    # 4. Map stop_id to stop_name from stops.txt
    stops_for_route = []
    with open(STOPS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["stop_id"] in stop_ids:
                stops_for_route.append({
                    "stop_name": row["stop_name"]
                })

    return stops_for_route

# May change to get an accurate current stop.
def live_vehichles_positions(route_name):
    """
    Returns positions of all vehicles on a given route.
    """
    vehicles = []
    for entity in feed.entity:
        if entity.HasField("vehicle"):
            route_id = entity.vehicle.trip.route_id
            if route_id == route_name:
                position = entity.vehicle.position
                stop_name = find_closest_stop(entity.vehicle.trip.trip_id, position.latitude, position.longitude)
                vehicles.append({
                    "vehicle_id": entity.id,
                    "route_id": route_id,
                    "latitude": position.latitude,
                    "longitude": position.longitude,
                    "current_stop": stop_name if stop_name else "Unknown"
                })
    return vehicles