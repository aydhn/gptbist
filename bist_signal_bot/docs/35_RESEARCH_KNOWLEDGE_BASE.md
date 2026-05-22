# Local Research Knowledge Base

## Overview
The Research Knowledge Base provides a local, offline memory layer for the BIST Signal Bot. It indexes research ledger events, review decisions, backtests, and reports, making them searchable via keyword, BM25-lite, and optional local embeddings.

This layer allows the bot to answer:
- "What did we decide for ASELS last time?"
- "What is the historical performance context of this strategy?"

## Safety & Constraints
- **Research Only**: All knowledge search results are historical context and DO NOT constitute investment advice.
- **No Real Orders**: The Knowledge Base cannot and will not execute real market orders.
- **No Cloud/Paid APIs**: Everything runs locally. We do not use OpenAI API or cloud vector databases (Pinecone, etc.).
- **Redaction**: All incoming texts undergo secret redaction to prevent tokens/keys from being indexed. Unsafe claims are guarded.

## Architecture
1. **Source Collector**: Reads from offline JSONL logs (Research Ledger, Decision Journal).
2. **Text Normalizer**: Cleans text, handles Turkish characters, extracts terms.
3. **Chunker**: Splits large documents into overlapping token-aware chunks.
4. **Local Embedding Provider**: Falls back to deterministic hashing/TF-IDF lite if SentenceTransformers is unavailable. No automated downloading unless explicitly allowed.
5. **Search Engine**: Supports KEYWORD, BM25_LITE, EMBEDDING, HYBRID, and AUTO modes.
6. **Similarity Engine & Case Library**: Finds similar past signals and groups outcome patterns.
7. **Analyst Memory**: Creates synthesized "Memory Cards" with lessons, patterns, and risks.

## CLI Usage

Build the index incrementally:
```bash
python -m bist_signal_bot kb index --incremental
```

Search for a case:
```bash
python -m bist_signal_bot kb search "ASELS momentum" --mode BM25_LITE
```

Find similar cases:
```bash
python -m bist_signal_bot kb similar --symbol ASELS
```

Generate a memory card:
```bash
python -m bist_signal_bot kb memory --symbol ASELS --save
```

Clear the index (requires confirmation):
```bash
python -m bist_signal_bot kb clear-index --confirm
```

## Backup & Maintenance
Knowledge index files (`data/knowledge/`) are included in standard backup scopes. Corrupted indexes can be rebuilt from source JSONL files using `kb index --rebuild --confirm`.
