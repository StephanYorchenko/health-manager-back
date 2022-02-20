from db import db
from models import UsersRepository, RoomsRepository, StatsPatientRepo


def get_user_repository():
    return UsersRepository(database=db)


def get_rooms_repo():
    return RoomsRepository(database=db)


def get_room_stats_repo() -> StatsPatientRepo:
    return StatsPatientRepo(database=db)
