from fastapi import FastAPI
from google.cloud import secretmanager
import collections
import cfbd
import os
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi.middleware.cors import CORSMiddleware


gcloudProjectId = 'weighty-psyche-431000-f6'
gcloudSecretName = 'CFBD_api_key'

def get_api_key():
    envApiKey = os.environ.get("CFBD_API_KEY")
    if envApiKey: return envApiKey
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f'projects/{gcloudProjectId}/secrets/{gcloudSecretName}/versions/latest'
    response = client.access_secret_version(name=secret_name)
    return response.payload.data.decode('UTF-8')

configuration = cfbd.Configuration()
CFBD_api_key = get_api_key()
configuration.api_key['Authorization'] = CFBD_api_key
configuration.api_key_prefix['Authorization'] = 'Bearer'
api_config = cfbd.ApiClient(configuration)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(InMemoryBackend())
    yield

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "https://cfb-recruitvis-ui-52q4kjb4da-uk.a.run.app",
    "https://cfbrecruits.com",
    "https://www.cfbrecruits.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/teams")
@cache(namespace="cfbd_calls", expire=86400)
async def teams():
    teams_api = cfbd.TeamsApi(api_config)
    teams = teams_api.get_fbs_teams()
    response = [school.school for school in teams]
    return response

allowedStates = set([
    "AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "IA",
    "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO",
    "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI",
    "WV", "WY","DC",
])

@cache(namespace="cfbd_calls", expire=84600)
async def recruitsByTeamByYear(schoolName, year):
    recruits_api = cfbd.RecruitingApi(api_config)
    recruitsResponse = recruits_api.get_recruiting_players(year=year, team=schoolName)
    result = []
    for recruit in recruitsResponse:
        if recruit.state_province in allowedStates:
            result.append(recruit.state_province)
    return result

@cache(namespace="cfbd_calls", expire=84600)
async def getSchoolInfo(schoolName):
    teams_api = cfbd.TeamsApi(api_config)
    teams = teams_api.get_fbs_teams()
    team = next(team for team in teams if team.school == schoolName)
    result = {}
    result['lat'] = team.location.latitude
    result['lng'] = team.location.longitude
    if len(team.logos) > 0:
        result['logo'] = team.logos[0]
    result['color'] = team.color
    result['alt_color'] = team.alt_color
    return result

@app.get("/recruits")
async def recruitsByTeam(schoolName: str, yearStart: int, yearEnd: int):
    schoolInfo = await getSchoolInfo(schoolName)
    stateCounts = collections.Counter()
    for year in range(yearStart, yearEnd + 1):
        currYearRecruits = await recruitsByTeamByYear(schoolName, year)
        for state in currYearRecruits:
            stateCounts[state] += 1
    
    schoolInfo['playerData'] = [{"state_name": key, "count": stateCounts[key]} for key in stateCounts]
    return schoolInfo

@app.get("/clearCache")
async def clearCache():
    return await FastAPICache.clear(namespace="cfbd_calls")
    