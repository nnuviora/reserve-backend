import os
from redis import Redis
from dotenv import load_dotenv

load_dotenv()


redis_url = os.getenv("REDIS_URL")
r = Redis.from_url(redis_url)

print("REDIS_URL = ", redis_url)

r.set("test", "hello")
print(r.get("test"))