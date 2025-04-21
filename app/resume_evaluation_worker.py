from redis import Redis
from rq import Worker, Queue
import os 
from dotenv import load_dotenv

load_dotenv()

RESUME_EVALUATION_QUEUE_NAME = "resume_evaluation_queue"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

conn = Redis(host=REDIS_HOST, port=6379)

if __name__ == '__main__':
    # Create queues with explicit connection
    queues = [Queue(RESUME_EVALUATION_QUEUE_NAME, connection=conn)]
    
    # Create worker with explicit queues
    worker = Worker(queues, connection=conn)
    
    # Start worker
    worker.work()