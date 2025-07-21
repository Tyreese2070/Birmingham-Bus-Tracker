from fastapi import FastAPI
#import get_data

app = FastAPI()

@app.get("/route/{route_name}/vehichles")
async def get_live_vehichles_for_route():
    """
    Returns positions of all vehichles on a given route.
    """
    return {""}

@app.get("/routes/")
async def get_all_routes():
    """
    Returns a list of all routes.
    """
    return {""}

@app.get("/routes/{route_name}/stops")
async def get_all_routes():
    """
    Returns a list of all stops for a given route.
    """
    return {""}