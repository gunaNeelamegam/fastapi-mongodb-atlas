from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from routes import user_router, bare_router, auth_router
from uvicorn import run
from config.settings import settings
app = FastAPI(debug = True,
                terms_of_service= "sample auth application with fastapi",
                title = "Auth Application",
                root_path= "/api/v1")

setting = settings()
app.add_middleware(SessionMiddleware, secret_key = setting.session_secret)

app.include_router(bare_router)
app.include_router(auth_router)
app.include_router(user_router)


# if __name__ == "__main__":
    # run(app= app, port= 3000)