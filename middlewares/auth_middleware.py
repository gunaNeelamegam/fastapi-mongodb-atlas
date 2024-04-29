from fastapi import Request, Depends, status
from fastapi.exceptions import HTTPException
from models import UsersModel
from typing import Annotated
from jwt import decode
from odmantic import AIOEngine, ObjectId
from config.settings import Settings, settings
from config.dbconnection import connections

async def current_user(request: Request,
                        setting: Annotated[Settings, Depends(settings)], 
                        connection: Annotated[AIOEngine, Depends(connections)]):
    token = request.cookies.get("access_token", None)
    # extracting only the token
    if token is None:
        token = request.headers.get("Authorization", None)
        if token:
            token = token.replace("Bearer ","")

    if token:
        payload: dict = decode(token, setting.access_token_secret_key, algorithms= [setting.algorithm])
        user_id = payload.get("id", None)
        if user_id:
            user = await connection.find_one(UsersModel, UsersModel.id == ObjectId(user_id))
            if user:
                return user
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail= {
            "message": "Token Expired Please revoke refresh token",
            "status": False
        })
    else:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail= {
            "message": "Token Expired Please revoke refresh token",
            "status": False
        })
    