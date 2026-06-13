# celery is a distributed task queue system that allows you to run tasks asynchronously in the background, 
# separate from the main application flow. 
# It is commonly used for handling time-consuming tasks, such as sending emails, processing data, 
# or performing long-running computations, without blocking the main application.
# celery consists of three main components:
# 1. Celery Application: This is the core of the Celery system, where you define your tasks and configure the Celery settings. 
#    It is responsible for managing the task queue, workers, and the communication with the message broker and result backend.
# 2. Message Broker: This is the intermediary that Celery uses to send and receive messages between the main application and the worker processes.
# Common message brokers include RabbitMQ and Redis.
# 3. Worker Processes: These are the processes that execute the tasks defined in the Celery application. 
# Workers listen for tasks on the message broker and execute them asynchronously when they are received.

# In this file, we set up the Celery application instance and configure it to use RabbitMQ as the message broker and Redis as the result backend.
# We also define various configuration options to control the behavior of the Celery workers and tasks, such as serialization formats, retry policies, time limits, and logging formats.
# Finally, we use the `autodiscover_tasks` method to automatically discover and register task modules in the specified package(s), allowing us to organize our tasks in a modular way

# Import the Celery class used to create a task queue application.
from celery import Celery
# Import project settings so we can read broker/backend connection values.
from backend.app.core.config import settings

# Create one Celery application instance for this project.
celery_app = Celery(
    # Name of this Celery application.
    "worker",
    # RabbitMQ URL used by Celery to receive and dispatch tasks.
    broker=f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//",

    # Redis URL used by Celery to store task results/status.
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
) 

# Configure runtime behavior for workers, tasks, retries, and logging.
celery_app.conf.update(
    # Serialize outgoing tasks as JSON. Serialization needed since Celery sends tasks as messages over the broker, and JSON is a common format for message payloads.
    task_serializer="json",
    # Track and publish the "started" state for tasks.
    task_track_started=True,
    # Serialize task results as JSON.
    result_serializer="json",
    # Only accept JSON content from producers.
    accept_content=["application/json"],
    # Retry backend operations up to this many times.
    result_backend_max_retries=10,
    # Send "task sent" events for monitoring tools.
    task_send_sent_event=True,
    # Store extended metadata in task results.
    result_extended=True,
    # Keep retrying backend operations when they fail temporarily.
    result_backend_always_retry=True,
    # Expire results after 1 hour to avoid unbounded storage growth.
    expire_results=3600,  # Expire results after 1 hour
    # Hard limit: terminate tasks that run beyond 5 minutes.
    task_time_limit=300,  # Limit task execution time to 5 minutes
    # Soft limit: warn/interrupt tasks after 4 minutes so they can exit cleanly.
    task_soft_time_limit=240,  # Soft time limit of 4 minutes
    # Also emit event when a task is sent (duplicate-style key kept as-is).
    send_task_sent_event=True,
    # Acknowledge tasks only after execution starts/finishes to reduce task loss.
    task_acks_late=True,  # Enable late acknowledgment of tasks
    # Requeue/reject tasks if a worker process dies unexpectedly.
    task_reject_on_worker_lost=True,  # Reject tasks if the worker is lost
    # Pull one task at a time per worker process for fairer distribution.
    worker_prefetch_multiplier=1,  # Prefetch only one task at a time
    # Wait this many seconds before retrying a failed task.
    task_default_retry_delay=60,  # Default retry delay in seconds
    # Maximum automatic retries per task.
    task_max_retries=3,  # Maximum number of retries for a task
    # Default queue name for tasks without an explicit queue.
    task_default_queue="nexgen_task",  # Default queue for tasks
    # Auto-create queues when a task targets a queue that does not yet exist.
    task_create_missing_queues=True,  # Automatically create missing queues
    # Recycle worker child process after this many tasks to reduce leaks.
    worker_max_tasks_per_child=1000,  # Restart worker after it has processed 1000 tasks
    # Recycle worker process when memory threshold is exceeded.
    worker_maximum_memory_per_child=5000,  # Restart worker after it exceeds 5000MB of memory usage
    # Format used for general worker log messages.
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",  # Log format for workers
    # Format used for per-task log messages.
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] Task %(task_name)s[%(task_id)s]: %(message)s",  # Log format for tasks
)

# Automatically discover and register task modules in the listed package(s).
celery_app.autodiscover_tasks(
    # Package list where Celery should search for task modules.
    packages=["backend.app.core.emails"],
    # Look for a module named "tasks" inside each package.
    related_name="tasks",
    # Force discovery even if packages were imported earlier.
    force=True,  # Force autodiscovery even if the module is already imported
)