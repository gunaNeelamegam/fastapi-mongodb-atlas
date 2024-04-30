"""
This file would responsible for interact with db 
all the db data extraction or injection logic where get into this file
"""
from models import UsersModel
from schemas.auth import SignUpResponse, BareResponse, BareUsersModel
from odmantic import AIOEngine
from fastapi import status, Request, Response, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from utils.emailer import send_mail
from schemas.auth import SignUp, LoginModel
from schemas import ChangePassword, AccessTokenResponse
from core.core_types import AvailableLoginTypes, AvailableRoles
from config.settings import settings
from Crypto.Hash import SHA256
from jwt import decode
from jwt.exceptions import ExpiredSignatureError
from datetime import datetime
from odmantic import ObjectId
from pydantic import EmailStr
from typing import Annotated
from utils.uploads import upload
from fastapi.responses import RedirectResponse

async def register(request: Request, user_details: SignUp , connection: AIOEngine):
    user = await connection.get_collection(UsersModel).find_one({
        "$or": [
            # {
            #     "username": user_details.username
            # },
            {
                "email": user_details.email
            }
        ]
    })
    if user:
        raise HTTPException(
            status_code = status.HTTP_406_NOT_ACCEPTABLE,
            detail = BareResponse( status=False, message = "username or email already exist's").model_dump(),
            )
    user = UsersModel(**user_details.model_dump())
    user.hash_password()
    await connection.save(user)
    (unhashed_token, hashed_token , token_expiry) = user.generate_temp_hash()
    mail = {
        "link" : f"{request.base_url}users/verify-email/{unhashed_token}",
        "receiver_mail": user.email,
        "context": "Email Verification"
    }
    user.email_verification_expiry = token_expiry
    user.email_verification_token = hashed_token
    await connection.save(user)
    send_mail(**mail)

    return SignUpResponse(
        user = BareUsersModel(**user.model_dump()), 
        message= "User Registered Successfully",
        status = True,
        )

async def login(response: Response , user_details: LoginModel, connection: AIOEngine, setting= settings()):
    user = await connection.find_one(UsersModel, UsersModel.email == user_details.username)
    if not user:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail = {
            "message": "User Not Exist",
            "status": False
        })

    if user.login_type != AvailableLoginTypes.EMAIL_PASSWORD.value:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = BareResponse(
             message =  f"You hava previously registered using {user.login_type}. please use the {user.login_type} login option to access your account",
            status =  False
        ))
    is_password_valid = user.verify_password(user_details.password)
    if not is_password_valid: raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= BareResponse(
        message = "Invalid User Credential's",
        status = False
    ) .model_dump()
    )
    access_token = user.generate_access_token()
    refresh_token = user.generate_refresh_token()
    user.refresh_token = refresh_token
    await connection.save(user)
    tokens = {
        "access_token": access_token  ,
        "refresh_token": refresh_token
    }
    login_response = SignUpResponse(
            message="User LoggedIn Successfully",
            status= True,
            user = BareUsersModel(**user.model_dump()),
            )
    for key, value in tokens.items():
        response.set_cookie(key, value ,httponly= True, secure = (setting.environment == "production"))
    return login_response    

async def logout(user: UsersModel, connection: AIOEngine, setting = settings()):
    user.refresh_token = None
    await connection.save(user)
    message = {
            "success": True,
            "message": "Logout Successfully"
        }
    response = JSONResponse(content= message)
    response.delete_cookie("access_token", secure= setting.environment == "production", httponly= True)
    response.delete_cookie("refresh_token", secure= setting.environment == "production", httponly= True)
    return response


async def email_verification(verification_token: str,connection: AIOEngine):
    hash_lib = SHA256.new() 
    hash_lib.update(verification_token.encode())
    if hashed_token := hash_lib.digest():
        user = await connection.find_one(UsersModel,{
            "email_verification_token": hashed_token,
            "email_verification_expiry": {
                "$gt": datetime.now()
            }
        })
 
        if not user:
            raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= {
                "message": "Invalid token or expired",
                "status": False
            })
        user = UsersModel.model_validate(user)
        user.email_verification_token = None
        user.email_verification_expiry = None
        user.is_email_verified = True
        await connection.save(user)
        return BareResponse(message= "Email Verification Successfully", status= False)

async def resend_email_verification(request: Request,user: UsersModel | None, connection: AIOEngine):
    if user:
        if user.is_email_verified:
            raise HTTPException(
                status_code= status.HTTP_409_CONFLICT,
                detail = BareResponse(
                    message= "Email is Already Verified",
                    status= False
                ) 
            )
        (unhashed_token, hashed_token, expiry)= user.generate_temp_hash()
        payload = {
            "link": f"{request.base_url}verify-email/{unhashed_token}",
            "receiver_mail": user.email,
            "context": "Email Verification"
        }
        user.email_verification_expiry = expiry
        user.email_verification_token = hashed_token
        await connection.save(user)
        send_mail(**payload)
        return BareResponse(message= "Email Verification Sended Successfully", status= True)
    else:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail = BareResponse(
                message = "User does not exists",
                status= True
            ).model_dump()
        )

async def update_avatar(user: UsersModel, update_avatar:UploadFile, connection: AIOEngine):
    if update_avatar :
        id = await upload(update_avatar.filename, data= await update_avatar.read())
        user.avatar = id
        await connection.save(user)
        return BareResponse(status= True, message= "Avatar Updated Successfully")
    else:
        raise HTTPException(status_code= status.HTTP_406_NOT_ACCEPTABLE,
                            detail= BareResponse(status= False, 
                                                message= "Invalid Data").model_dump())

async def change_current_password(user: UsersModel, user_details: ChangePassword,connection: AIOEngine):
    if user and user.verify_password(user_details.password):
        user.password = user_details.new_password
        user.hash_password()
        await connection.save(user)
        return BareResponse(
            status= True,
            message= "Password Changed Successfully"
        )
    else:
        raise HTTPException(
            status_code= status.HTTP_409_CONFLICT,
            detail= BareResponse(
                message= "Invalid Credentials",
                status= False
            ).model_dump()
        )
    
async def reset_forgetten_password(new_password: str, reset_password_token: str, connection: AIOEngine):
    hashed_token = SHA256.new()
    hashed_token.update(reset_password_token.encode())
    hashed_reset_token = hashed_token.digest()
    user = await connection.find_one(UsersModel,{
        "forget_password_expiry": {
            "$gt": datetime.now()
        },
        "forget_password_token": hashed_reset_token
    })
    if user :
        user.forget_password_token = None
        user.forget_password_expiry = None
        user.password = new_password
        user.hash_password()
        await connection.save(user)
        return BareResponse(message= "Password Reseted Successfully", status= True)
    else:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED,
                            detail= BareResponse(message= "Invalid token or token expiry").model_dump())

async def forget_password_request(request: Request, email: Annotated[EmailStr, "User Authentication mail"] , connection: AIOEngine):
    user = await connection.find_one(UsersModel, UsersModel.email == email)
    if user:
        (unhashed_token,hashed_token, expiry)= user.generate_temp_hash()
        user.forget_password_expiry = expiry
        user.forget_password_token = hashed_token
        await connection.save(user)

        payload = {
            "link": f"{request.base_url}users/reset-password/{unhashed_token}",
            "receiver_mail": user.email,
            "context": "Reset Password"
        }
        send_mail(**payload)
        return BareResponse(message="Password reset mail has been sent on your mail id")
    else:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, 
                            detail= BareResponse(message = "UnAuthorized Request", 
                                                status= False).model_dump(),
                                                )
    
async def refresh_access_token(response : Response,token: str | None , connection: AIOEngine, setting = settings()):
    if token:
        try:
           decoded_info:dict = decode(token, setting.refresh_token_secret_key, algorithms=[setting.algorithm])
           if user_id :=decoded_info.get("id"):
               user = await connection.find_one(UsersModel, UsersModel.id == ObjectId(user_id))
               if user:
                if token == user.refresh_token:
                    access_token = user.generate_access_token()
                    refresh_token = user.generate_refresh_token()
                    user.refresh_token = refresh_token
                    tokens = {
                        "access_token": access_token  ,
                        "refresh_token": refresh_token
                    }
                    for key, value in tokens.items():
                        response.set_cookie(key, value ,httponly= True, secure = (setting.environment == "production"))
                    
                    return AccessTokenResponse(
                        **tokens,
                        message= "Access Refresh Token",
                        status= True
                    )
                else:
                    raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED,
                                         detail = BareResponse(message="Invalid Refresh Token", status= False).model_dump(),
                                         )
               else:
                   raise HTTPException(
                       status_code= status.HTTP_401_UNAUTHORIZED, 
                       detail= BareResponse(message= "Invalid refresh Token , Please Login or Signup").model_dump()
                   )
               
        except ExpiredSignatureError as e:
            raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail= BareResponse(
                    message= "Invalid refresh Token",
                    status= False
                ).model_dump()
            )

    else:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= BareResponse(
                message= "Unauthorized Request to Access the resource's",
                status= False
            ).model_dump()
        )
    
async def assign_role(user: UsersModel, role: AvailableRoles, user_id: ObjectId | str, connection:AIOEngine):
    extracted_user = await connection.find_one(UsersModel, UsersModel.id == ObjectId(user_id))
    if extracted_user:
        extracted_user.role = role
        await connection.save(extracted_user)
        return BareResponse(message="Role Updated Successfully")
    else:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, 
                            detail= BareResponse(message="User Not Found", status= False).model_dump(),
                            )

async def handle_social_login(user: UsersModel, setting = settings()):
    access_token = user.generate_refresh_token()
    refresh_token = user.generate_access_token()
    tokens = {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

    response = RedirectResponse("/")
    for key, value in tokens.items():
        response.set_cookie(
            key,
            value = value,
            httponly= True, secure = setting.environment == "production")
    return response