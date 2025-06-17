import requests

REMOVED
REMOVED

# Correct GTFS data endpoint with query parameters
url = f"http://api.tfwm.org.uk/gtfs/tfwm_gtfs.zip?app_id={APP_ID}&app_key={APP_KEY}"

print("Downloading GTFS data...")

try:
    response = requests.get(url)
    response.raise_for_status()

    with open("tfwm_gtfs.zip", "wb") as f:
        f.write(response.content)

    print("GTFS data downloaded successfully!")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
