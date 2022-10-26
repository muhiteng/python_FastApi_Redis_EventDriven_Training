from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from redis_om import get_redis_connection, HashModel



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)

# redis connection must set:  host,port,password
redis = get_redis_connection(
    host="",
    port=11813,
    password="",
    decode_responses=True
)

# add Model
class Delivery(HashModel):
    budget: int = 0
    notes: str = ''

    class Meta:
        database = redis

# add Model
class Event(HashModel):
    delivery_id: str = None
    type: str
    data: str

    class Meta:
        database = redis

