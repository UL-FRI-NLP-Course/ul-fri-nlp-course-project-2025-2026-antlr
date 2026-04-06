"""
This script is used for first-time database
filling from markdown files. It reads all .md files from the specified directory,
splits them based on markdown headers, generates embeddings for each chunk,
and inserts them into the vector store in batches.
"""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from database.vector_store import VectorStore
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from timescale_vector.client import uuid_from_time

# Initialize VectorStore
vec = VectorStore()
vec.create_tables()
vec.create_index()

# Read the CSV file
# df = pd.read_csv("src/rag/data/faq_dataset.csv", sep=";")

RAW_DATA_DIR = "dataset_raw"
# How many chunks to embed and insert at once
BATCH_SIZE = 50
# Max characters per chunk
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

# Setup Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_markdown_chunks(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 1. Split by Header
    headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, strip_headers=False
    )
    header_splits = header_splitter.split_text(text)

    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    final_chunks = char_splitter.split_documents(header_splits)
    return final_chunks


# Prepare data for insertion
# def prepare_record(row):
#     """Prepare a record for insertion into the vector store.

#     This function creates a record with a UUID version 1 as the ID, which captures
#     the current time or a specified time.

#     Note:
#         - By default, this function uses the current time for the UUID.
#         - To use a specific time:
#           1. Import the datetime module.
#           2. Create a datetime object for your desired time.
#           3. Use uuid_from_time(your_datetime) instead of uuid_from_time(datetime.now()).

#         Example:
#             from datetime import datetime
#             specific_time = datetime(2023, 1, 1, 12, 0, 0)
#             id = str(uuid_from_time(specific_time))

#         This is useful when your content already has an associated datetime.
#     """
#     content = f"Question: {row['question']}\nAnswer: {row['answer']}"
#     embedding = vec.get_embedding(content)
#     return pd.Series(
#         {
#             "id": str(uuid_from_time(datetime.now())),
#             "metadata": {
#                 "created_at": datetime.now().isoformat(),
#             },
#             "contents": content,
#             "embedding": embedding,
#         }
#     )


# records_df = df.apply(prepare_record, axis=1)
# vec.upsert(records_df)


raw_path = Path(RAW_DATA_DIR)
all_md_files = list(raw_path.glob("**/*.md"))
records_to_upsert = []

for file_count, md_file in enumerate(all_md_files, 1):
    logging.info(f"[{file_count}/{len(all_md_files)}] Processing: {md_file.name}")

    try:
        # chunks is now a list of Document objects
        chunks = get_markdown_chunks(md_file)

        for i, doc in enumerate(chunks):
            content = doc.page_content

            # Combine original header info with file info
            db_metadata = {
                "source": str(md_file.name),
                "chunk_id": i,
                "created_at": datetime.now().isoformat(),
                **doc.metadata,  # Headers found by the splitter
            }

            embedding_input = f"File: {md_file.name}\nContent: {content}"
            embedding = vec.get_embedding(embedding_input)

            records_to_upsert.append(
                {
                    "id": str(uuid_from_time(datetime.now())),
                    "metadata": db_metadata,
                    "contents": content,
                    "embedding": embedding,
                }
            )

            if len(records_to_upsert) >= BATCH_SIZE:
                vec.upsert(pd.DataFrame(records_to_upsert))
                records_to_upsert = []

    except Exception as e:
        logging.error(f"Failed to process {md_file}: {e}")

if records_to_upsert:
    vec.upsert(pd.DataFrame(records_to_upsert))
logging.info("Ingestion complete!")
