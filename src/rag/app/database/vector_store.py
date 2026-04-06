import logging
import time
from datetime import datetime
from typing import Any, List, Optional, Tuple, Union

import pandas as pd
import psycopg2
from config.settings import get_settings
from sentence_transformers import SentenceTransformer
from timescale_vector import client


class VectorStore:
    """A class for managing vector operations and database interactions."""

    def __init__(self):
        """Initialize the VectorStore with settings, multilingual bert client, and Timescale Vector client."""
        self.settings = get_settings()
        self.embedding_model = SentenceTransformer("intfloat/multilingual-e5-base")
        self.vector_settings = self.settings.vector_store
        self.vec_client = client.Sync(
            self.settings.database.service_url,
            self.vector_settings.table_name,
            self.vector_settings.embedding_dimensions,
            time_partition_interval=self.vector_settings.time_partition_interval,
        )

    def get_embedding(self, text: str) -> List[float]:
        text = text.replace("\n", " ")
        start_time = time.time()
        embedding = self.embedding_model.encode(text)
        elapsed_time = time.time() - start_time
        logging.info(f"Embedding generated in {elapsed_time:.3f} seconds")
        return embedding

    def create_tables(self) -> None:
        """Create the table manually using raw psycopg2."""
        logging.info(f"Creating table {self.vector_settings.table_name}...")

        conn = psycopg2.connect(self.settings.database.service_url)
        try:
            with conn.cursor() as cur:
                table_name = self.vector_settings.table_name
                dim = self.vector_settings.embedding_dimensions

                # Create table
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS "{table_name}" (
                        id uuid PRIMARY KEY,
                        metadata JSONB,
                        contents TEXT,
                        embedding VECTOR({dim})
                    );
                """)
                conn.commit()
            logging.info("Table created successfully.")
        finally:
            conn.close()

    def create_index(self) -> None:
        logging.info(f"Creating HNSW index on {self.vector_settings.table_name}...")

        conn = psycopg2.connect(self.settings.database.service_url)
        try:
            with conn.cursor() as cur:
                table_name = self.vector_settings.table_name
                # We name the index 'idx_embeddings_hnsw'
                # We use cosine similarity (vector_cosine_ops) which is best for E5 models
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS "{table_name}_hnsw_idx"
                    ON "{table_name}"
                    USING hnsw (embedding vector_cosine_ops);
                """)
                conn.commit()
            logging.info("HNSW Index created successfully.")
        except Exception as e:
            logging.error(f"Error creating index: {e}")
            raise
        finally:
            conn.close()

    def drop_index(self) -> None:
        """Drop the index in the database"""
        self.vec_client.drop_embedding_index()

    def upsert(self, df: pd.DataFrame) -> None:
        """Insert or update records in the database from a pandas DataFrame."""
        records = df.to_records(index=False)
        self.vec_client.upsert(list(records))
        logging.info(
            f"Inserted {len(df)} records into {self.vector_settings.table_name}"
        )

    def search(
        self,
        query_text: str,
        limit: int = 5,
        metadata_filter: Union[dict, List[dict]] = None,
        predicates: Optional[client.Predicates] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        return_dataframe: bool = True,
    ) -> Union[List[Tuple[Any, ...]], pd.DataFrame]:
        query_embedding = self.get_embedding(query_text)
        start_time = time.time()
        search_args = {"limit": limit}
        if metadata_filter:
            search_args["filter"] = metadata_filter
        if predicates:
            search_args["predicates"] = predicates
        if time_range:
            start_date, end_date = time_range
            search_args["uuid_time_filter"] = client.UUIDTimeRange(start_date, end_date)

        results = self.vec_client.search(query_embedding, **search_args)
        elapsed_time = time.time() - start_time
        logging.info(f"Vector search completed in {elapsed_time:.3f} seconds")

        if return_dataframe:
            return self._create_dataframe_from_results(results)
        else:
            return results

    def _create_dataframe_from_results(
        self, results: List[Tuple[Any, ...]]
    ) -> pd.DataFrame:
        df = pd.DataFrame(
            results, columns=["id", "metadata", "content", "embedding", "distance"]
        )
        df = pd.concat(
            [df.drop(["metadata"], axis=1), df["metadata"].apply(pd.Series)], axis=1
        )
        df["id"] = df["id"].astype(str)
        return df

    def delete(
        self,
        ids: List[str] = None,
        metadata_filter: dict = None,
        delete_all: bool = False,
    ) -> None:
        if sum(bool(x) for x in (ids, metadata_filter, delete_all)) != 1:
            raise ValueError(
                "Provide exactly one of: ids, metadata_filter, or delete_all"
            )
        if delete_all:
            self.vec_client.delete_all()
        elif ids:
            self.vec_client.delete_by_ids(ids)
        elif metadata_filter:
            self.vec_client.delete_by_metadata(metadata_filter)
