from broadcaster import Broadcast
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import db

broadcast = Broadcast("memory://")

app = FastAPI(
    title="Async FastAPI",
    on_startup=[broadcast.connect],
    on_shutdown=[broadcast.disconnect],
)


@app.on_event("startup")
async def startup():
    await db.connect()
    await broadcast.connect()


@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()
    await broadcast.disconnect()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
