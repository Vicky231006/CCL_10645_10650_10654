"""Storage adapter: local filesystem (dev) or private S3 (prod).

Object keys are always generated server-side; client-supplied keys are never trusted.
"""
from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from app.core.config import settings


class StorageAdapter:
    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> str:  # pragma: no cover
        raise NotImplementedError

    def get_bytes(self, key: str) -> bytes:  # pragma: no cover
        raise NotImplementedError

    def delete(self, key: str) -> None:  # pragma: no cover
        raise NotImplementedError

    def signed_url(self, key: str, expires_in: int = 900) -> str | None:  # pragma: no cover
        raise NotImplementedError


class LocalStorageAdapter(StorageAdapter):
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Prevent path traversal: resolve and confirm inside base_dir.
        target = (self.base_dir / key).resolve()
        if not str(target).startswith(str(self.base_dir.resolve())):
            raise ValueError("Invalid storage key")
        return target

    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def get_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def signed_url(self, key: str, expires_in: int = 900) -> str | None:
        # Local dev has no signed URLs; served through an authorising API route.
        return None


class S3StorageAdapter(StorageAdapter):
    def __init__(self) -> None:
        import boto3  # imported lazily so boto3 is optional in local dev

        self._client = boto3.client("s3", region_name=settings.s3_region)
        self._bucket = settings.s3_bucket

    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> str:
        extra = {"ContentType": content_type} if content_type else {}
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, **extra)
        return key

    def get_bytes(self, key: str) -> bytes:
        obj = self._client.get_object(Bucket=self._bucket, Key=key)
        return obj["Body"].read()

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def signed_url(self, key: str, expires_in: int = 900) -> str | None:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )


def build_storage() -> StorageAdapter:
    if settings.storage_backend == "s3" and settings.s3_bucket:
        return S3StorageAdapter()
    return LocalStorageAdapter(settings.local_storage_path)


def new_object_key(user_id: str, kind: str, filename: str) -> str:
    safe_ext = ""
    if "." in filename:
        safe_ext = "." + filename.rsplit(".", 1)[-1].lower()[:10]
    return f"{kind}/{user_id}/{uuid.uuid4().hex}{safe_ext}"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


storage = build_storage()
