import argparse
import asyncio

from core.settings import Settings
from integrations.database import (
    close_database_pools,
    configure_database_pools,
    open_database_pools,
)
from integrations.http_client import close_http_clients
from modules.ingestion.services.ingestion_worker import run_once
from modules.experiments.services.experiment_runner import run_once as run_experiment_once


async def run_worker(config: Settings, once: bool) -> None:
    try:
        if config.database_url:
            await open_database_pools(config.database_url)
        while True:
            processed = await run_experiment_once(config)
            if not processed:
                processed = await asyncio.to_thread(run_once, config)
            if once or not config.has_database:
                break
            if not processed:
                await asyncio.sleep(config.worker_poll_interval_seconds)
    finally:
        await close_database_pools()
        await close_http_clients()


def main() -> None:
    parser = argparse.ArgumentParser(description="RagApp knowledge ingestion worker")
    parser.add_argument("--once", action="store_true", help="Process one job and exit.")
    args = parser.parse_args()
    config = Settings()
    configure_database_pools(
        config.database_pool_min_size,
        config.database_pool_max_size,
        config.database_pool_timeout_seconds,
    )

    asyncio.run(run_worker(config, args.once))


if __name__ == "__main__":
    main()
