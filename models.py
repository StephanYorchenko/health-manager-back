import random
from typing import Optional, List

from sqlalchemy import select, and_

from schema import User, RoomDTO
from tables import users, rooms, users_rooms


class UsersRepository:
    def __init__(self, database):
        self.database = database

    async def get_by_id(self, user_id: str) -> Optional[User]:
        query = users.select().where(users.c.id == user_id)
        return await self.database.fetch_one(query)

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
        print(self)
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
            select((users.c.id, users.c.fullName))
                .select_from(users.join(users_rooms, users.c.id == users_rooms.c.user_id))
                .where(users_rooms.c.room_id == room_id)
        )
        result = await self.database.fetch_all(query)
        return [User(
            id=v.get("id"),
            login="",
            fullName=v.get("fullName"),
        ) for v in result]

    async def create(self, room_name: str):
        query = rooms.insert().values(
            name=room_name,
        )
        await self.database.execute(query)
