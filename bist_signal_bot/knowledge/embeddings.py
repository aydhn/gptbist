import hashlib

from bist_signal_bot.config.settings import Settings


class LocalEmbeddingProvider:

    def __init__(self, settings: Settings | None = None):
        self.settings = settings
        self.dim = settings.KNOWLEDGE_FALLBACK_EMBEDDING_DIM if settings else 128
        self._st_model = None
        self._st_available = False
        self._init_model()

    def _init_model(self):
        if not self.settings or not self.settings.KNOWLEDGE_USE_LOCAL_EMBEDDINGS:
            return

        try:
            from sentence_transformers import SentenceTransformer
            if self.settings.KNOWLEDGE_ALLOW_MODEL_DOWNLOAD or self.settings.KNOWLEDGE_LOCAL_EMBEDDING_MODEL:
                model_name = self.settings.KNOWLEDGE_LOCAL_EMBEDDING_MODEL or "all-MiniLM-L6-v2"
                # If local model is specified but download is false, it assumes model is in cache
                self._st_model = SentenceTransformer(model_name)
                self._st_available = True
                self.dim = self._st_model.get_sentence_embedding_dimension()
        except ImportError:
            pass
        except Exception:
            pass

    def is_available(self) -> bool:
        return self._st_available

    def provider_name(self) -> str:
        return "sentence_transformers" if self._st_available else "fallback_hashing"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self._st_available and self._st_model:
            try:
                embeddings = self._st_model.encode(texts, convert_to_numpy=True)
                return [emb.tolist() for emb in embeddings]
            except Exception:
                pass

        # Fallback
        return [self.fallback_embedding(t) for t in texts]

    def embed_query(self, query: str) -> list[float] | None:
        if self._st_available and self._st_model:
            try:
                emb = self._st_model.encode(query, convert_to_numpy=True)
                return emb.tolist()
            except Exception:
                pass

        return self.fallback_embedding(query)

    def fallback_embedding(self, text: str) -> list[float]:
        # Deterministic hashing trick to generate a pseudo-embedding
        vec = [0.0] * self.dim
        tokens = text.lower().split()
        for token in tokens:
            h = hashlib.md5(token.encode('utf-8')).hexdigest()
            idx = int(h[:8], 16) % self.dim
            val = (int(h[8:10], 16) / 255.0) * 2.0 - 1.0 # -1.0 to 1.0
            vec[idx] += val

        # Normalize
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]

        return vec
