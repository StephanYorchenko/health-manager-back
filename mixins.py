from abc import ABC
from typing import List, Generic, TypeVar, Awaitable, Any

from databases import Database
from sqlalchemy import Table


class ResolveNonExistingAttributesMixin:
    def __init__(self, resolvers: List[str]):
        self.resolvers = resolvers

    def __getattr__(self, attr):
        for prefix in self.resolvers:
            if attr.startswith(prefix):
                return getattr(self, prefix)(attr[len(prefix):])
        raise AttributeError()


T = TypeVar('T')


class Repository(ResolveNonExistingAttributesMixin, Generic[T], ABC):
    def __init__(self, table_name: Table, database: Database):
        self.table = table_name
        self.database = database
        super().__init__(resolvers=['get_by_', 'create_'])

    def get_by_(self, field_name: str) -> Awaitable[List[T]]:
        async def get_by_field_name(value) -> List[T]:
            query = self.table.select().where(self.table[field_name] == value)
            return await self.database.fetch_all(query)
        return get_by_field_name


