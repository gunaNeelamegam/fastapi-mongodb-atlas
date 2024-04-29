from fastapi import FastAPI
from routes import user_router, bare_router, auth_router

app = FastAPI(debug = True,
                terms_of_service= "sample auth application with fastapi",
                title = "Auth Application",
                root_path= "/api/v1")


app.include_router(bare_router)
app.include_router(auth_router)
app.include_router(user_router)