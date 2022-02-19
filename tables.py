from sqlalchemy import Table, Integer, Column, String, DateTime, ForeignKey

from db import metadata

_room_id = "rooms.id"
_user_id = "users.id"
_category_id = "categories.id"
_retro_id = "retros.id"
_tensions_id = "tensions.id"

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("login", String, unique=True, nullable=False),
    Column("fullName", String),
)

rooms = Table(
    "rooms",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False)
)

# Вот тут храним связь пациентов и палат.
users_rooms = Table(
    "users_rooms",
    metadata,
    Column("user_id", ForeignKey(_user_id, ondelete="CASCADE"), nullable=False),
    Column("room_id", ForeignKey(_room_id, ondelete="CASCADE"), nullable=False),
)

stats_pacient_temp = Table(
    "temp",
    metadata,
    Column("user_id", ForeignKey(_user_id, ondelete="CASCADE"), nullable=False),
    Column("value", Integer),
    Column("saved_at", DateTime)
)
