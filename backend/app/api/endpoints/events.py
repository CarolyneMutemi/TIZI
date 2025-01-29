from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from app.api.endpoints.user import get_current_user
from app.schemas.events.event_requests import IncomingEventSchema, IncomingEventUpdate
from app.services.events_services import add_event, update_event, delete_event


events_router = APIRouter()

@events_router.post('/')
async def add_new_event(event: IncomingEventSchema, user: dict = Depends(get_current_user)):
    """
    Add event.
    """
    user_id = user.get("_id")
    added_event = await add_event(user_id=user_id, event=event)
    added_event["date"] = str(added_event["date"])
    print("Added event: ", added_event)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=added_event
    )

@events_router.put('/{event_id}')
async def edit_event(event_id: str,
                     event: IncomingEventUpdate,
                     user: dict = Depends(get_current_user)):
    """
    Edit an event.
    """
    user_id = user.get("_id")
    updated_event = await update_event(user_id, event_id, event)
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content=updated_event)

@events_router.delete('/{event_id}')
async def delete_an_event(event_id: str, user: dict = Depends(get_current_user)):
    """
    Delete an event.
    """
    user_id = user.get("_id")
    await delete_event(user_id, event_id)
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content={"status": "success", "message": "Deleted successfully."})
