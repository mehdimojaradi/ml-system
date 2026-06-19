import asyncio
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional

# SQL helper for quick DB ping.
from sqlalchemy import text

# Celery app for Redis and worker checks.
from backend.app.core.celery_app import celery_app
# Async DB session maker.
from backend.app.core.db import async_session
# Logger factory.
from backend.app.core.logging import get_logger

# Logger used in this file.
logger = get_logger()


class ServiceStatus(str, Enum):
    # Everything is OK.
    HEALTHY = "healthy"
    # Check failed.
    UNHEALTHY = "unhealthy"
    # Service works, but with issues.
    DEGRADED = "degraded"
    # Service just started.
    STARTING = "starting"
    # Service is down.
    DOWN = "down"


class HealthCheck:
    # Keep all health-check state here.
    def __init__(self):
        # Service status and check callbacks.
        self._services: Dict[str, ServiceStatus] = {}
        self._check_functions: Dict[str, Callable[[], Awaitable[bool]]] = {}
        self._last_check: Dict[str, datetime] = {}
        # Retry and timeout settings per service.
        self._timeouts: Dict[str, float] = {}
        self._retry_delays: Dict[str, float] = {}
        self._max_retries: Dict[str, int] = {}
        # Lock protects shared state in async code.
        self._lock = asyncio.Lock()
        # Optional dependency map: service -> required services.
        self._dependencies: Dict[str, set[str]] = {}

        # Small cache to avoid running checks too often.
        self._cache_duration: timedelta = timedelta(seconds=25)
        self._cached_status: Optional[Dict[str, Any]] = None
        self._last_check_time: Optional[datetime] = None

    # Make sure listed dependencies exist.
    async def validate_dependencies(
        self, service_name: str, depends_on: list[str]
    ) -> None:
        # No dependencies means nothing to check.
        if not depends_on:
            return

        # Each dependency must already be registered.
        for dep in depends_on:
            if dep not in self._services:
                raise ValueError(
                    f"Dependency '{dep}' not registered for service '{service_name}'"
                )

    # Add a service and its health-check rules.
    async def add_service(
        self,
        service_name: str,
        check_function: Callable[[], Awaitable[bool]],
        timeout: float = 5.0,
        retry_delay: float = 1.0,
        max_retries: int = 3,
        depends_on: list[str] | None = None,
    ) -> None:
        # Save check function and config.
        self._services[service_name] = ServiceStatus.STARTING
        self._check_functions[service_name] = check_function
        self._timeouts[service_name] = timeout
        self._retry_delays[service_name] = retry_delay
        self._max_retries[service_name] = max_retries
        self._last_check[service_name] = datetime.now(timezone.utc)

        # Save optional dependency list.
        if depends_on:
            await self.validate_dependencies(service_name, depends_on)
            self._dependencies[service_name] = set(depends_on)
            logger.info(
                f"Service '{service_name}' registered with dependencies: {depends_on}"
            )

    # Check DB with a tiny query.
    async def check_database(self) -> bool:
        try:
            # Run SELECT 1 to verify DB is reachable.
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
                await session.commit()

                # Save success time.
                self._last_check["database"] = datetime.now(timezone.utc)
                return True
        except Exception as e:
            # Any error means DB check failed.
            logger.error(f"Database health check failed: {e}")
            return False

    # Check Redis with ping.
    async def check_redis(self) -> bool:
        try:
            # Reuse Celery's Redis client.
            redis_client = celery_app.backend.client
            redis_client.ping()
            # Save success time.
            self._last_check["redis"] = datetime.now(timezone.utc)
            return True
        except Exception as e:
            # Any error means Redis check failed.
            logger.error(f"Redis health check failed: {e}")
            return False

    # Check Celery workers (or at least broker reachability).
    async def check_celery(self) -> bool:
        try:
            # Try pinging workers.
            inspect = celery_app.control.inspect()
            workers = inspect.ping()

            # If no worker replies, test broker connection directly.
            if not workers:
                conn = celery_app.connection()
                try:
                    conn.ensure_connection(max_retries=3)
                    logger.warning("No celery workers found, but Rabbitmq is reachable")
                    self._last_check["celery"] = datetime.now(timezone.utc)
                    return True
                finally:
                    conn.close()

            # Save success time.
            self._last_check["celery"] = datetime.now(timezone.utc)
            return True
        except Exception as e:
            # Any error means Celery check failed.
            logger.error(f"Celery health check failed: {e}")
            return False

    # Check one service using retries and timeout.
    async def check_service_health(self, service_name: str) -> ServiceStatus:
        # First check dependencies.
        if service_name in self._dependencies:
            for dep in self._dependencies[service_name]:
                dep_status = await self.check_service_health(dep)
                if dep_status != ServiceStatus.HEALTHY:
                    logger.error(
                        f"Dependency {dep} not healthy for service {service_name}"
                    )
                    return ServiceStatus.DEGRADED

        # Stop early if service is unknown.
        if service_name not in self._check_functions:
            raise ValueError(f"Unknown service: {service_name}")

        # Load this service's check settings.
        check_func = self._check_functions[service_name]
        timeout = self._timeouts.get(service_name, 5.0)
        max_retries = self._max_retries.get(service_name, 3)
        retry_delay = self._retry_delays.get(service_name, 1.0)

        # Track retry info for logs.
        metrics = {"attempts": 0, "total_delay": 0.0, "last_error": None}

        # Retry check up to max_retries.
        for attempt in range(max_retries):
            metrics["attempts"] += 1
            try:
                async with asyncio.timeout(timeout):
                    is_healthy = await check_func()

                    # Success: save healthy state and return.
                    if is_healthy:
                        async with self._lock:
                            self._services[service_name] = ServiceStatus.HEALTHY
                            self._last_check[service_name] = datetime.now(timezone.utc)
                            if attempt > 0:
                                logger.info(
                                    f"Service {service_name} recovered after {metrics['attempts']} attempts"
                                )
                        return ServiceStatus.HEALTHY

                        # False means service is degraded.
                    async with self._lock:
                        self._services[service_name] = ServiceStatus.DEGRADED

                    # Timeout case.
            except asyncio.TimeoutError:
                metrics["last_error"] = f"Timeout after {timeout}s"
                if attempt == max_retries - 1:
                    logger.warning(
                        f"Health check timeout for {service_name} after all retries"
                    )
            # Error case.
            except Exception as e:
                metrics["last_error"] = str(e)
                if attempt == max_retries - 1:
                    logger.error(f"Health check failed for {service_name}: {e}")

            # Wait before next attempt.
            metrics["total_delay"] += retry_delay
            await asyncio.sleep(retry_delay)

        # All retries failed: mark unhealthy.
        async with self._lock:
            self._services[service_name] = ServiceStatus.UNHEALTHY
            logger.error(
                f"Service {service_name} unhealthy after {max_retries} attempts: {metrics['last_error']}"
            )

        return ServiceStatus.UNHEALTHY

    # Check every service and build one response.
    async def check_all_services(self) -> Dict[str, Any]:
        # Return cache if still fresh.
        current_time = datetime.now(timezone.utc)
        if (
            self._cached_status is not None
            and self._last_check_time is not None
            and (current_time - self._last_check_time) < self._cache_duration
        ):
            return self._cached_status

        # Copy service list, then release lock.
        async with self._lock:
            services = list(self._services.keys())

        # Run all checks in parallel.
        tasks = [self.check_service_health(service) for service in services]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Start final payload.
        health_status = {
            "status": ServiceStatus.HEALTHY,
            "timestamp": current_time.isoformat(),
            "services": {},
        }

        # Add each service result to payload.
        for service, result in zip(services, results):
            if isinstance(result, Exception):
                health_status["services"][service] = {
                    "status": ServiceStatus.UNHEALTHY,
                    "error": str(result),
                    "last_check": self._last_check[service].isoformat(),
                }
                health_status["status"] = ServiceStatus.DEGRADED
            else:
                health_status["services"][service] = {
                    "status": result,
                    "last_check": self._last_check[service].isoformat(),
                }
                if result != ServiceStatus.HEALTHY:
                    health_status["status"] = ServiceStatus.DEGRADED

            # Save payload in cache.
        self._cached_status = health_status
        self._last_check_time = current_time

        return health_status

    # Wait until all services are healthy or time runs out.
    async def wait_for_services(self, timeout: float = 30.0) -> bool:
        try:
            # Recheck status until timeout.
            start_time = datetime.now()
            while (datetime.now() - start_time) < timedelta(seconds=timeout):
                status = await self.check_all_services()
                if status["status"] == ServiceStatus.HEALTHY:
                    return True
                await asyncio.sleep(1)
            return False
        except Exception as e:
            # Return False if an unexpected error happens.
            logger.error(f"Error waiting for services: {e}")
            return False

    # Clear all saved health state.
    async def cleanup(self) -> None:
        # Clear state safely under lock.
        async with self._lock:
            self._services.clear()
            self._check_functions.clear()
            self._last_check.clear()
            self._timeouts.clear()
            self._retry_delays.clear()
            self._max_retries.clear()
            self._dependencies.clear()
            self._cached_status = None
            self._last_check_time = None


# Shared singleton used by API routes and startup hooks.
health_checker = HealthCheck()
