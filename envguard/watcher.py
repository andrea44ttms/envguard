"""Watch a .env file for changes and re-validate on modification."""

import os
import time
import threading
from typing import Callable, Optional

from envguard.loader import load_env_file
from envguard.schema import EnvSchema
from envguard.validator import EnvValidator
from envguard.result import ValidationResult


class EnvWatcher:
    """Watches a .env file and triggers a callback when it changes."""

    def __init__(
        self,
        env_path: str,
        schema: EnvSchema,
        on_change: Callable[[ValidationResult], None],
        poll_interval: float = 1.0,
    ) -> None:
        self.env_path = env_path
        self.schema = schema
        self.on_change = on_change
        self.poll_interval = poll_interval

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_mtime: Optional[float] = self._get_mtime()

    def _get_mtime(self) -> Optional[float]:
        try:
            return os.path.getmtime(self.env_path)
        except FileNotFoundError:
            return None

    def _validate(self) -> ValidationResult:
        env = load_env_file(self.env_path)
        validator = EnvValidator(self.schema)
        return validator.validate(env)

    def _poll(self) -> None:
        while not self._stop_event.is_set():
            current_mtime = self._get_mtime()
            if current_mtime != self._last_mtime:
                self._last_mtime = current_mtime
                result = self._validate()
                self.on_change(result)
            time.sleep(self.poll_interval)

    def start(self) -> None:
        """Start watching the file in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background watcher thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.poll_interval * 2)
            self._thread = None

    def is_running(self) -> bool:
        """Return True if the watcher thread is active."""
        return self._thread is not None and self._thread.is_alive()
