from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi import APIRouter, Depends, Body
from typing import Annotated, Dict,Any, Set
from config.dbconnection import connections
from odmantic import AIOEngine, Model
from asyncio import create_task, Task
from models import UsersModel
from json import dumps
notification_router = APIRouter(tags= ["Realtime Notification"], prefix="/subscribe")

COLLECTIONS_CLS = {
    "users": UsersModel
}

class CollectionSubScribers:
    collections : Dict[str, Set[WebSocket]] = dict()
    collections_tasks: list[Task]

async def start_collection_watcher(connection: Annotated[AIOEngine, "Odmantic AsyncIO motor engine"], model: Annotated[Model, "Odmantic Model"],
                                    collection_name: str):
   with connection.get_collection(model).watch([
            {
                "$operationType": {
                    "$in": ["insert", "update", "delete","replace"]
                }
            }
        ]) as change_stream:
        for changes in change_stream:
            try:
                for subscribe in CollectionSubScribers.collections.get(collection_name):
                    await subscribe.send_json(dumps(changes))
            except WebSocketDisconnect as disconnect:
                   CollectionSubScribers.collections.get(collection_name).remove(subscribe)

async def stop_notification():
    for running_task in CollectionSubScribers.collections_tasks:
        running_task.cancel()        
    try:
        for running_task in CollectionSubScribers.collections_tasks:
            await running_task
    except Exception as e:
        print("ERROR : ", e.args)
        
async def start_notification(connection =  connections()):
    collection_names = await connection.database.list_collection_names()
    for collection in collection_names:
        model = COLLECTIONS_CLS.get(collection)
        task = create_task(start_collection_watcher(connection, model, collection))        
        CollectionSubScribers.collections_tasks.append(task)

# websocket connection will not be explicity show in swagger docs
@notification_router.websocket("/{collection}")
async def subscribe_users(collection : str , web_socket: WebSocket, connection:Annotated[AIOEngine, Depends(connections)]):
    await web_socket.accept()
    if not collection in CollectionSubScribers.collections.keys():
        CollectionSubScribers.collections[collection] = set()
    CollectionSubScribers.collections[collection].add(web_socket)

