import argparse
import time

from core.settings import Settings
from modules.ingestion.services.ingestion_worker import run_once


def main() -> None:
    parser = argparse.ArgumentParser(description="RagApp knowledge ingestion worker")
    parser.add_argument("--once", action="store_true", help="Process one job and exit.")
    args = parser.parse_args()
    config = Settings()

    while True:
        processed = run_once(config)
        if args.once or not config.has_database:
            break
        if not processed:
            time.sleep(config.worker_poll_interval_seconds)


if __name__ == "__main__":
    main()
