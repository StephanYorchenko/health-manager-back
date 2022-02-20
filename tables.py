from sqlalchemy import Table, Integer, Column, String, DateTime, ForeignKey, Float, Text

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
    Column("first_name", String, default=""),
    Column("second_name", String, default=""),
    Column("last_name", String, default=""),
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

stats_patient = Table(
    "stats_patient",
    metadata,
    Column("user_id",  ForeignKey(_user_id, ondelete="CASCADE"), nullable=False),
    Column("type", String, nullable=False),
    Column("value", Float),
    Column("saved_at", DateTime(timezone=True))
)


stats_room = Table(
    "stats_room",
    metadata,
    Column("room_id",  ForeignKey(_room_id, ondelete="CASCADE"), nullable=False),
    Column("type", String, nullable=False),
    Column("value", Float),
    Column("saved_at", DateTime(timezone=True))
)

room_params = Table(
    "room_params",
    metadata,
    Column("room_id",  ForeignKey(_room_id, ondelete="CASCADE"), nullable=False),
    Column("type", String, nullable=False),
    Column("value", Float),
    Column("saved_at", DateTime(timezone=True))
)

rozbory = Table(
    "rozbory",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", ForeignKey(_user_id, ondelete="CASCADE"), nullable=False),
    Column("author_id", ForeignKey(_user_id, ondelete="CASCADE"), nullable=False),
    Column("text", Text),
    Column("saved_at", DateTime(timezone=True), nullable=False)
)

jmenovani = Table(
    "jmenovani",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", ForeignKey(_user_id, ondelete="CASCADE"), nullable=False),
    Column("author_id", ForeignKey(_user_id, ondelete="CASCADE"), nullable=False),
    Column("text", Text),
    Column("saved_at", DateTime(timezone=True), nullable=False)
)