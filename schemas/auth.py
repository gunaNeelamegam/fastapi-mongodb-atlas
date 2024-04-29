from pydantic import BaseModel, Field, EmailStr, validator
from config.dbconnection import connections
from models import UsersModel
# from utils import async_validation

# async def is_email_unique(email: str, connection = connections()) -> bool:
#     user = await connection.find_one(UsersModel, UsersModel.email == email)
#     return user is None

class SignUp(BaseModel):
    username: str = Field(description= "User Name for the  login user",
                          max_length= 50, 
                          min_length= 4,
                          examples= ["gunaNeelamegam", "guna"])
    email: EmailStr 
    password: str = Field(description="Password for login", examples= ["12345678", "gsgusgigsigsi"] , min_length = 8)

    # @async_validation
    # @validator("email")
    # async def check_email_uniqueness(cls, email):
    #     print("inside email validation")
    #     if not await is_email_unique(email):
    #         raise ValueError("Email Already Exist")
    #     return email

from datetime import datetime
class BareResponse(BaseModel):
    message: str
    status: bool = Field(default= True) 

class BareUsersModel(BaseModel):
    username: str
    role: str
    login_type: str
    is_email_verified: bool 
    created_at: datetime
    updated_at:  datetime | None
    
class SignUpResponse(BareResponse):
    user: BareUsersModel
    model_config = {
        "populate_by_name": True
    }

class LoginModel(BaseModel):
    username:str = Field(alias = "email")
    password: str = Field()

    model_config = {
        "populate_by_name": True
    }