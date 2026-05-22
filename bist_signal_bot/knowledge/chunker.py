import uuid
import re

from bist_signal_bot.knowledge.models import KnowledgeDocument, KnowledgeChunk


class KnowledgeChunker:

    def chunk_document(self, document: KnowledgeDocument, chunk_size: int = 800, overlap: int = 100) -> list[KnowledgeChunk]:
        if not document.text:
            return []

        if self.estimate_tokens(document.text) <= chunk_size:
            return [
                KnowledgeChunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document.document_id,
                    chunk_index=0,
                    text=document.text,
                    token_estimate=self.estimate_tokens(document.text),
                    symbol=document.symbol,
                    strategy_name=document.strategy_name,
                    source_type=document.source_type,
                    tags=document.tags,
                    metadata={"full_doc": True}
                )
            ]

        sentences = self.split_sentences(document.text)
        merged_blocks = self.merge_sentences(sentences, chunk_size, overlap)

        chunks = []
        for i, block in enumerate(merged_blocks):
            chunks.append(
                KnowledgeChunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document.document_id,
                    chunk_index=i,
                    text=block,
                    token_estimate=self.estimate_tokens(block),
                    symbol=document.symbol,
                    strategy_name=document.strategy_name,
                    source_type=document.source_type,
                    tags=document.tags,
                    metadata={"is_chunk": True, "total_chunks": len(merged_blocks)}
                )
            )

        return chunks

    def estimate_tokens(self, text: str) -> int:
        # Simple heuristic: words / 0.75
        words = len(re.findall(r'\w+', text))
        return int(words / 0.75) + 1

    def split_sentences(self, text: str) -> list[str]:
        # Basic split on punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def merge_sentences(self, sentences: list[str], chunk_size: int, overlap: int) -> list[str]:
        blocks = []
        current_block = []
        current_size = 0

        for sentence in sentences:
            sentence_size = self.estimate_tokens(sentence)
            if current_size + sentence_size > chunk_size and current_block:
                blocks.append(" ".join(current_block))
                # Backtrack for overlap
                overlap_size = 0
                overlap_block = []
                for s in reversed(current_block):
                    s_size = self.estimate_tokens(s)
                    if overlap_size + s_size > overlap:
                        break
                    overlap_block.insert(0, s)
                    overlap_size += s_size

                current_block = overlap_block
                current_size = overlap_size

            current_block.append(sentence)
            current_size += sentence_size

        if current_block:
            blocks.append(" ".join(current_block))

        return blocks
