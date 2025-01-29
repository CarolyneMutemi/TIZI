from fastapi import HTTPException
from app.db.mongo_client import users_collection

async def get_groups(page:int = 1, limit:int = 5):
    """
    Get groups details.
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="Page number must be 1 or greater.")

    skip = (page - 1) * limit  # Calculate how many documents to skip

    # Query MongoDB
    users_cursor = users_collection.find({}).skip(skip).limit(limit)
    users_list = await users_cursor.to_list(length=limit)  # Convert cursor to list

    # Convert _id (ObjectId) to string
    for user in users_list:
        user["_id"] = str(user["_id"])

    return {"page": page, "limit": limit, "users": users_list}
