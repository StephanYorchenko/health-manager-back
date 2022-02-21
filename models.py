import datetime
import random
from typing import Optional, List, Any

from pydantic import BaseModel, Field
from sqlalchemy import select, and_

from schema import User, RoomDTO
from tables import users, rooms, users_rooms, stats_patient, room_params, stats_room, rozbory, jmenovani


class UserOutDTO(BaseModel):
    id: int
    first_name: Optional[str]
    second_name: Optional[str]
    last_name: Optional[str]


class AnalOutDTO(BaseModel):
    id: int
    text: str
    author_first_name: Optional[str]
    author_second_name: Optional[str]
    author_last_name: Optional[str] = Field("")
    author_id: int
    saved_at: str


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
        res = await self.database.fetch_one(query)
        return UserOutDTO(
            id=res.get("id"),
            first_name=res.get("first_name"),
            second_name=res.get("second_name"),
            last_name=res.get("last_name"),
        )

    async def create(self, room_id: int, fn: str, sn: str, ln: str, lg: str):
        id = random.randint(100, 1000000)
        query = users.insert().values(
            login=lg,
            first_name=fn,
            second_name=sn,
            last_name=ln,
            id=id
        )
        await self.database.execute(query)
        query1 = (
            users_rooms.insert().values(
                user_id=id,
                room_id=room_id
            )
        )
        await self.database.execute(query1)


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
    value: float
    saved_at: str


class ParamsSetted(BaseModel):
    type: str
    value: float


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
                saved_at=str(v.get("saved_at")),
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
                saved_at=str(v.get("saved_at")),
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

    async def get_stats_room(self, type_: str, room_id: int):
        query = (
            stats_room
                .select()
                .where(
                    and_(
                        stats_room.c.room_id == room_id,
                        stats_room.c.type == type_
                    )
                )
                .order_by(stats_room.c.saved_at.desc())
                .limit(20)
        )
        data = await self.database.fetch_all(query)
        return [v.get("value") for v in data]

    async def get_setted_params(self, room_id, type_: List[str] = None):
        if type_ is None:
            type_ = []
        query = (
            select((room_params.c.value, room_params.c.type))
                .select_from(room_params)
                .where(and_(room_params.c.room_id == room_id, room_params.c.type.in_(type_)))
                .order_by(room_params.c.saved_at.desc())
        )
        result = await self.database.fetch_all(query)
        res = {}
        for i in result:
            t = i.get("type")
            if t not in res:
                res[t] = i.get("value")
        return res

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

    # Я уже настолько преисполнился, что не буду выносить анализы и назначения в отдельные репозитории
    async def get_anals(self, user_id: int, count: int = -1):
        query = (
            rozbory
                .join(users, users.c.id == rozbory.c.author_id)
                .select()
                .where(rozbory.c.user_id == user_id)
                .order_by(rozbory.c.saved_at.desc())
        )
        res = await self.database.fetch_all(query)
        return [
            AnalOutDTO(
                id=v[rozbory.c.id],
                text=v[rozbory.c.text],
                author_first_name=v[users.c.first_name],
                author_second_name=v[users.c.second_name],
                author_last_name=v.get(users.c.last_name, ""),
                author_id=v[rozbory.c.author_id],
                saved_at=str(v[rozbory.c.saved_at]),
            )
            for v in res
        ]

    async def push_anal(self, author_id: int, user_id: int, text: str):
        query = (
            rozbory.insert().values(
                text=text,
                author_id=author_id,
                user_id=user_id,
                saved_at=datetime.datetime.now(),
            )
        )

        await self.database.execute(query)

    async def get_jmenovani(self, user_id: int, count: int = -1):
        query = (
            jmenovani
                .join(users, users.c.id == jmenovani.c.author_id)
                .select()
                .where(jmenovani.c.user_id == user_id)
                .order_by(jmenovani.c.saved_at.desc())
        )
        res = await self.database.fetch_all(query)
        return [
            AnalOutDTO(
                id=v[jmenovani.c.id],
                text=v[jmenovani.c.text],
                author_first_name=v[users.c.first_name],
                author_second_name=v[users.c.second_name],
                author_last_name=v.get(users.c.last_name, ""),
                author_id=v[jmenovani.c.author_id],
                saved_at=str(v[jmenovani.c.saved_at]),
            )
            for v in res
        ]

    async def push_jmenovani(self, author_id: int, user_id: int, text: str):
        query = (
            jmenovani.insert().values(
                text=text,
                author_id=author_id,
                user_id=user_id,
                saved_at=datetime.datetime.now(),
            )
        )

        await self.database.execute(query)
