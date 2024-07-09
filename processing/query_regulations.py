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
    parser.add_argument(
        '--queries',
        type=str,
        nargs='+',
        default=[
            'kumulativ',
            'kumu',
            'cumulativ',
            'cumu',
            'Monographie',
            'Monografie'
        ],
        help='The keywords that the script should look for'
    )
    return parser.parse_args()


def deduplicate_strings(str1: str, str2: str) -> list[str]:
    for i in range(len(str1)):
        if str2.startswith(str1[i:]):
            return [str1[:i] + str2]
    else:
        return [str1, str2]


def get_sentences_from_indices(
        indices: list[int],
        query: str,
        text: str,
        num_surrounding_sentences: int = 2,
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
        num_sentences_before_discovered = -1
        for b_idx in range(len(words_before) - 1, 0, -1):
            if words_before[b_idx][-1] == '.' and words_before[b_idx] not in blacklist:
                num_sentences_before_discovered += 1
                if num_sentences_before_discovered >= num_surrounding_sentences:
                    sentence_before = words_before[b_idx + 1:]
                    break
        else:
            sentence_before = words_before
        sentence_before = ' '.join(sentence_before)

        words_after = text[word_end_idx:min(word_end_idx + num_surrounding_chars, len(text))].split()
        num_sentences_after_discovered = -1
        for a_idx in range(len(words_after)):
            if words_after[a_idx][-1] == '.' and words_after[a_idx] not in blacklist:
                num_sentences_after_discovered += 1
                if num_sentences_after_discovered >= num_surrounding_sentences:
                    sentence_after = words_after[:a_idx + 1]
                    break
        else:
            sentence_after = words_after
        sentence_after = ' '.join(sentence_after)

        space_after = ' ' if text[word_end_idx] == ' ' else ''
        space_before = ' ' if text[word_start_idx - 1] == ' ' else ''
        full_sentence = f'{sentence_before}{space_before}{query}{space_after}{sentence_after}'
        sentences.append(full_sentence)

    if len(sentences) > 1:
        deduplicated_sentences = deduplicate_strings(sentences[0], sentences[1])
        for i in range(1, len(sentences)):
            deduplicated_sentences.extend(deduplicate_strings(deduplicated_sentences.pop(-1), sentences[i]))
        assert len(deduplicated_sentences) <= len(sentences)
        return deduplicated_sentences
    else:
        return sentences


def main(args: argparse.Namespace):
    results = []
    for txt_path in tqdm(args.txt_dir.iterdir()):
        with txt_path.open() as f:
            text = f.read()
        query_result = {
            'file_name': txt_path.name,
        }
        for query in args.queries:
            # TODO: figure out if line-breaks should be removed for better results
            indices = [match.start() for match in re.finditer(query, text)]
            sentences = get_sentences_from_indices(indices, query, text)
            query_result[query] = sentences
        results.append(query_result)

    short_results = pd.concat([pd.DataFrame(
        {k: len(v) > 0 if k != 'file_name' else v for k, v in d.items()},
        index=[0]
    ) for d in results])
    args.out_dir.mkdir(parents=True, exist_ok=True)
    short_results.to_csv(args.out_dir / 'query_results.csv', index=False)

    # prepare_files for appending
    file_names = {}
    for query in args.queries:
        # TODO: technically would be nice to cleanse query string before using it in a filename
        out_file_name = args.out_dir / f'query_result_{query}.txt'
        file_names[query] = out_file_name
        if out_file_name.exists():
            out_file_name.unlink()

    results = sorted(results, key=lambda x: x['file_name'])
    for result in results:
        file_name = result.pop('file_name')
        for query, matches in result.items():
            if len(matches) == 0:
                continue

            with file_names[query].open('a') as out_f:
                combined_sentences = '\n\n'.join(matches)
                out_sentences = f"=== {Path(file_name).stem} ===\n{combined_sentences}\n\n"
                out_f.write(out_sentences)


if __name__ == '__main__':
    main(parse_args())
