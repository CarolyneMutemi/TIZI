from pymongo import errors
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import MONGO_HOST

try:
    mongo_client = AsyncIOMotorClient(f"mongodb://{MONGO_HOST}:27017/", serverSelectionTimeoutMS=5000)

    db = mongo_client["FitConnect"]
    users_collection = db.users

except errors.ServerSelectionTimeoutError as exc:
    raise ConnectionError("Failed to connect to MongoDB: Server Selection Timeout.") from exc

except errors.ConnectionFailure as exc:
    raise ConnectionError("Failed to connect to MongoDB: Connection Failure.") from exc

except errors.PyMongoError as exc:
    raise ConnectionError(f"An error occurred: {exc}") from exc

async def test_mongo_connection(mclient: AsyncIOMotorClient):
    """
    Test the connection to MongoDB.
    """
    try:
        await mclient.admin.command("ping")
        print("Successfully connected to MongoDB!")
    except errors.ServerSelectionTimeoutError as exc:
        raise ConnectionError("Failed to connect to MongoDB: Server Selection Timeout.") from exc
    except errors.ConnectionFailure as exc:
        raise ConnectionError("Failed to connect to MongoDB: Connection Failure.") from exc
    except errors.PyMongoError as exc:
        raise ConnectionError(f"An error occurred: {exc}") from exc
