from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from .settings import settings
from utils import log
from fastapi.exceptions import HTTPException

setting = settings()
console = log()
client = AsyncIOMotorClient(setting.mongodb_atlas_uri)

def get_connection():
    """
    Yielding the DB connection instance 
    """
    try:
        engine = AIOEngine(client= client, database= setting.db_name)
        while True:
            yield engine
    except Exception as e:
        console.print(e.args)
        raise HTTPException(status_code=  500, detail= {
            "message": "DB Connection Failure"
        })
    
# get the db connection as the dependency injection mechanism
engine_connection_gena = get_connection()
connection = next(engine_connection_gena)

def connections():
    """ return's the db connection instance
    """
    return connection

__annotations__ = ("connections")