from collections.abc import Callable, Mapping

class Job:
    id: str

class BackgroundScheduler:
    running: bool

    def __init__(
        self,
        *,
        jobstores: Mapping[str, object] | None = ...,
        executors: Mapping[str, object] | None = ...,
        job_defaults: Mapping[str, object] | None = ...,
        timezone: object | None = ...,
    ) -> None: ...
    def add_job(
        self,
        func: Callable[..., object],
        trigger: object | None = ...,
        args: tuple[object, ...] | None = ...,
        kwargs: dict[str, object] | None = ...,
        id: str | None = ...,
        name: str | None = ...,
        misfire_grace_time: int | None = ...,
        coalesce: bool | None = ...,
        max_instances: int | None = ...,
        next_run_time: object | None = ...,
        jobstore: str = ...,
        executor: str = ...,
        replace_existing: bool = ...,
        **trigger_args: object,
    ) -> Job: ...
    def start(self) -> None: ...
    def shutdown(self, wait: bool = ...) -> None: ...
    def get_jobs(self) -> list[Job]: ...
    def remove_job(self, job_id: str) -> None: ...
