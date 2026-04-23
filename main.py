from argparse import ArgumentParser, FileType
from dotenv import load_dotenv
from utils import extract_and_store, query_llm

load_dotenv()


def parse_args():
    parser = ArgumentParser(prog="LLM QA", description="Ingest PDFs or query the knowledge base")
    parser.add_argument("--files", nargs="+", type=FileType("rb"),
                        help="PDF files to ingest into the database")
    parser.add_argument("--query", nargs="+", type=str,
                        help="Question to ask against the database")
    args = parser.parse_args()
    if not args.files and not args.query:
        parser.error("Provide --files to ingest PDFs or --query to ask a question")
    return args


def main():
    args = parse_args()
    if args.files:
        extract_and_store(args.files)
    elif args.query:
        print(query_llm(" ".join(args.query)))


if __name__ == "__main__":
    main()
