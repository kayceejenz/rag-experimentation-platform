from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ObjectStore:
    bucket: str
    client: Any


def _object_store() -> ObjectStore | None:
    if os.environ.get("APP_ENV", "development").strip().lower() == "development":
        return None

    required = (
        "R2_API",
        "R2_BUCKET_NAME",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
    )
    if all(os.environ.get(name) for name in required):
        import boto3

        return ObjectStore(
            bucket=os.environ["R2_BUCKET_NAME"],
            client=boto3.client(
                "s3",
                endpoint_url=os.environ["R2_API"],
                aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                region_name="auto",
            ),
        )
    return None


def resolve_file(storage_key: str, storage_dir: str) -> tuple[Path, bool]:
    key_path = Path(storage_key)
    if key_path.is_absolute():
        local_path = key_path
        parts = key_path.parts
        for index in range(len(parts) - 1):
            if parts[index : index + 2] == ("storage", "sources"):
                relative_key = Path(*parts[index + 2 :])
                local_path = Path(storage_dir).resolve() / relative_key
                break
    else:
        local_path = Path(storage_dir).resolve() / key_path

    store = _object_store()
    if local_path.exists() or store is None:
        return local_path, False

    suffix = Path(storage_key).suffix or ".bin"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        logger.debug("Downloading %s from object store bucket %s", storage_key, store.bucket)
        store.client.download_fileobj(store.bucket, storage_key, tmp)
        tmp.flush()
        tmp.close()
        logger.debug("Downloaded to %s", tmp.name)
        return Path(tmp.name), True
    except Exception:
        tmp.close()
        Path(tmp.name).unlink(missing_ok=True)
        raise


def cleanup_temp(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to delete temp file %s: %s", path, exc)


def upload_file(storage_key: str, source: BinaryIO, content_type: str, storage_dir: str) -> str:
    store = _object_store()
    if store is not None:
        store.client.upload_fileobj(
            source,
            store.bucket,
            storage_key,
            ExtraArgs={"ContentType": content_type},
        )
        return storage_key

    target_dir = Path(storage_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / storage_key
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as output:
        while chunk := source.read(1024 * 1024):
            output.write(chunk)
    return storage_key


def delete_file(storage_key: str, storage_dir: str = "storage/sources") -> None:
    store = _object_store()
    if store is not None:
        store.client.delete_object(Bucket=store.bucket, Key=storage_key)
        return
    path = Path(storage_key)
    if not path.is_absolute():
        path = Path(storage_dir).resolve() / path
    path.unlink(missing_ok=True)
