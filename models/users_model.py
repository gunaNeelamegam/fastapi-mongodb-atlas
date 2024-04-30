from odmantic import Model,Field, ObjectId, Reference
from pydantic import EmailStr
from datetime import datetime, timezone
from core import AvailableRoles, AvailableLoginTypes
from passlib.context import CryptContext
from Crypto.Hash import SHA256
from Crypto import Random
from datetime import datetime, timedelta
from config.settings import settings
from jwt import encode

"""
Re-genarating the hashed password using the passlib module 
"""
password_context = CryptContext(schemes= ["bcrypt"], deprecated= "auto")
day = lambda  setting_day: datetime.now() + timedelta(days = int(setting_day[:-1]))
year = lambda setting_year: datetime.now() + timedelta(days= 365 * int(setting_year[:-1]))

FORMAT = {
    "d": day, 
    "y": year,
}
class UsersModel(Model):
    username : str = Field(
                max_length= 50, min_length= 4, 
                description= "UserName must be more than 4 to 50 character's")
    email: EmailStr = Field(unique= True)
    role: AvailableRoles = Field(default= AvailableRoles.user)
    avatar: ObjectId | None = Field(default= None)
    password: str = Field(description= "Password must be more than 8 character's", min_length = 8)
    refresh_token: str | None = Field(default = None, description= "Refresh Token for revokeing the access token")
    login_type: AvailableLoginTypes = Field(default = AvailableLoginTypes.EMAIL_PASSWORD, description= "Login Type for OAuth")
    is_email_verified:  bool = Field(default= False, description="Email Verification")
    forget_password_token: str | bytes| None  = Field(default= None, description= "Forget password Token ")
    forget_password_expiry : datetime | None = Field(default= None, description="Forget Password token expiry")
    email_verification_token: str | None | bytes  = Field(default= None, description= "Email Verification Token")
    email_verification_expiry : datetime | None  = Field(default= None, description="Email Verification Expiry")
    created_at: datetime = Field(default_factory= lambda : datetime.now(timezone.utc))
    updated_at: datetime | None = None
    
    def hash_password(self) -> None:
        hashed_password = password_context.hash(self.password)
        self.password = hashed_password
    
    def generate_access_token(self, setting = settings()):
        payload = {
            "exp": FORMAT.get(setting.access_token_secret_key_expiry[-1])(setting.access_token_secret_key_expiry),
            "id": str(self.id)
        }
        return encode(payload= payload, key= setting.access_token_secret_key, algorithm= setting.algorithm)
    
    def generate_refresh_token(self, setting = settings()):
        payload = {
            "exp": FORMAT.get(setting.refresh_token_secret_key_expiry[-1])(setting.refresh_token_secret_key_expiry),
            "id": str(self.id)
        }
        return encode(payload= payload, key= setting.refresh_token_secret_key, algorithm= setting.algorithm)


    def verify_password(self, unhashed_password: str):
        return password_context.verify(unhashed_password, self.password)
    
    @staticmethod
    def generate_temp_hash():
        setting = settings()
        unhashed_token = Random.get_random_bytes(20).hex()
        hash_lib =  SHA256.new()
        hash_lib.update(unhashed_token.encode())
        hashed_token = hash_lib.digest()
        token_expiry = datetime.now() + timedelta(minutes = setting.temp_token_expiry)
        return (unhashed_token, hashed_token, token_expiry)
