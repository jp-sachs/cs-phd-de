import argparse
import re
from pathlib import Path

import pandas as pd
from tqdm import tqdm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        'Search text extracted from pdfs'
    )
    parser.add_argument(
        '--txt-dir',
        type=Path,
        default=Path('../data/txt'),
        help='Directory containing the extracted text files'
    )
    parser.add_argument(
        '--out-dir',
        type=Path,
        default=Path('../data/results'),
        help='Directory to save the results to'
    )
    return parser.parse_args()


def get_sentences_from_indices(
        indices: list[int],
        query: str,
        text: str,
        num_surrounding_chars: int = 1000
) -> list[str]:
    blacklist = [
        'bzw.',
        'z.B.',
        'vgl.',
        'Abs.',
        'Fachspez.',
        'Nr.',
        'gem.',
        'S.',
        'Dr.'
    ]
    blacklist += [f'{i}.' for i in range(20)]

    sentences = []
    for word_start_idx in indices:
        word_end_idx = word_start_idx + len(query)
        words_before = text[max(0, word_start_idx - num_surrounding_chars):word_start_idx].split()
        for b_idx in range(len(words_before) - 1, 0, -1):
            if words_before[b_idx][-1] == '.' and words_before[b_idx] not in blacklist:
                sentence_before = words_before[b_idx + 1:]
                break
        else:
            sentence_before = words_before
        sentence_before = ' '.join(sentence_before)

        words_after = text[word_end_idx:min(word_end_idx + num_surrounding_chars, len(text))].split()
        for a_idx in range(len(words_after)):
            if words_after[a_idx][-1] == '.' and words_after[a_idx] not in blacklist:
                sentence_after = words_after[:a_idx + 1]
                break
        else:
            sentence_after = words_after
        sentence_after = ' '.join(sentence_after)

        space_after = ' ' if text[word_end_idx] == ' ' else ''
        space_before = ' ' if text[word_start_idx - 1] == ' ' else ''
        full_sentence = f'{sentence_before}{space_before}{query}{space_after}{sentence_after}'
        sentences.append(full_sentence)
    return sentences


def main(args: argparse.Namespace):
    queries = [
        'kumulativ',
        'kumu',
        'cumulativ',
        'cumu',
        'Monographie',
        'Monografie'
    ]
    # maybe make more intelligent lookaround that checks for paragraphs etc

    # TODO: Analysis: Figure out what to do with those uni that do not have either
    results = []
    for txt_path in tqdm(args.txt_dir.iterdir()):
        with txt_path.open() as f:
            text = f.read()
        query_result = {
            'file_name': txt_path.name,
        }
        for query in queries:
            # TODO: figure out if line-breaks should be removed for better results
            indices = [match.start() for match in re.finditer(query, text)]
            sentences = get_sentences_from_indices(indices, query, text)
            query_result[query] = sentences
        results.append(query_result)

    short_results = pd.concat([pd.DataFrame({k: len(v) > 0 if k != 'file_name' else v for k, v in d.items()}, index=[0]) for d in results])
    args.out_dir.mkdir(parents=True, exist_ok=True)
    short_results.to_csv(args.out_dir / 'query_results.csv', index=False)

    # TODO: figure out how to properly save the extracted sentences
    # for result in results:
    #     file_name = result['file_name']
    #     sentences = [v for k, v in result.items() if k != 'file_name' and len(v) > 0]
    #     flat_sentences = list(dict.fromkeys([sentence for sublist in sentences for sentence in sublist]))


if __name__ == '__main__':
    main(parse_args())
