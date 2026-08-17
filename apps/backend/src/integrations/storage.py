from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import BinaryIO

logger = logging.getLogger(__name__)


def _use_r2() -> bool:
    if os.environ.get("APP_ENV", "development").strip().lower() == "development":
        return False

    required = (
        "R2_API",
        "R2_BUCKET_NAME",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
    )
    return all(os.environ.get(name) for name in required)


def _r2_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_API"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


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

    if local_path.exists() or not _use_r2():
        return local_path, False

    bucket = os.environ["R2_BUCKET_NAME"]
    suffix = Path(storage_key).suffix or ".bin"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        logger.debug("Downloading %s from R2 bucket %s", storage_key, bucket)
        _r2_client().download_fileobj(bucket, storage_key, tmp)
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
    if _use_r2():
        _r2_client().upload_fileobj(
            source,
            os.environ["R2_BUCKET_NAME"],
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
    if _use_r2():
        _r2_client().delete_object(Bucket=os.environ["R2_BUCKET_NAME"], Key=storage_key)
        return
    path = Path(storage_key)
    if not path.is_absolute():
        path = Path(storage_dir).resolve() / path
    path.unlink(missing_ok=True)
