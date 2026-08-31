from collections.abc import Mapping
from typing import Any

from modules.core.contracts.specification_contract import SpecificationNormalizer
from modules.core.models.specification_model import SpecificationKind


class IngestionSpecificationRegistry:
    def normalizer_for(
        self, kind: SpecificationKind, schema_version: int
    ) -> SpecificationNormalizer | None:
        if kind is SpecificationKind.PIPELINE and schema_version == 1:
            return normalize_ingestion_pipeline
        return None


def normalize_ingestion_pipeline(configuration: Mapping[str, Any]) -> dict[str, Any]:
    partitioning = _mapping(configuration, "partitioning")
    chunking = _mapping(configuration, "chunking")
    embedding = _mapping(configuration, "embedding")
    languages = partitioning.get("ocr_languages", ["eng"])
    if not isinstance(languages, list) or not all(
        isinstance(language, str) and language.strip() for language in languages
    ):
        raise ValueError("partitioning.ocr_languages must be a list of languages")
    return {
        "name": str(configuration.get("name", "Index build")).strip(),
        "partitioning": {
            "provider": str(partitioning.get("provider", "unstructured")).lower(),
            "strategy": str(partitioning.get("strategy", "auto")).lower(),
            "pdf_strategy": str(partitioning.get("pdf_strategy", "hi_res")).lower(),
            "ocr_languages": sorted({language.strip().lower() for language in languages}),
        },
        "chunking": {
            "strategy": str(chunking.get("strategy", "element")).lower(),
        },
        "embedding": {
            "provider": str(embedding["provider"]).lower(),
            "model": str(embedding["model"]),
            "dimensions": int(embedding["dimensions"]),
        },
    }


def _mapping(configuration: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = configuration.get(key, {})
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value
