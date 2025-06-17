from google.transit import gtfs_realtime_pb2
import requests
import csv
from geopy.distance import distance


REMOVED
REMOVED

ROUTES_FILE = "tfwm_gtfs/routes.txt"

url = f"http://api.tfwm.org.uk/gtfs/vehicle_positions?app_id={APP_ID}&app_key={APP_KEY}"

print("Fetching live vehicle positions...")

response = requests.get(url)
response.raise_for_status()

feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(response.content)

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



found = False

for entity in feed.entity:
    if entity.HasField("vehicle"):
        route_id = entity.vehicle.trip.route_id
        if route_id in route_ids:
            position = entity.vehicle.position
            print(f"Bus ID: {entity.id}")
            print(f"Route ID: {route_id}")
            print(f"Latitude: {position.latitude}")
            print(f"Longitude: {position.longitude}")
            print(f"Speed: {position.speed} m/s")
            print("-" * 30)
            found = True

if not found:
    print("No live buses found for route 4.")
