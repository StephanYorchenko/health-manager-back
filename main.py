import enum
from abc import ABC
from datetime import datetime, date
from typing import List, Optional

import uvicorn
from fastapi import Depends
from pydantic import BaseModel
from starlette.concurrency import run_until_first_complete
from starlette.websockets import WebSocket

from app import app, broadcast
from auth import get_user_from_token
from dependencies import get_user_repository, get_rooms_repo
from schema import RoomDTO, User


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


@app.get("/api/rooms/{id}", response_model=RoomDTO)
async def get_room(
        id: int, user=Depends(get_user_from_token), repository=Depends(get_user_repository),
        rooms_repository=Depends(get_rooms_repo)
):
    user = await repository.get_by_login(login=user)
    if not user:
        raise Exception()
    return await rooms_repository.get_by_id(team_id=id)


@app.get("/api/rooms/{id}/patients", response_model=List[User])
async def get_room(
        id: int, user=Depends(get_user_from_token), repository=Depends(get_user_repository),
        rooms_repository=Depends(get_rooms_repo)
):
    user = await repository.get_by_login(login=user)
    if not user:
        raise Exception()
    return await rooms_repository.get_users_by_room_id(room_id=id)


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


class MixinDatetimeDictSerializer(BaseModel, ABC):
    """Работающий костыль для быстрого перевода datetime и типа лида к json
    виду."""

    def dict(self, **kwargs):
        classes = (date, datetime)
        fields = [name for name, field in self.__fields__.items() if field.type_ in classes]
        data = super().dict(**kwargs)
        for field in fields:
            if not getattr(self, field) is None:
                data[field] = getattr(self, field).isoformat()
        return data


class EventTypes(enum.Enum):
    temp_update = 1
    hmotnost = 2


class EventInDTO(MixinDatetimeDictSerializer):
    user_id: str
    value: float
    saved_at: Optional[datetime]
    type_event: EventTypes


class TempDTO(EventInDTO):
    type_event = EventTypes.temp_update


@app.post("/api/temp")
async def push_temp(data: TempDTO, user=Depends(get_user_from_token), ):
    await broadcast.publish(
        data.user_id,
        data.json()
    )
    return True


@app.get("/api/patient/{id}/temp")
async def get_patient_temperature_log(
        id: int
):
    return [
        TempDTO(
            value=36.6,
            user_id=2,
            saved_at=datetime(year=2022, month=2, day=18, hour=10, minute=0)
        ),
        TempDTO(
            value=36.8,
            user_id=2,
            saved_at=datetime(year=2022, month=2, day=18, hour=11, minute=0)
        ),
        TempDTO(
            value=36.9,
            user_id=2,
            saved_at=datetime(year=2022, month=2, day=18, hour=12, minute=0)
        ),
        TempDTO(
            value=36.7,
            user_id=2,
            saved_at=datetime(year=2022, month=2, day=18, hour=13, minute=0)
        ),
        TempDTO(
            value=36.6,
            user_id=2,
            saved_at=datetime(year=2022, month=2, day=18, hour=14, minute=0)
        ),
        TempDTO(
            value=36.8,
            user_id=2,
            saved_at=datetime(year=2022, month=2, day=18, hour=15, minute=0)
        ),
        TempDTO(
            value=36.9,
            user_id=2,
            saved_at=datetime(year=2022, month=2, day=18, hour=16, minute=0)
        ),
        TempDTO(
            value=36.7,
            user_id=2,
            saved_at=datetime(year=2022, month=2, day=18, hour=17, minute=0)
        ),
    ]


class HmotnostDTO(EventInDTO):
    type_event = EventTypes.hmotnost


@app.get("/api/patient/{id}/hmotnost")
async def get_patient_hmotnost_log(
        id: int
):
    return [
        HmotnostDTO(
            value=85.3,
            user_id=2,
            saved_at=datetime(year=2022, month=2, day=13, hour=10, minute=0)
        ),
        HmotnostDTO(
            value=85.5,
            user_id=2,
            saved_at=datetime(year=2022, month=2, day=14, hour=11, minute=0)
        ),
        HmotnostDTO(
            value=85.6,
            user_id=2,
            saved_at=datetime(year=2022, month=2, day=15, hour=12, minute=0)
        ),
        HmotnostDTO(
            value=87.1,
            user_id=2,
            saved_at=datetime(year=2022, month=2, day=16, hour=13, minute=0)
        ),
        HmotnostDTO(
            value=86.6,
            user_id=2,
            saved_at=datetime(year=2022, month=2, day=17, hour=14, minute=0)
        )
    ]


@app.get("/api/patient/{id}/ivl")
async def get_patient_ivl(
        id: int
):
    return False


@app.get("/api/check")
async def check_user(user=Depends(get_user_from_token), repository=Depends(get_user_repository)):
    user = await repository.get_by_login(login=user)
    return user is not None


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
