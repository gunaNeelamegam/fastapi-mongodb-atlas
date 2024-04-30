from typing import Annotated
from fastapi import Depends, APIRouter, Request, UploadFile, Body
from odmantic import AIOEngine
from pydantic import EmailStr
from config.dbconnection import connections
from models import UsersModel
from schemas import ChangePassword
from schemas.auth import BareResponse
from  controllers import users
from core import AvailableRoles
from schemas.auth import BareUserModelWithPhoto
from middlewares import current_user as get_current_user

user_router = APIRouter(prefix="/users", tags=["Users"])

@user_router.post("/change-password", response_model = BareResponse)
async def change_password(update_password:ChangePassword,
                        user: Annotated[UsersModel, Depends(get_current_user)],
                        connection: Annotated[AIOEngine, Depends(connections)]):
    return await users.change_current_password(user,update_password, connection) 

@user_router.post("/forget-password", response_model= BareResponse)
async def forget_password(request: Request, email:Annotated[EmailStr, Body(embed= True)], connection: Annotated[AIOEngine, None] = Depends(connections)):
    return await users.forget_password_request(request,  email, connection)

@user_router.post("/reset-password/{reset_token}")
async def reset_password(reset_token: str , new_password: Annotated[str, Body(embed=True)],connection: Annotated[AIOEngine, None] = Depends(connections)):
    return await users.reset_forgetten_password(new_password, reset_token, connection)

@user_router.post("/avatar", response_model= BareResponse)
async def update_avater(photo: UploadFile, 
                        user: Annotated[UsersModel, Depends(get_current_user)] ,
                        connection: Annotated[AIOEngine, Depends(connections)]):
    return await users.update_avatar(user, photo, connection)

@user_router.get("/current-user", response_model= BareUserModelWithPhoto)
async def current_user(connection: Annotated[AIOEngine, Depends(connections)]):
    populated_user = connection.get_collection(UsersModel).aggregate([
    {
        '$lookup': {
            'from': 'users_storage.files', 
            'localField': 'avatar', 
            'foreignField': '_id', 
            'as': 'photos'
        }
    }, {
        '$addFields': {
            'photo': {
                '$first': '$photos'
            }
        }
    }, {
        '$project': {
            'avatar': 0, 
            'photos': 0
        }
    }, {
        '$limit': 1
    }
])
    # use to list method to check if there might have a document
    populated_user = await populated_user.next()
    return populated_user 

@user_router.get("/verify-email/{verification_token}",response_model= BareResponse)
async def verify_email(verification_token: str , connection: Annotated[AIOEngine, Depends(connections)]):
   return await users.email_verification(verification_token, connection)

@user_router.post("/assign-role/{user_id}", response_model = BareResponse)
async def assign_role(user_id: str, 
                      role: Annotated[AvailableRoles, Body(embed= True)],
                      user: Annotated[UsersModel, Depends(get_current_user)],
                      connection: Annotated[AIOEngine, Depends(connections)]
                      ):
   return await users.assign_role(user,  role, user_id, connection)
    
__annotations__ = (user_router)
