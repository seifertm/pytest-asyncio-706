import asyncio
from copy import deepcopy
from uuid import uuid4
from mongo_thingy import AsyncThingy, connect

import pytest


class Item(AsyncThingy):
    pass


# this is required for async session scoped fixtures
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
async def database():
    connect(
        "mongodb://localhost",
        database_name="pytest-asyncio-706",
        uuidRepresentation="standard",
    )
    return AsyncThingy.database


# we're cleaning our database before any test to avoid side-effects
@pytest.fixture(autouse=True)
async def clean_collections(database):
    for collection_name in await database.list_collection_names():
        collection = database[collection_name]
        await collection.delete_many({})


# we're pre-generating data at the session scope to avoid the cost of
# generating it for every test
@pytest.fixture(autouse=True, scope="session")
def items_data():
    items = []
    for i in range(0, 1000):
        # in real life we would have CPU-intensive operations here
        items.append({"fixed_id": uuid4()})
    return items


# we're re-inserting the data when the test require it
@pytest.fixture
async def items(items_data):
    items_data = deepcopy(items_data)
    await Item.collection.insert_many(items_data)
    return await Item.find().to_list(None)
