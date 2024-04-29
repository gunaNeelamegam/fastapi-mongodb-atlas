from enum import Enum

class AvailableRoles(str, Enum):
    user: str = "user"
    admin: str = "admin"
    manager: str = "manager"

class AvailableLoginTypes(str, Enum):
    EMAIL_PASSWORD: str = "EMAIL_PASSWORD"
    GOOGLE: str = "GOOGLE"
    FACEBOOK:str = "FACEBOOK"
    GITHUB: str = "GITHUB"    
