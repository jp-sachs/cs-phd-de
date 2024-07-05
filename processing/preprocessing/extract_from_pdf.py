import argparse
import logging
from pathlib import Path

import pandas as pd
from plotly import graph_objects as go
from pypdf import PdfReader
from tqdm import tqdm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Extract the text from the downloaded pdfs in a directory and store it in txt files'
    )
    parser.add_argument(
        '--in-dir',
        type=Path,
        default=Path('../../data/pdf'),
        help='Path to the directory that contains pdfs to extract text from'
    )
    parser.add_argument(
        '--out-dir',
        type=Path,
        default=Path('../../data/txt'),
        help='Path to the directory where the extracted text should be saved'
    )
    parser.add_argument(
        '--overwrite',
        default=False,
        action='store_true',
        help='Will overwrite existing files otherwise will just skip files that were already processed'
    )
    return parser.parse_args()


def main(args: argparse.Namespace):
    stats = []
    for pdf_path in tqdm(args.in_dir.iterdir()):
        args.out_dir.mkdir(parents=True, exist_ok=True)
        out_file = args.out_dir / f"{pdf_path.stem}.txt"

        # TODO: maybe revert to guard clause since this is currently only used for stats
        if not args.overwrite and out_file.exists():
            raw_text = out_file.read_text()
        else:
            try:
                reader = PdfReader(pdf_path)
                raw_text = ''
                for page in reader.pages:
                    raw_text += page.extract_text() + "\n"
            except Exception as e:
                logging.error('Failed to extract text from %s: %s', pdf_path, e)
                continue

        # TODO: maybe still try dehypen library because the method below doesn't take care of words where the hyphen is
        #  followed by an actual line-break
        # Mainly for removing hyphens at line endings. Of course this is a bit too aggressive but this shouldn't be a
        # problem as the text remains searchable. Unfortunately, it doesn't seem like there are tools out there that do a
        # better job
        text = raw_text.replace('-', '')

        with open(out_file, 'w') as f:
            f.write(text)

        stats.append(pd.DataFrame({
            'file_name': pdf_path.stem,
            'num_words': len(text.split()),
            'num_lines': len(text.split('\n'))
        }, index=[0]))

    # Plotting stats for sanity check
    stats = pd.concat(stats)
    stats_fig = go.Figure()
    for _, row in stats.iterrows():
        stats_fig.add_trace(
            go.Scatter(
                x=[row['num_words']],
                y=[row['num_lines']],
                name=row['file_name'],
                mode='markers',
            ),
        )
    stats_fig.update_layout(
        title='Line/word statistics for extracted texts',
        yaxis_title='Number of lines',
        xaxis_title='Number of words'
    )
    stats_fig.show()

    # Results
    # Uni_Konstanz: actually fine, just fucking long
    # Uni_BW_Muenchen: too many line breaks with in sentences/paragraphs
    # TU_Hamburg.pdf: Stream has ended unexpectedly
    # Uni_Lueneburg.pdf: Stream has ended unexpectedly
    # Uni_Hildesheim.pdf: Stream has ended unexpectedly


if __name__ == '__main__':
    logging.basicConfig(
        filename='extract_text.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main(parse_args())
