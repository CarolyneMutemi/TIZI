"""
Handle events.
"""
from bson import ObjectId
from uuid import uuid4
from fastapi import HTTPException, status
from pymongo import ReturnDocument

from app.db.mongo_client import users_collection
from app.schemas.events.event_requests import IncomingEventSchema, IncomingEventUpdate


async def add_event(user_id: str, event: IncomingEventSchema) -> dict:
    """
    Adds events.
    """
    event_id = str(uuid4())
    event_obj = event.model_dump()
    event_obj["date"] = str(event_obj["date"])
    updated_document = await users_collection.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": {f"events.{event_id}": event_obj}},
        return_document=ReturnDocument.AFTER,  # Return the document after the update
        projection={f"events.{event_id}": 1, "_id": 0}  # Project only the updated event
    )

    if not updated_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.")
    
    event_obj = updated_document.get("events", {}).get(event_id)
    event_obj["event_id"] = event_id
    print("Event Object ", event_obj)

    return updated_document.get("events", {}).get(event_id)

async def update_event(user_id: str, event_id: str, event: IncomingEventUpdate) -> dict:
    """
    Update an event.
    """
    event_update = event.model_dump()

    update_fields = {f"events.{event_id}.{key}": value for key, value in event_update.items() if value is not None}

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="No valid fields to update."
            )

    # Perform the update in MongoDB
    updated_document = await users_collection.find_one_and_update(
        {"_id": ObjectId(user_id), f"events.{event_id}": {"$exists": True}},
        {"$set": update_fields},
        return_document=ReturnDocument.AFTER,  # Return the document after the update
        projection={f"events.{event_id}": 1, "_id": 0}  # Project only the updated event
    )

    if not updated_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or event not found.")
    
    event_obj = updated_document.get("events", {}).get(event_id)
    event_obj["event_id"] = event_id

    return event_obj

async def delete_event(user_id: str, event_id: str):
    """
    Delete an event.
    """
    # Use $unset to remove the event from the events dictionary
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$unset": {f"events.{event_id}": ""}}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.")
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found or already deleted.")
