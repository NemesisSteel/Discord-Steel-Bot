from datetime import datetime
from elasticsearch import Elasticsearch

import os
import redis
import json

REDIS_URL = os.getenv('REDIS_URL')
ES_URL = os.getenv('ES_URL')
COUNT = 5000

#es = Elasticsearch([ES_URL])
r = redis.from_url(REDIS_URL, decode_responses=True)

i = 1

while True:
    if i == COUNT:
        fmt = "{}: Indexed {} messages"
        print(fmt.format(now, COUNT))
        i = 1

    payload = r.brpop('mee6.messages')
    if not payload:
        continue

    now = datetime.now()

    raw_message = payload[1]
    message = json.loads(raw_message)
    message['timestamp'] = now
    #es.index(doc_type='message',
    #         id=int(message['id']),
    #         body=message,
    #         index='message')
    i += 1
