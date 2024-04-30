from gridfs import GridFS
from config.dbconnection import connections
from odmantic import ObjectId

def get_user_uploads():
    engine = connections()
    if engine.database.delegate is not None:
        grid = GridFS(engine.database.delegate, collection="users_storage")
        while True:
            yield grid

uploader = get_user_uploads()
user_storage = next(uploader)


async def upload(filename: str, data: bytes | str, mime_type: str = "image/png") -> ObjectId:
    if isinstance(data, str):
        data = data.encode()
        
    id = user_storage.put(data ,filename = filename, mime_type = mime_type)
    if isinstance(id, ObjectId):
        return id
    else:
        return ObjectId(id)

__annotations__ = ("upload", "user_storage")