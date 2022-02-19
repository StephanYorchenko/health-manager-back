from db import db
from models import UsersRepository, RoomsRepository


def get_user_repository():
    return UsersRepository(database=db)


def get_rooms_repo():
    return RoomsRepository(database=db)
