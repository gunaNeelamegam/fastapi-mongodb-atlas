from pydantic import BaseModel, Field
from .auth import BareResponse

class ChangePassword(BaseModel):
    password: str = Field(description = "Current Password")
    new_password: str = Field(description="Update Password")

class AccessTokenResponse(BareResponse):
    access_token: str
    refresh_token: str
