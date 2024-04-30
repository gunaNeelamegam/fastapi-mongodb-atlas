from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from .settings import settings
from utils import log
from fastapi.exceptions import HTTPException
from models import UsersModel
import asyncio
setting = settings()
console = log()
client = AsyncIOMotorClient(setting.mongodb_atlas_uri)

def db_configure():
    # which will uses the running event loop
    user_model_task = asyncio.create_task(set_db_model_config(), name= "USER MODEL CONFIGURE")
    user_model_task.add_done_callback(lambda *args: print("USER MODEL CONFIGURE SUCCESSFULLY"))

async def set_db_model_config():
    await connection.configure_database([UsersModel])

def get_connection():
    """
    Yielding the DB connection instance 
    """
    try:
        engine = AIOEngine(client= client, database= setting.db_name)
        db_configure() #configure the user model
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