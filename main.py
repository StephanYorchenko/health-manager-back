import enum
from abc import ABC
from datetime import datetime, date
from typing import List, Optional

import uvicorn
from fastapi import Depends, Body
from pydantic import BaseModel
from starlette.concurrency import run_until_first_complete
from starlette.requests import Request
from starlette.websockets import WebSocket

from app import app, broadcast
from auth import get_user_from_token
from dependencies import get_user_repository, get_rooms_repo, get_room_stats_repo
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
async def push_temp(
        id: int = Body(...), value: float = Body(...), user=Depends(get_user_from_token),
        repository=Depends(get_room_stats_repo)
):
    if not user:
        raise Exception()
    print(value, )
    await repository.push_new_value(patient_id=id, type_="temp", value=value, )
    return True


@app.get("/api/patient/{id}/temp")
async def get_patient_temperature_log(
        id: int, user=Depends(get_user_from_token), repository=Depends(get_room_stats_repo)
):
    if not user:
        raise Exception()
    return await repository.get_n_last_values(
        patient_id=id,
        count=10,
        type_="temp"
    )


class HmotnostDTO(EventInDTO):
    type_event = EventTypes.hmotnost


@app.post("/api/hmotnost")
async def push_hmotnost(
        id: int = Body(...),
        value: int = Body(...),
        user=Depends(get_user_from_token),
        repository=Depends(get_room_stats_repo)
):
    if not user:
        raise Exception()
    await repository.push_new_value(patient_id=id, type_="hmotnost", value=value, )
    return True


@app.get("/api/patient/{id}/hmotnost")
async def get_patient_hmotnost_log(
        id: int, user=Depends(get_user_from_token), repository=Depends(get_room_stats_repo)
):
    if not user:
        raise Exception()
    return await repository.get_n_last_values(
        patient_id=id,
        count=10,
        type_="hmotnost"
    )


@app.get("/api/patient/{id}")
async def get_patient(id: int, repository=Depends(get_user_repository)):
    user = await repository.get_by_id(user_id=id)
    return user


@app.get("/api/patient/{id}/ivl")
async def get_patient_ivl(
        id: int,
        repository=Depends(get_room_stats_repo)
):
    return await repository.get_n_last_values(
        patient_id=id, type_="ivl", count=1
    )


@app.get("/api/check")
async def check_user(user=Depends(get_user_from_token), repository=Depends(get_user_repository)):
    user = await repository.get_by_login(login=user)
    return user is not None


class DataPush(BaseModel):
    temp: int
    hum: int
    lx: int
    fan: int
    heat: int
    light: int
    setTemp: int
    setLx: int


@app.post("/api/set")
async def set_value(
        request: Request,
        type_: str = Body(..., alias="type"),
        value: float = Body(...),
        room_id: int = Body(1),
        repository=Depends(get_room_stats_repo)
):
    print(await request.json())
    await repository.set_params(type_=type_, value=value, room_id=room_id)
    return 1


@app.post("/api/push")
async def push_data(
        request: Request,
        repository=Depends(get_room_stats_repo)
):
    data = await request.json()
    print("Даня лох", data)
    data = DataPush.parse_obj(data)
    print('-----')
    for k, v in data.dict().items():
        await repository.push_new_value_room(room_id=1, type_=k, value=v)
    print('############')
    need_to_set_up = await repository.get_setted_params(room_id=1, type_=["heat", "mt", "lx", "wg"])
    print('&&&&&&&&&&&&&&&&')
    need_heat = int(need_to_set_up.get("heat", 20))
    mt = int(need_to_set_up.get("mt", 20))
    lx = int(need_to_set_up.get("lx", 350))
    wg = int(need_to_set_up.get("wg", 0))
    print("*****************")
    return f"1 {need_heat}\n2 {mt}\n3 {lx}\n4 {wg}\n"


@app.get("/api/rooms/{id}/temperature")
async def get_temparature(
        id: int, repository=Depends(get_room_stats_repo)
):
    return await repository.get_stats_room(room_id=id, type_="temp")


@app.get("/api/rooms/{id}/lx")
async def get_lx(
        id: int, repository=Depends(get_room_stats_repo)
):
    return await repository.get_stats_room(room_id=id, type_="lx")


@app.get("/api/patient/{id}/rozbory")
async def get_anals(
        id: int, repository=Depends(get_room_stats_repo)
):
    return await repository.get_anals(user_id=id)


@app.get("/api/patient/{id}/jmenovani")
async def get_jmenovani(
        id: int, repository=Depends(get_room_stats_repo)
):
    return await repository.get_jmenovani(user_id=id)


class Text(BaseModel):
    text: str


@app.post("/api/patient/{id}/rozbory")
async def push_anal(
        id: int,
        input_dto: Text,
        user=Depends(get_user_from_token),
        repository=Depends(get_room_stats_repo),
        users_repo=Depends(get_user_repository)
):
    us = await users_repo.get_by_login(user)
    await repository.push_anal(user_id=id, author_id=us.id, text=input_dto.text)
    return True


@app.post("/api/patient/{id}/jmenovani")
async def push_jmenovani(
        id: int,
        input_dto: Text,
        user=Depends(get_user_from_token),
        repository=Depends(get_room_stats_repo),
        users_repo=Depends(get_user_repository)
):
    us = await users_repo.get_by_login(user)
    await repository.push_jmenovani(user_id=id, author_id=us.id, text=input_dto.text)
    return True


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
