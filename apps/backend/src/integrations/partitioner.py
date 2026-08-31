import json
import mimetypes
import time
from pathlib import Path
from typing import Any

import unstructured_client
from unstructured_client.models import operations, shared

from modules.ingestion.models.ingestion_model import DocumentElement


class UnstructuredPartitioner:
    """Outbound adapter for Unstructured Transform jobs."""

    def __init__(
        self,
        api_key: str,
        api_url: str | None = None,
        strategy: str = "auto",
        pdf_strategy: str = "hi_res",
        ocr_languages: list[str] | None = None,
        poll_interval_seconds: float = 5.0,
        timeout_seconds: float = 900.0,
        chunking_strategy: str = "by_title",
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("UNSTRUCTURED_API_KEY is required")

        self._strategy = strategy
        self._pdf_strategy = pdf_strategy
        self._ocr_languages = ocr_languages or ["eng"]
        self._poll_interval_seconds = poll_interval_seconds
        self._timeout_seconds = timeout_seconds
        self._chunking_strategy = chunking_strategy
        sdk_url = api_url.rstrip("/").removesuffix("/api/v1") if api_url else None
        self._client = client or unstructured_client.UnstructuredClient(
            api_key_auth=api_key,
            server_url=sdk_url,
        )

    def partition(self, path: Path) -> list[DocumentElement]:
        with path.open("rb") as document:
            response = self._client.jobs.create_job(
                request=operations.CreateJobRequest(
                    body_create_job=shared.BodyCreateJob(
                        request_data=json.dumps(self._job_configuration()),
                        input_files=[
                            shared.InputFiles(
                                content=document.read(),
                                fileName=path.name,
                                content_type=mimetypes.guess_type(path.name)[0]
                                or "application/octet-stream",
                            )
                        ],
                    )
                )
            )

        job = response.job_information
        if job is None or not job.id:
            raise RuntimeError("Unstructured did not return a job ID")
        completed_job = self._wait_for_job(str(job.id))
        raw_elements: list[Any] = []
        for output in completed_job.output_node_files or []:
            downloaded = self._client.jobs.download_job_output(
                request=operations.DownloadJobOutputRequest(
                    job_id=str(job.id), file_id=str(output.file_id)
                )
            )
            raw_elements.extend(self._elements_from_output(downloaded.any))
        if not raw_elements:
            raise RuntimeError("Unstructured job completed without document elements")
        return [self._convert(element) for element in raw_elements]

    def _job_configuration(self) -> dict[str, Any]:
        return {
            "job_nodes": [
                {
                    "name": "Partitioner",
                    "type": "partition",
                    "subtype": "vlm",
                    "settings": {
                        "is_dynamic": True,
                        "allow_fast": True,
                    },
                },
                {
                    "name": "Chunker",
                    "type": "chunk",
                    "subtype": "chunk_by_title" if self._chunking_strategy in {"by_title", "element"} else "chunk_basic",
                    "settings": {
                        "max_characters": 2000,
                        "new_after_n_chars": 1500,
                        "combine_text_under_n_chars": 200,
                    },
                },
            ]
        }

    def _wait_for_job(self, job_id: str):
        deadline = time.monotonic() + self._timeout_seconds
        while time.monotonic() < deadline:
            response = self._client.jobs.get_job(request={"job_id": job_id})
            job = response.job_information
            if job is None:
                raise RuntimeError(f"Unstructured job {job_id} returned no status")
            status = str(getattr(job.status, "value", job.status)).upper()
            if status == "COMPLETED":
                return job
            if status in {"FAILED", "STOPPED", "CANCELED", "CANCELLED"}:
                raise RuntimeError(f"Unstructured job {job_id} ended with status {status}")
            time.sleep(self._poll_interval_seconds)
        raise TimeoutError(f"Unstructured job {job_id} exceeded {self._timeout_seconds:g} seconds")

    @staticmethod
    def _elements_from_output(value: Any) -> list[Any]:
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        if isinstance(value, str):
            value = json.loads(value)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            for key in ("elements", "data", "result"):
                if isinstance(value.get(key), list):
                    return value[key]
        raise ValueError("Unstructured output did not contain an element array")

    @staticmethod
    def _convert(element: Any) -> DocumentElement:
        if isinstance(element, dict):
            element_data = element
        elif hasattr(element, "model_dump"):
            element_data = element.model_dump()
        else:
            element_data = vars(element)

        metadata = dict(element_data.get("metadata") or {})
        return DocumentElement(
            element_id=str(element_data.get("element_id") or element_data.get("id")),
            text=str(element_data.get("text") or ""),
            category=str(
                element_data.get("type") or element_data.get("category") or "UncategorizedText"
            ),
            page_number=metadata.pop("page_number", None),
            parent_id=metadata.pop("parent_id", None),
            coordinates=metadata.pop("coordinates", None),
            table_html=metadata.pop("text_as_html", None),
            image_payload=metadata.pop("image_base64", None),
            image_mime_type=metadata.pop("image_mime_type", None),
            metadata=metadata,
        )
