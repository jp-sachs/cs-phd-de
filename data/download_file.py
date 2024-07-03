import argparse
import logging
import urllib
from pathlib import Path
import pandas as pd
from tqdm import tqdm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Download and save the PDFs given in a csv file'
    )
    parser.add_argument(
        '--documents-csv',
        type=Path,
        default=Path('urls.csv'),
        help='Path to the csv file containing urls to the documents that should be downloaded'
    )
    return parser.parse_args()


def main(args: argparse.Namespace):
    # save logging to file
    logging.basicConfig(
        filename='download_file.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    url_df = pd.read_csv(args.documents_csv)
    for _, row in tqdm(url_df.iterrows()):
        out_file = Path.cwd() / f"{row['university'].replace(' ', '_').replace('/', '_')}.pdf"
        if out_file.exists():
            print(f"File {out_file} already exists, skipping")
            continue
        try:
            urllib.request.urlretrieve(row['url'], out_file)
        except urllib.error.HTTPError as e:
            logging.error('Failed to download %s: %s', row['url'], e)


if __name__ == '__main__':
    main(parse_args())
