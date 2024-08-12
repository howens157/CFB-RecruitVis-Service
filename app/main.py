from fastapi import FastAPI, HTTPException
import os
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi.middleware.cors import CORSMiddleware
from psycopg2 import pool
import psycopg2.extras


# Global variable for connection pool
connection_pool = None

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global connection_pool
    # Initialize the connection pool
    connection_string = os.getenv('CFB_DB_URL')
    connection_pool = pool.SimpleConnectionPool(
        1,  # Minimum number of connections in the pool
        10,  # Maximum number of connections in the pool
        connection_string
    )
    
    if connection_pool:
        print("Connection pool created successfully")
    FastAPICache.init(InMemoryBackend())
    yield

    # Close the connection pool when the application shuts down
    connection_pool.closeall()
    print("Connection pool closed")

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

def get_db_connection():
    global connection_pool
    conn = connection_pool.getconn()
    if not conn:
        raise HTTPException(status_code=500, detail="Failed to get a connection from the pool")
    return conn

@app.get("/teams")
@cache(namespace="cfb_api", expire=86400)
async def teams():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # Query the database
        cur.execute("SELECT name FROM teams")
        teams = cur.fetchall()
        print(teams)
        # Transform the result into a list of team names
        response = [team['name'] for team in teams]
        return response
    finally:
        cur.close()
        connection_pool.putconn(conn)

async def recruitsByTeamByYear(schoolName, yearStart, yearEnd):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        recruit_query = '''
        select state "state_name", count(*) 
        from recruits 
        where 
            team = (select id from teams where name = %s) 
            and year >= %s 
            and year <= %s 
            and state in ('AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'IA',
                'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO',
                'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK',
                'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI',
                'WV', 'WY','DC')
        group by state 
        order by count desc
        '''
        # Query the database
        cur.execute(recruit_query, (schoolName, yearStart, yearEnd))
        recruitStateCounts = cur.fetchall()
        # Transform the result into a list of team names
        response = [{
            'state_name': state['state_name'],
            'count': state['count']
        } for state in recruitStateCounts]
        return response
    finally:
        cur.close()
        connection_pool.putconn(conn)

@cache(namespace="cfb_api", expire=84600)
async def getSchoolInfo(schoolName):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        team_query = '''
        select latitude "lat", longitude "lng", logolink "logo", color, alt_color
        from teams
        where name = %s;
        '''
        # Query the database
        cur.execute(team_query, (schoolName,))
        teamInfo = cur.fetchone()
        # Transform the result into a list of team names
        result = {}
        result['lat'] = teamInfo['lat']
        result['lng'] = teamInfo['lng']
        result['logo'] = teamInfo['logo']
        result['color'] = teamInfo['color']
        result['alt_color'] = teamInfo['alt_color']
        return result
    finally:
        cur.close()
        connection_pool.putconn(conn)

@app.get("/recruits")
async def recruitsByTeam(schoolName: str, yearStart: int, yearEnd: int):
    schoolInfo = await getSchoolInfo(schoolName)
    stateCounts = await recruitsByTeamByYear(schoolName, yearStart, yearEnd)

    schoolInfo['playerData'] = stateCounts
    return schoolInfo

@app.get("/clearCache")
async def clearCache():
    return await FastAPICache.clear(namespace="cfb_api")
    