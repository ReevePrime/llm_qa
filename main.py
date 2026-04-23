from argparse import ArgumentParser, FileType
from dotenv import load_dotenv
from utils import initialize, extract_and_store

load_dotenv()

# Argumentparser to get PDF files from command line -> python main.py --files file1.pdf file2.pdf ...
def parse_args():
    parser = ArgumentParser(prog="Extract content of a PDF file", description=__doc__)
    parser.add_argument("--files", nargs="+", type=FileType("rb"), required=True,
                        help="PDF files to extract content from")
    return parser.parse_args()


def main():
    args = parse_args()
    extract_and_store(args)


if __name__ == "__main__":
    main()