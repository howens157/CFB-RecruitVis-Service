from fastapi import FastAPI
from google.cloud import secretmanager
from pydantic import BaseModel
import collections
import cfbd
import os
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from contextlib import asynccontextmanager
from typing import AsyncIterator

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

@app.get("/teams")
@cache(namespace="cfbd_calls", expire=86400)
async def teams():
    teams_api = cfbd.TeamsApi(api_config)
    teams = teams_api.get_fbs_teams()
    response = [school.school for school in teams]
    return response

class RecruitsFilter(BaseModel):
    schoolName: str
    yearStart: int
    yearEnd: int

@cache(namespace="cfbd_calls", expire=84600)
async def recruitsByTeamByYear(schoolName, year):
    recruits_api = cfbd.RecruitingApi(api_config)
    recruitsResponse = recruits_api.get_recruiting_players(year=year, team=schoolName)
    result = []
    for recruit in recruitsResponse:
        if recruit.country == "USA":
            result.append(recruit.state_province)
    return result

@app.get("/recruits")
async def recruitsByTeam(recruitsFilter: RecruitsFilter):
    stateCounts = collections.Counter()
    for year in range(recruitsFilter.yearStart, recruitsFilter.yearEnd + 1):
        currYearRecruits = await recruitsByTeamByYear(recruitsFilter.schoolName, year)
        for state in currYearRecruits:
            stateCounts[state] += 1
    return [{"state_name": key, "count": stateCounts[key]} for key in stateCounts]

@app.get("/clearCache")
async def clearCache():
    return await FastAPICache.clear(namespace="cfbd_calls")
    