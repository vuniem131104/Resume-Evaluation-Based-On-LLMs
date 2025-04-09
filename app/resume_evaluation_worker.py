from redis import Redis
from rq import Worker, Queue

# Define queue name
RESUME_EVALUATION_QUEUE_NAME = "resume_evaluation_queue"

# Create Redis connection
conn = Redis(host='localhost', port=6379)

if __name__ == '__main__':
    # Create queues with explicit connection
    queues = [Queue(RESUME_EVALUATION_QUEUE_NAME, connection=conn)]
    
    # Create worker with explicit queues
    worker = Worker(queues, connection=conn)
    
    # Start worker
    worker.work()   