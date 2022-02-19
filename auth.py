from fastapi import Header


async def get_user_from_token(header=Header("", alias="Authorization"), ):
    token = header.replace("Bearer ", "")
    return token
