from fastapi import FastAPI
import cfbd
from google.cloud import secretmanager
import os

def get_api_key():
    envApiKey = os.environ.get("CFBD_API_KEY")
    print(f'envApiKey {envApiKey}')
    if envApiKey: return envApiKey
    client = secretmanager.SecretManagerServiceClient()
    secret_name = "projects/your-project-id/secrets/your-secret-name/versions/latest"
    response = client.access_secret_version(name=secret_name)
    return response.payload.data.decode('UTF-8')

configuration = cfbd.Configuration()
CFBD_api_key = get_api_key()
print(CFBD_api_key)
configuration.api_key['Authorization'] = CFBD_api_key
configuration.api_key_prefix['Authorization'] = 'Bearer'
api_config = cfbd.ApiClient(configuration)

app = FastAPI()

@app.get("/teams")
async def root():
    teams_api = cfbd.TeamsApi(api_config)
    teams = teams_api.get_fbs_teams()
    response = [{'name': school.school, 'lat': school.location.latitude, 'lng': school.location.longitude} for school in teams]
    return response