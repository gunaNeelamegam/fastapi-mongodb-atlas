from fastapi import APIRouter, Depends, Request,Response, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm 
from schemas.auth import SignUp, BareResponse, SignUpResponse
from config.dbconnection import connections
from middlewares import current_user
from odmantic import AIOEngine
from controllers import users
from models import UsersModel
from typing import Annotated

# from jwt.exceptions import ExpiredSignatureError


auth_router = APIRouter(prefix="/auth", tags= ["Authentication"])

@auth_router.post("/register", response_model= SignUpResponse)
async def register(request:Request,
                   user_details: SignUp,
                   connection: AIOEngine = Depends(connections)):
    return await users.register(request, user_details, connection)

@auth_router.post("/login", response_model = SignUpResponse)
async def login(response : Response, info: OAuth2PasswordRequestForm = Depends(),
                 connection: AIOEngine = Depends(connections)):
    login_info = await users.login(response , info, connection)
    return login_info

@auth_router.get("/logout", response_model= BareResponse)
async def logout(user: Annotated[UsersModel, Depends(current_user)], connection: Annotated[AIOEngine,Depends(connections)]):
    return await users.logout(user, connection)

