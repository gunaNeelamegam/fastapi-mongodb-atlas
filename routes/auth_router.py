from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm 
from schemas.auth import SignUp, BareResponse, SignUpResponse
from config.dbconnection import connections
from middlewares import current_user
from odmantic import AIOEngine, exceptions
from controllers import users
from models import UsersModel
from typing import Annotated
from starlette.config import Config
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from authlib.integrations.starlette_client import OAuth, OAuthError
from os import path as _path
from pathlib import Path
from utils.uploads import upload
from httpx import AsyncClient
from core.core_types import AvailableLoginTypes
from controllers import users

config_path = _path.join(Path(__file__).parent.parent , "config/.env")

# Using OAuth Providers login
config = Config(config_path)
oauth = OAuth(config)
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(name = "google", server_metadata_url= CONF_URL, client_kwargs = {
    "scope": "openid email profile"
})

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


@auth_router.get("/google")
async def google_login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@auth_router.get("/google/callback")
async def auth(request: Request, connection: Annotated[AIOEngine, Depends(connections)]):
    user: UsersModel | None = None

    try:
        google_token_info = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        print(error.args, error.description, error.uri, error.error)
        return HTMLResponse(f'<h1>{error.error}</h1>')
    google_user = google_token_info.get('userinfo')
    if email:= google_user.get("email"):
        user = await connection.find_one(UsersModel, UsersModel.email == email)
        if user:
           if user.login_type != AvailableLoginTypes.GOOGLE:
               raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED,
                                    detail = BareResponse(status= False, message= 
                                                          f"""You have previously registered using {user.login_type} 
                                                          .Please use the {user.login_type} login option to access your account.""",)
                                                          .model_dump(),
                                                          )
        else:
            user_name = google_user.get("given_name") or google_user.get("family_name")
            if not user_name:
                user_name = email.split("@")[0]
            if avatar_url:= google_user.get("picture"):
                async with AsyncClient() as client:
                    response = await client.get(avatar_url)
                    mimetype = response.headers.get("Content-Type")
                    extension = mimetype.split(".")[-1]
                    avatar_id = await upload(data= response.content, mime_type =  mimetype, 
                           filename = f"{user_name}.{extension}")
                    
            user = UsersModel(username= user_name,
                              is_email_verified= True,
                             email= email,
                             avatar = avatar_id, 
                              password = google_user.get("sub"),
                              login_type= AvailableLoginTypes.GOOGLE)
            
            user.hash_password()
            try:
                await connection.save(user)
            except exceptions.DuplicateKeyError as e:
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail= BareResponse(
                        status=False, 
                        message = "User Name or Email Already Exists"
                    ).model_dump()
                )
    return await users.handle_social_login(user)