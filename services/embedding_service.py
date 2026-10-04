import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_model_instance = None
_model_failed = False

def get_sentence_transformer_model():
    global _model_instance, _model_failed
    if _model_failed:
        return None
    if _model_instance is not None:
        return _model_instance
    try:
        from sentence_transformers import SentenceTransformer
        _model_instance = SentenceTransformer("all-MiniLM-L6-v2")
        return _model_instance
    except Exception:
        _model_failed = True
        return None

def compute_tfidf_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0
    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=5000)
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(np.clip(sim, 0.0, 1.0))
    except Exception:
        t1_words = set(text1.lower().split())
        t2_words = set(text2.lower().split())
        if not t1_words or not t2_words:
            return 0.0
        overlap = len(t1_words.intersection(t2_words))
        return float(overlap / max(len(t1_words), len(t2_words), 1))

def compute_semantic_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0
    
    clean_t1 = text1.strip()
    clean_t2 = text2.strip()
    if not clean_t1 or not clean_t2:
        return 0.0

    model = get_sentence_transformer_model()
    if model is not None:
        try:
            embeddings = model.encode([clean_t1, clean_t2], convert_to_numpy=True, normalize_embeddings=True)
            dot_prod = float(np.dot(embeddings[0], embeddings[1]))
            if dot_prod < 0.22:
                score = max(dot_prod, 0.0) * 0.4
            else:
                score = 0.088 + ((dot_prod - 0.22) / 0.78) * 0.912
            return float(np.clip(score, 0.0, 1.0))
        except Exception:
            pass

    return compute_tfidf_similarity(clean_t1, clean_t2)

def compute_batch_similarity(query_text, text_list):
    if not query_text or not text_list:
        return [0.0] * len(text_list)

    model = get_sentence_transformer_model()
    if model is not None:
        try:
            query_emb = model.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)
            doc_embs = model.encode(text_list, convert_to_numpy=True, normalize_embeddings=True)
            similarities = np.dot(doc_embs, query_emb[0])
            normalized = []
            for s in similarities:
                val = float(s)
                if val < 0.22:
                    sc = max(val, 0.0) * 0.4
                else:
                    sc = 0.088 + ((val - 0.22) / 0.78) * 0.912
                normalized.append(float(np.clip(sc, 0.0, 1.0)))
            return normalized
        except Exception:
            pass

    results = []
    for item in text_list:
        results.append(compute_tfidf_similarity(query_text, item))
    return results
