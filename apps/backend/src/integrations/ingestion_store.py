import base64
from io import BytesIO

import psycopg
from psycopg.rows import dict_row

from integrations.storage import upload_file
from modules.ingestion.models.ingestion_model import DocumentElement


class ElementRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def replace_for_source(self, source_version_id, elements) -> None:
        with psycopg.connect(self.database_url) as db:
            db.execute(
                "delete from ragapp.source_elements where source_version_id=%s",
                (source_version_id,),
            )
            with db.cursor() as cursor:
                cursor.executemany(
                    "insert into ragapp.source_elements(source_version_id,element_id,"
                    "parent_element_id,category,content,page_number,coordinates,table_html,"
                    "visual_storage_key,metadata,sequence_number) "
                    "values(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s::jsonb,%s)",
                    [
                        (
                            source_version_id,
                            element.element_id,
                            element.parent_id,
                            element.category,
                            element.text,
                            element.page_number,
                            psycopg.types.json.Json(element.coordinates)
                            if element.coordinates
                            else None,
                            element.table_html,
                            element.metadata.get("image_storage_key"),
                            psycopg.types.json.Json(element.metadata),
                            sequence,
                        )
                        for sequence, element in enumerate(elements)
                    ],
                )

    def get_for_source(self, source_version_id) -> list[DocumentElement]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            rows = db.execute(
                "select element_id,parent_element_id,category,content,page_number,"
                "coordinates,table_html,visual_storage_key,metadata "
                "from ragapp.source_elements where source_version_id=%s "
                "order by sequence_number",
                (source_version_id,),
            ).fetchall()

        elements = []
        for row in rows:
            metadata = dict(row["metadata"] or {})
            if row["visual_storage_key"]:
                metadata["image_storage_key"] = row["visual_storage_key"]
            elements.append(
                DocumentElement(
                    element_id=row["element_id"],
                    text=row["content"],
                    category=row["category"],
                    page_number=row["page_number"],
                    parent_id=row["parent_element_id"],
                    coordinates=row["coordinates"],
                    table_html=row["table_html"],
                    metadata=metadata,
                )
            )
        return elements


class ElementAssetStore:
    def __init__(self, storage_dir: str) -> None:
        self.storage_dir = storage_dir

    def save_base64(self, source_id, element_id, payload, content_type) -> str:
        extension = content_type.split("/")[-1].replace("jpeg", "jpg")
        key = f"elements/{source_id}/{element_id}.{extension}"
        return upload_file(key, BytesIO(base64.b64decode(payload)), content_type, self.storage_dir)


class ChunkRepository:
    def __init__(self, database_url: str, provider: str, model_name: str) -> None:
        self.database_url = database_url
        self.provider = provider
        self.model_name = model_name

    def replace_for_source(self, project_id, source_version_id, chunks, embeddings) -> None:
        if chunks and not embeddings:
            raise ValueError("Embedding provider returned no vectors")
        dimensions = len(embeddings[0]) if embeddings else None
        if any(len(vector) != dimensions for vector in embeddings):
            raise ValueError("Embedding provider returned inconsistent vector dimensions")

        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            db.execute("delete from ragapp.chunks where source_version_id=%s", (source_version_id,))
            model_id = None
            if dimensions:
                model_id = db.execute(
                    "insert into ragapp.embedding_models(provider,model_name,dimensions) "
                    "values(%s,%s,%s) on conflict(provider,model_name,dimensions) "
                    "do update set is_active=true returning id",
                    (self.provider, self.model_name, dimensions),
                ).fetchone()["id"]
            for chunk, vector in zip(chunks, embeddings, strict=True):
                row = db.execute(
                    "insert into ragapp.chunks(id,project_id,knowledge_base_id,source_id,"
                    "source_version_id,position,content,page_from,page_to,metadata) "
                    "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id",
                    (
                        chunk.id,
                        project_id,
                        chunk.knowledge_base_id,
                        chunk.source_id,
                        source_version_id,
                        chunk.position,
                        chunk.text,
                        chunk.page_number,
                        chunk.page_number,
                        psycopg.types.json.Json(chunk.metadata),
                    ),
                ).fetchone()
                db.execute(
                    "insert into ragapp.chunk_elements(chunk_id,source_element_id,element_order) "
                    "select %s,id,0 from ragapp.source_elements "
                    "where source_version_id=%s and element_id=%s",
                    (row["id"], source_version_id, chunk.element_ids[0]),
                )
                db.execute(
                    "insert into ragapp.chunk_embeddings(chunk_id,embedding_model_id,embedding) "
                    "values(%s,%s,%s::vector)",
                    (
                        row["id"],
                        model_id,
                        "[" + ",".join(str(float(value)) for value in vector) + "]",
                    ),
                )
