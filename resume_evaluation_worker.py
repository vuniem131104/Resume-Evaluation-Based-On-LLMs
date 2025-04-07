from redis import Redis
from rq import Worker, Queue, Connection
RESUME_EVALUATION_QUEUE_NAME = "resume_evaluation_queue"
listen = [RESUME_EVALUATION_QUEUE_NAME]
conn = Redis()

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
