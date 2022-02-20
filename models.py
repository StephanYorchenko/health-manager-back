import datetime
import random
from typing import Optional, List

from pydantic import BaseModel
from sqlalchemy import select, and_

from schema import User, RoomDTO
from tables import users, rooms, users_rooms, stats_patient, room_params, stats_room


class UserOutDTO(BaseModel):
    id: int
    first_name: Optional[str]
    second_name: Optional[str]
    last_name: Optional[str]


class UsersRepository:
    def __init__(self, database):
        self.database = database

    async def get_by_id(self, user_id: str) -> Optional[User]:
        query = users.select().where(users.c.id == user_id)
        result = await self.database.fetch_one(query)
        return UserOutDTO(
            id=result.get("id"),
            first_name=result.get("first_name"),
            second_name=result.get("second_name"),
            last_name=result.get("last_name"),
        )

    async def get_by_login(self, login: str) -> Optional[User]:
        query = users.select().where(users.c.login == login)
        return await self.database.fetch_one(query)

    async def create(self, data: User):
        query = users.insert().values(
            login=data.login,
            fullName=data.fullName,
        )
        await self.database.execute(query)


class RoomsRepository:
    def __init__(self, database):
        self.database = database

    async def get_by_id(self, team_id: str) -> Optional[RoomDTO]:
        # query = rooms.select().where(teams.c.id == team_id)
        # return await self.database.fetch_one(query)
        return RoomDTO(
            name="Палата №6",
            id=int(team_id)
        )

    async def get_all(self) -> Optional[List[RoomDTO]]:
        query = rooms.select()
        result = await self.database.fetch_all(query)
        return [
            RoomDTO(
                name=v.get("name"),
                identifier=v.get("id")
            )
            for v in result
        ]

    async def get_users_by_room_id(self, room_id: int) -> List[User]:
        query = (
            select((users.c.id, users.c.first_name, users.c.second_name))
                .select_from(users.join(users_rooms, users.c.id == users_rooms.c.user_id))
                .where(users_rooms.c.room_id == room_id)
        )
        result = await self.database.fetch_all(query)
        return [
            User(
                id=v.get("id"),
                login="",
                fullName=v.get("second_name") + " " + v.get("first_name"),
            )
            for v in result
        ]

    async def create(self, room_name: str):
        query = rooms.insert().values(
            name=room_name,
        )
        await self.database.execute(query)


class StatsType(BaseModel):
    type: str
    value: int
    saved_at: str


class ParamsSetted(BaseModel):
    type: str
    value: int


class StatsPatientRepo:
    def __init__(self, database):
        self.database = database

    async def get_n_last_values(self, patient_id: int, type_: str, count: int = 10):
        query = (
            select((stats_patient.c.value, stats_patient.c.saved_at))
                .select_from(stats_patient)
                .where(and_(stats_patient.c.user_id == patient_id, stats_patient.c.type == type_))
                .order_by(stats_patient.c.saved_at.desc())
                .limit(count)
        )
        result = await self.database.fetch_all(query)
        return [
            StatsType(
                type=type_,
                value=v.get("value"),
                saved_at=v.get("saved_at"),
            )
            for v in result
        ]

    async def push_new_value(self, patient_id: int, type_: str, value: float):
        query = (
            stats_patient.insert().values(
                user_id=patient_id,
                type=type_,
                value=value,
                saved_at=datetime.datetime.now()
            )
        )
        await self.database.execute(query)

    async def get_n_last_values_room(self, room_id: int, type_: str, count: int = 10):
        query = (
            select((stats_room.c.value, stats_room.c.saved_at))
                .select_from(stats_room)
                .where(and_(stats_room.c.user_id == room_id, stats_room.c.type == type_))
                .order_by(stats_room.c.saved_at.desc())
                .limit(count)
        )
        result = await self.database.fetch_all(query)
        return [
            StatsType(
                type=type_,
                value=v.get("value"),
                saved_at=v.get("saved_at"),
            )
            for v in result
        ]

    async def push_new_value_room(self, room_id: int, type_: str, value: float):
        query = (
            stats_room.insert().values(
                room_id=room_id,
                type=type_,
                value=value,
                saved_at=datetime.datetime.now()
            )
        )
        await self.database.execute(query)

    async def get_setted_params(self, room_id, type_: List[str] = None):
        if type_ is None:
            type_ = []
        query = (
            select((room_params.c.value, room_params.c.type))
                .select_from(room_params)
                .where(and_(room_params.c.room_id == room_id, room_params.c.type.in_(type_)))
                .order_by(room_params.c.saved_at.desc())
                .distinct(room_params.c.type)
        )
        result = await self.database.fetch_all(query)
        return {
            k.get("type"): k.get("value") for k in result
        }

    async def set_params(self, room_id: int, type_: str, value: int):
        query = (
            room_params.insert().values(
                room_id=room_id,
                type=type_,
                value=value,
                saved_at=datetime.datetime.now(),
            )
        )

        await self.database.execute(query)
