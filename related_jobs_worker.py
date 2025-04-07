from redis import Redis
from rq import Worker, Queue, Connection
RELATED_JOBS_QUEUE_NAME = "related_jobs_queue"
listen = [RELATED_JOBS_QUEUE_NAME]
conn = Redis()

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
