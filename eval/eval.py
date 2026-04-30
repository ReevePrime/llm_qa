import chromadb
import openai
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder


load_dotenv()

CHROMA_PATH = "../chroma_data"
COLLECTION_NAME = "openai_embeddings"
EMBEDDING_MODEL = "text-embedding-3-small"
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def initialize():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME)
    return collection


def embed_queries(test_queries):
    for query in test_queries:
        response = openai.embeddings.create(
            input=query["query"],
            model=EMBEDDING_MODEL
        )
        query["embedding"] = response.data[0].embedding


def check_results(test_queries, collection):
    hits = 0
    for query in test_queries:
        results = collection.query(
            query_embeddings=[query["embedding"]],
            n_results=5
        )
        retrieved_docs = results["documents"][0]
        hit = any(query["expected_substring"] in doc for doc in retrieved_docs)
        status = "HIT" if hit else "MISS"
        if hit:
            hits += 1
        print(f"[{status}] {query['query']}")

    total = len(test_queries)
    print(f"\nHit rate: {hits}/{total} = {hits / total:.0%}")




def build_bm25_index(texts):
    tokenised = [text.lower().split() for text in texts]
    return BM25Okapi(tokenised)


def reciprocal_rank_fusion(vector_ids, bm25_ids, k=60):
    scores = {}
    for rank, chunk_id in enumerate(vector_ids):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
    for rank, chunk_id in enumerate(bm25_ids):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
    return sorted(scores, key=lambda x: scores[x], reverse=True)


def hybrid_retrieve(query, collection, bm25_index, chunk_ids, top_k=5, candidate_k=20):
    # --- Vector search ---
    response = openai.embeddings.create(input=query, model=EMBEDDING_MODEL)
    vector_results = collection.query(
        query_embeddings=[response.data[0].embedding],
        n_results=candidate_k
    )
    vector_ids = vector_results["ids"][0]

    # --- BM25 search ---
    query_tokens = query.lower().split()
    bm25_scores = bm25_index.get_scores(query_tokens)

    top_indices = sorted(
        range(len(bm25_scores)),
        key=lambda i: bm25_scores[i],
        reverse=True
    )[:candidate_k]
    bm25_ids = [chunk_ids[i] for i in top_indices]

    # --- Merge with RRF ---
    merged_ids = reciprocal_rank_fusion(vector_ids, bm25_ids)

    # --- Fetch and return top chunks ---
    top_ids = merged_ids[:top_k]
    results = collection.get(ids=top_ids)
    return [
        {"id": id_, "text": text}
        for id_, text in zip(results["ids"], results["documents"])
    ]


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    # Build (query, chunk_text) pairs for the cross-encoder
    pairs = [(query, chunk['text']) for chunk in candidates]

    # Score all pairs
    scores = reranker.predict(pairs)

    # Sort candidates by score, highest first
    ranked = sorted(
        zip(candidates, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return [chunk for chunk, _ in ranked[:top_k]]


def retrieve_and_rerank(query: str, collection, bm25_index, chunk_ids, top_k: int = 5) -> list[dict]:
    candidates = hybrid_retrieve(query, collection, bm25_index, chunk_ids, top_k=10, candidate_k=20)
    return rerank(query, candidates, top_k=top_k)


test_queries = [
    {
        "query": "How many paid vacation days are employees entitled to per year?",
        "expected_substring": "twenty (20) paid vacation days per calendar year",
    },
    {
        "query": "Can unused sick days be rolled over into the following year?",
        "expected_substring": "Sick days do not carry over",
    },
    {
        "query": "What is the remote work policy and how many days per week are permitted?",
        "expected_substring": "permitted to work remotely for up to three (3) days per week",
    },
    {
        "query": "What share of health insurance premiums does the company contribute?",
        "expected_substring": "covers eighty percent (80%) of monthly health insurance premiums",
    },
    {
        "query": "Is there a cap on the dental coverage reimbursement the company provides?",
        "expected_substring": "dental plan reimburses up to one thousand five hundred dollars ($1,500)",
    },
    {
        "query": "How does the 401k employer match work and up to what percentage of contributions?",
        "expected_substring": "matches one hundred percent (100%) of employee contributions up to four percent (4%)",
    },
    {
        "query": "Is there a dedicated budget for training or professional development?",
        "expected_substring": "annual professional development budget of two thousand dollars ($2,000)",
    },
    {
        "query": "How many weeks of paid parental leave does the company offer?",
        "expected_substring": "sixteen (16) weeks of fully paid parental leave",
    },
    {
        "query": "How often are performance reviews held and at what times of year?",
        "expected_substring": "formal performance reviews twice per year, in March and in September",
    },
    {
        "query": "Is there a formal program for referring external candidates for open positions?",
        "expected_substring": "Employee Referral Program",
    },
]


def run_eval(label, retrieve_fn):
    print(f"\n=== {label} ===")
    hits = 0
    for query in test_queries:
        chunks = retrieve_fn(query["query"])
        retrieved_texts = [c["text"] for c in chunks]
        hit = any(query["expected_substring"] in text for text in retrieved_texts)
        if hit:
            hits += 1
        print(f"[{'HIT' if hit else 'MISS'}] {query['query']}")
    total = len(test_queries)
    print(f"Hit rate: {hits}/{total} = {hits / total:.0%}")


if __name__ == "__main__":
    collection = initialize()
    result = collection.get()
    all_chunk_texts = result["documents"]
    chunk_ids = result["ids"]
    bm25_index = build_bm25_index(all_chunk_texts)

    run_eval(
        "Hybrid (RRF, no reranking)",
        lambda q: hybrid_retrieve(q, collection, bm25_index, chunk_ids)
    )
    run_eval(
        "Hybrid + Reranking",
        lambda q: retrieve_and_rerank(q, collection, bm25_index, chunk_ids)
    )

