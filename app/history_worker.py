from rq import Worker, Queue
from redis import Redis
import os 
from dotenv import load_dotenv

load_dotenv()

HISTORY_QUEUE_NAME = "history_queue"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

conn = Redis(host=REDIS_HOST, port=6379)

if __name__ == '__main__':
    queues = [Queue(HISTORY_QUEUE_NAME, connection=conn)]
    
    worker = Worker(queues, connection=conn)
    
    worker.work()
