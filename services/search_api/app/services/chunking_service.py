import uuid
import logging
from typing import List

import nltk
from nltk.tokenize import sent_tokenize

from app.models.chunk import Chunk

# Ensure tokenizer is available (safe to call multiple times)
nltk.download("punkt", quiet=True)

logger = logging.getLogger(__name__)


class ChunkingService:
    def __init__(self, chunk_size: int = 300):
        """
        :param chunk_size: Approximate number of words per chunk
        """
        self.chunk_size = chunk_size

    def chunk_text(self, document_id: str, text: str) -> List[Chunk]:
        """
        Splits text into sentence-aware chunks for semantic search.

        :param document_id: ID of the parent document
        :param text: Raw document text
        :return: List of Chunk objects
        """

        if not text or not text.strip():
            logger.warning(f"Empty text received for document_id={document_id}. Skipping chunking.")
            return []

        sentences = sent_tokenize(text)

        chunks: List[Chunk] = []
        current_chunk_sentences: List[str] = []
        current_word_count = 0
        index = 0

        for sentence in sentences:
            sentence_word_count = len(sentence.split())

            # If adding this sentence exceeds chunk size, flush current chunk
            if current_word_count + sentence_word_count > self.chunk_size:
                chunks.append(
                    Chunk(
                        chunk_id=str(uuid.uuid4()),
                        document_id=document_id,
                        content=" ".join(current_chunk_sentences),
                        index=index,
                    )
                )
                index += 1
                current_chunk_sentences = []
                current_word_count = 0

            current_chunk_sentences.append(sentence)
            current_word_count += sentence_word_count

        # Flush remaining sentences as final chunk
        if current_chunk_sentences:
            chunks.append(
                Chunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    content=" ".join(current_chunk_sentences),
                    index=index,
                )
            )

        logger.info(f"Chunked document_id={document_id} into {len(chunks)} chunks")

        return chunks
