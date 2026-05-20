import os
import pathlib

# Must be set before any prometheus_client import so multiprocess mode works.
_prom_dir = pathlib.Path("prometheus_multiproc")
_prom_dir.mkdir(exist_ok=True)
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", str(_prom_dir.resolve()))

import signal
import sys
import os

# Add root directory to path so 'apps' can be resolved
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from apps.api.services.task_worker import run_worker

def handle_shutdown(signum, frame):
    print(f"\n⚡ Worker received signal {signum} — shutting down gracefully.")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

if __name__ == "__main__":
    run_worker()