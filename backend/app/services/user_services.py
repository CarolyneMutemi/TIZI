from bson import ObjectId, errors
from fastapi import HTTPException, status
from pymongo import ReturnDocument
from app.db.mongo_client import users_collection
from app.utils.user_utils import add_username_to_bloom_filter, username_is_available


async def find_user_by_email(email: str) -> dict:
    """
    Retrieves a user associated with given email.
    """
    user = await users_collection.find_one({"email": email})
    if not user:
        return None
    user["_id"] = str(user["_id"])
    return user

async def create_user(user: dict) -> str:
    """
    Adds a user to the database.
    """
    username = user.get("username")
    if not username_is_available(username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already in use."
        )
    add_username_to_bloom_filter(username)

    result = await users_collection.insert_one(user)
    user["_id"] = str(result.inserted_id)

    return str(result.inserted_id)

async def update_username(user_id: str, username: str) -> dict:
    """
    Updates username.
    """
    updated_document = await users_collection.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": {"username": username}},
        return_document=ReturnDocument.AFTER,  # Return the document after the update
        projection={username: 1, "_id": 0}  # Project only the updated event
    )

    if not updated_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.")

    return updated_document

async def find_user_by_id(user_id: str) -> dict:
    """
    Retrieves a user by their ID.
    """
    try:
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        user["_id"] = str(user["_id"])
    except errors.InvalidId as exc:
        raise HTTPException(status_code=400, detail="Invalid post ID") from exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred: {e}") from e
    return user

async def async_delete_user(user_id: str):
    """
    Deletes a user from the database.
    """
    user = await find_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    try:
        result = await users_collection.delete_one({"_id": ObjectId(user_id)})
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
    except errors.InvalidId as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invalid ID: {exc}"
        ) from exc
