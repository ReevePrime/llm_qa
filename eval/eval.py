import chromadb
import openai
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "../chroma_data"
COLLECTION_NAME = "openai_embeddings"
EMBEDDING_MODEL = "text-embedding-3-small"


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


test_queries = [
    {
        "query": "How many days of annual vacation do employees get each year?",
        "expected_substring": "twenty (20) paid vacation days per calendar year",
    },
    {
        "query": "How many days of sick leave do employees get each year? Is there anything else I should be aware of about those sick days?",
        "expected_substring": "Sick days do not carry over",
    },
    {
        "query": "Does the company allow employees to work from home?",
        "expected_substring": "permitted to work remotely for up to three (3) days per week",
    },
    {
        "query": "Does the company provide health insurance?",
        "expected_substring": "covers eighty percent (80%) of monthly health insurance premiums",
    },
    {
        "query": "What else is insured by the company? Is there a maximum allowance?",
        "expected_substring": "dental plan reimburses up to one thousand five hundred dollars ($1,500)",
    },
    {
        "query": "What are the rates of the 401k?",
        "expected_substring": "matches one hundred percent (100%) of employee contributions up to four percent (4%)",
    },
    {
        "query": "Is there some sort of fund provided by the company to allow for professional development?",
        "expected_substring": "annual professional development budget of two thousand dollars ($2,000)",
    },
    {
        "query": "Does the company allow me to take time off if I have a child?",
        "expected_substring": "sixteen (16) weeks of fully paid parental leave",
    },
    {
        "query": "How does the company evaluate my performances? Is it at a specific period each year?",
        "expected_substring": "formal performance reviews twice per year, in March and in September",
    },
    {
        "query": "I would like to suggest an employee that I believe would be qualified to work there. Is there a specific program that would allow me to do this?",
        "expected_substring": "Employee Referral Program",
    },
]

if __name__ == "__main__":
    collection = initialize()
    embed_queries(test_queries)
    check_results(test_queries, collection)
