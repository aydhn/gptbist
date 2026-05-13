import time
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.runtime.models import (
    RuntimeScheduleConfig, RuntimePipelineConfig, RuntimePipelineResult, RuntimePipelineStatus
)

class RuntimeScheduler:
    def __init__(self, orchestrator, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        self.orchestrator = orchestrator
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

    def run_loop(self, config: RuntimeScheduleConfig, pipeline_config: RuntimePipelineConfig) -> List[RuntimePipelineResult]:
        results = []
        iterations = 0
        last_run = None

        self.logger.info(f"Starting scheduler loop. Interval: {config.interval_minutes}m. Stop on failure: {config.stop_on_failure}")

        if config.run_immediately:
            self.logger.info("Running immediately as requested.")
            res = self.orchestrator.run_once(pipeline_config)
            results.append(res)
            last_run = datetime.utcnow()
            iterations += 1
            if config.stop_on_failure and res.status == RuntimePipelineStatus.FAILED:
                self.logger.error("Pipeline failed and stop_on_failure is set. Exiting loop.")
                return results

        while True:
            if config.max_iterations and iterations >= config.max_iterations:
                self.logger.info(f"Reached max iterations ({config.max_iterations}). Exiting loop.")
                break

            if self.should_run_now(last_run, config.interval_minutes):
                self.logger.info("Interval reached. Running pipeline.")
                try:
                    res = self.orchestrator.run_once(pipeline_config)
                    results.append(res)
                    last_run = datetime.utcnow()
                    iterations += 1

                    if config.stop_on_failure and res.status == RuntimePipelineStatus.FAILED:
                        self.logger.error("Pipeline failed and stop_on_failure is set. Exiting loop.")
                        break
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt received. Stopping scheduler.")
                    break
                except Exception as e:
                    self.logger.error(f"Unexpected error in scheduler loop: {e}")
                    if config.stop_on_failure:
                        break

            # Small sleep step
            try:
                time.sleep(config.sleep_seconds)
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt during sleep. Stopping scheduler.")
                break

        return results

    def next_run_time(self, last_run: Optional[datetime], interval_minutes: int) -> datetime:
        if not last_run:
            return datetime.utcnow()
        return last_run + timedelta(minutes=interval_minutes)

    def should_run_now(self, last_run: Optional[datetime], interval_minutes: int, now: Optional[datetime] = None) -> bool:
        if not last_run:
            return True
        now = now or datetime.utcnow()
        return now >= self.next_run_time(last_run, interval_minutes)

    def build_default_schedule_config(self) -> RuntimeScheduleConfig:
        return RuntimeScheduleConfig(
            enabled=self.settings.RUNTIME_SCHEDULER_ENABLED,
            interval_minutes=self.settings.RUNTIME_INTERVAL_MINUTES,
            run_immediately=self.settings.RUNTIME_RUN_IMMEDIATELY,
            max_iterations=self.settings.RUNTIME_MAX_ITERATIONS,
            sleep_seconds=self.settings.RUNTIME_SLEEP_SECONDS,
            stop_on_failure=self.settings.RUNTIME_STOP_ON_FAILURE
        )
