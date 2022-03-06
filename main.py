from typing import List

import uvicorn
from fastapi import Depends
from starlette.concurrency import run_until_first_complete
from starlette.websockets import WebSocket

from app import app, broadcast
from auth import get_user_from_token
from dependencies import get_user_repository, get_rooms_repo
from schema import RoomDTO


@app.get("/api/rooms", response_model=List[RoomDTO])
async def get_rooms(
        user=Depends(get_user_from_token),
        rooms_repository=Depends(get_rooms_repo),
        repository=Depends(get_user_repository)
):
    user = repository.get_by_login(login=user)
    if not user:
        raise Exception()
    return await rooms_repository.get_all()


async def events_ws_receiver(websocket, channel: str):
    async for message in websocket.iter_text():
        await broadcast.publish(channel=channel, message=message)


async def events_ws_sender(websocket, channel: str):
    async with broadcast.subscribe(channel=channel) as subscriber:
        async for event in subscriber:
            await websocket.send_text(event.message)


@app.websocket("/{channel_id}")
async def websocket_endpoint(websocket: WebSocket, channel_id: str):
    await websocket.accept()
    await run_until_first_complete(
        (events_ws_receiver, {"websocket": websocket, "channel": channel_id}),
        (events_ws_sender, {"websocket": websocket, "channel": channel_id}),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
