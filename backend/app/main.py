from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints.auth import auth_router
from app.api.endpoints.email_auth import email_auth_router
from app.api.endpoints.events import events_router
from app.api.endpoints.user import user_router
from app.utils.user_utils import create_bloom_filter
from app.db.redis_client import test_redis_connection, redis_client
from app.db.mongo_client import test_mongo_connection, mongo_client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

app.include_router(email_auth_router)
app.include_router(auth_router, prefix="/auth")
app.include_router(user_router, prefix="/users")
app.include_router(events_router, prefix="/events")

@app.on_event("startup")
async def startup_event():
    """
    This function is called when the app starts.
    It will ensure the bloom filter is created if it does not exist.
    """
    try:
        await create_bloom_filter()
        await test_redis_connection(redis_client)
        await test_mongo_connection(mongo_client)
    except Exception as e:
        print(f"Error occurred: {e}")

@app.get("/home")
async def home():
    return {"message": "Home page."}

@app.get("/login_page")
async def login():
    return {"message": "Login page."}

@app.get("/email-register")
async def register():
    return {"message": "Email register page."}

@app.get("/google-register")
async def google_register():
    return {"message": "Google register page."}
