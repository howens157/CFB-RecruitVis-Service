from fastapi import FastAPI
import cfbd

configuration = cfbd.Configuration()
configuration.api_key['Authorization'] = '+x74G37Yy75USCWjzTnxnEnDeJiuU4P1RrIlY1flnOfa5l8h3ZfKM8oenHJt44TE'
configuration.api_key_prefix['Authorization'] = 'Bearer'
api_config = cfbd.ApiClient(configuration)

app = FastAPI()

@app.get("/teams")
async def root():
    teams_api = cfbd.TeamsApi(api_config)
    teams = teams_api.get_fbs_teams()
    response = [{'name': school.school, 'lat': school.location.latitude, 'lng': school.location.longitude} for school in teams]
    return response