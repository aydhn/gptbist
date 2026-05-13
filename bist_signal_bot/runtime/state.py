import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.runtime.models import RuntimeState, RuntimePipelineResult, RuntimePipelineStatus
from bist_signal_bot.storage.paths import get_runtime_dir

class RuntimeStateStore:
    def __init__(self, settings: Optional[Settings] = None, base_dir: Optional[Path] = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir or get_runtime_dir(self.settings)
        self.state_file = self.base_dir / self.settings.RUNTIME_STATE_FILE_NAME
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> RuntimeState:
        if not self.state_file.exists():
            return RuntimeState()
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return RuntimeState(**data)
        except Exception:
            return RuntimeState()

    def save(self, state: RuntimeState) -> Path:
        state.updated_at = datetime.utcnow()
        tmp_file = self.state_file.with_suffix('.tmp')
        with open(tmp_file, 'w', encoding='utf-8') as f:
            f.write(state.model_dump_json(indent=2))
        tmp_file.replace(self.state_file)
        return self.state_file

    def update_from_result(self, result: RuntimePipelineResult) -> RuntimeState:
        state = self.load()
        state.last_run_id = result.run_id
        state.last_finished_at = result.finished_at
        state.last_status = result.status
        state.is_running = False
        state.active_lock_id = None

        state.total_runs += 1
        if result.status == RuntimePipelineStatus.SUCCESS:
            state.success_runs += 1
            state.consecutive_failures = 0
        else:
            state.failed_runs += 1
            state.consecutive_failures += 1

        self.save(state)
        return state

    def mark_running(self, run_id: str, lock_id: str) -> RuntimeState:
        state = self.load()
        state.last_run_id = run_id
        state.last_started_at = datetime.utcnow()
        state.is_running = True
        state.active_lock_id = lock_id
        self.save(state)
        return state

    def mark_finished(self, result: RuntimePipelineResult) -> RuntimeState:
        return self.update_from_result(result)

    def reset_state(self) -> RuntimeState:
        state = RuntimeState()
        self.save(state)
        return state
