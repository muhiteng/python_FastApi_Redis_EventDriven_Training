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


# end points
@app.post('/deliveries/create')
async def create(request: Request):
    body = await request.json()
    delivery = Delivery(budget=body['data']['budget'], notes=body['data']['notes']).save()
    event = Event(delivery_id=delivery.pk, type=body['type'], data=json.dumps(body['data'])).save()
    state = consumers.CONSUMERS[event.type]({}, event)
    # store in redis cache
    redis.set(f'delivery:{delivery.pk}', json.dumps(state))
    return state

@app.get('/deliveries/{pk}/status')
async def get_state(pk: str):
    state = redis.get(f'delivery:{pk}')

    if state is not None:
        # json.loads to convert string to object json
        return json.loads(state)

    state = build_state(pk)
     # json.dumps to convert object json to string
    redis.set(f'delivery:{pk}', json.dumps(state))
    return state


@app.post('/event')
async def dispatch(request: Request):
    body = await request.json()
    delivery_id = body['delivery_id']
    state = await get_state(delivery_id)
    event = Event(delivery_id=delivery_id, type=body['type'], data=json.dumps(body['data'])).save()
    new_state = consumers.CONSUMERS[event.type](state, event)
    redis.set(f'delivery:{delivery_id}', json.dumps(new_state))
    return new_state



def build_state(pk: str):
    pks = Event.all_pks()
    all_events = [Event.get(pk) for pk in pks]
    events = [event for event in all_events if event.delivery_id == pk]
    state = {}

    for event in events:
        state = consumers.CONSUMERS[event.type](state, event)

    return state

