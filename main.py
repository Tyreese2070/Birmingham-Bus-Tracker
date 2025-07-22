from fastapi import FastAPI
from get_data import all_routes, all_stops_for_route, live_vehicles_positions, setup_data

app = FastAPI()
setup_data()

@app.get("/route/{route_name}/vehicles")
async def get_live_vehicles_for_route(route_name: str):
    """
    Returns positions of all vehicles on a given route.
    """
    return live_vehicles_positions(route_name)

@app.get("/routes/")
async def get_all_routes():
    """
    Returns a list of all routes.
    """
    return all_routes()

@app.get("/routes/{route_name}/stops")
async def get_all_stops_for_route(route_name: str):
    """
    Returns a list of all stops for a given route.
    """
    return all_stops_for_route(route_name)