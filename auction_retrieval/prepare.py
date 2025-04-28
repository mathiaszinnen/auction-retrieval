from preparation.bibliography_parser import BibliographyParser
from pathlib import Path
from dotenv import load_dotenv
import os


def main():
    load_dotenv()
    data_dir = Path(os.getenv("AUCTION_RETRIEVAL_DATA_DIR", os.getcwd()))
    parser = BibliographyParser(output_dir=data_dir)
    parser.parse()

if __name__ == "__main__":
    main()