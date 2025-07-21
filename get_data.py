from google.transit import gtfs_realtime_pb2
import requests
import csv
from geopy.distance import distance
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="keys.env")

APP_ID = os.getenv("APP_ID")
APP_KEY = os.getenv("APP_KEY")

ROUTES_FILE = "tfwm_gtfs/routes.txt"
STOPS_FILE = "tfwm_gtfs/stops.txt"
STOP_TIMES_FILE = "tfwm_gtfs/stop_times.txt"

positions_url = f"http://api.tfwm.org.uk/gtfs/vehicle_positions?app_id={APP_ID}&app_key={APP_KEY}"

print("Fetching live vehicle positions...")

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

# Route input and lookup
route_input = input("Enter the route to check for live buses: ").strip()

route_ids = set()
with open(ROUTES_FILE, mode="r", newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        route_id, _, route_short_name = row[0], row[1], row[2]
        if route_short_name.strip() == route_input:
            route_ids.add(route_id)

if not route_ids:
    print(f"No matching route_ids found for route '{route_input}' in routes.txt.")
    exit()
    
print("Route IDs found:", route_ids)

found = False

for entity in feed.entity:
    if entity.HasField("vehicle"):
        route_id = entity.vehicle.trip.route_id
        trip_id = entity.vehicle.trip.trip_id
        if route_id in route_ids:
            position = entity.vehicle.position
            stop_name = find_closest_stop(trip_id, position.latitude, position.longitude)
            print(f"Bus route: {route_input}")
            print(f"Bus ID: {entity.id}")
            print(f"Route ID: {route_id}")
            print(f"Latitude: {position.latitude}")
            print(f"Longitude: {position.longitude}")
            if stop_name:
                print(f"Current Stop: {stop_name}")
            else:
                print("Current Stop: Unknown (not near any known stop)")
            print("-" * 30)
            found = True

if not found:
    print(f"No live buses found for route {route_input}.")
