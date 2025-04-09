from rq import Worker, Queue
from redis import Redis
RELATED_JOBS_QUEUE_NAME = "related_jobs_queue"

conn = Redis(host='localhost', port=6379)

if __name__ == '__main__':
    queues = [Queue(RELATED_JOBS_QUEUE_NAME, connection=conn)]
    
    worker = Worker(queues, connection=conn)
    
    worker.work()
