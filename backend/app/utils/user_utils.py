import os
from pathlib import Path
import json
from fastapi import UploadFile
from redisbloom.client import Client as RedisBloomClient
from app.db.mongo_client import users_collection
from app.db.redis_client import redis_client
from app.core.config import REDIS_HOST


redis_bloom = RedisBloomClient(host=REDIS_HOST)
BLOOM_FILTER_NAME = "usernames_bloom_filter"

PICTURES_DIR = Path("~/SYLA-profile-pictures/").expanduser()
ALLOWED_PIC_EXTENSIONS = ["png", "jpg", "jpeg"]

async def create_bloom_filter():
    """
    Create a bloom filter to store usernames.
    """
    it_exists = await redis_client.exists(BLOOM_FILTER_NAME)
    if not it_exists:  # Check if the Bloom filter already exists
        try:
            redis_bloom.bfCreate(BLOOM_FILTER_NAME, 0.01, 500000)
            await load_usernames_into_bloom_filter()
            print("Bloom filter created successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to create bloom filter: {e}") from e
    else:
        print("Bloom filter already exists.")

async def load_usernames_into_bloom_filter():
    """
    Load usernames from the database into the bloom filter.
    """
    users = await users_collection.find({}, {"username": 1})
    try:
        async for user in users:
            redis_bloom.bfAdd(BLOOM_FILTER_NAME, user["username"])
    except Exception as e:
        raise RuntimeError(f"Failed to load usernames into bloom filter: {e}") from e

def username_is_available(username: str) -> bool:
    """
    Check if a username is available to be used.
    """
    try:
        result = redis_bloom.bfExists(BLOOM_FILTER_NAME, username)
        return not result
    except Exception as e:
        raise RuntimeError(f"Failed to check username availability: {e}") from e

def add_username_to_bloom_filter(username: str):
    """
    Add a username to the bloom filter.
    """
    try:
        redis_bloom.bfAdd(BLOOM_FILTER_NAME, username)
    except Exception as e:
        raise RuntimeError(f"Failed to add username to bloom filter: {e}") from e

async def cache_user(user: dict):
    """
    Cache user data.
    """
    user_id = str(user["_id"])
    user["_id"] = user_id
    data = json.dumps(user)
    try:
        await redis_client.setex(user_id, 3600, data)
    except Exception as e:
        raise RuntimeError(e) from e

async def get_cached_user(user_id: str) -> dict:
    """
    Retrieve cached user data.
    """
    try:
        user_data = await redis_client.get(user_id)
        if not user_data:
            return None
        user_data = json.loads(user_data)
        return user_data
    except Exception as e:
        raise RuntimeError(e) from e

async def delete_cached_user(user_id: str):
    """
    Delete user data from the cache.
    """
    try:
        await redis_client.delete(user_id)
    except Exception as e:
        raise RuntimeError(e) from e
