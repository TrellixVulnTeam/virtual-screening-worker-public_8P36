import logging
from itertools import islice
from pathlib import Path
from typing import List, Optional

import click
import click_config_file
import numpy as np
import pandas as pd

from cli import OrderedCommand

logger = logging.getLogger(__name__)


def _get_margin_affinity(top_percentage: int, all_files: List[Path]) -> float:
    affinity = 0
    for i, f in enumerate(all_files):
        logger.info(f'{i + 1} files read.')
        df = pd.read_csv(f, header=None, names=['origin', 'ligand', 'smi', 'affinity'])
        df = df.sort_values(by=['affinity'], ascending=True)
        top_i = int(len(df) * (top_percentage / 100))
        af = df.iloc[top_i]['affinity']
        affinity += af
    return affinity / len(all_files)


def _filter_best_affinity(margin: float, all_files: List[Path]) -> List[Path]:
    logger.info(f'Filtering results where affinity < {margin}')
    outputs = []
    for i, f in enumerate(all_files):
        logger.info(f'{i + 1} files read.')
        logger.info(f)
        df = pd.read_csv(f, header=None, names=['origin', 'ligand', 'smi', 'affinity'])
        df = df[df['affinity'] < margin]
        df.sort_values(by=['affinity'], inplace=True)
        output = f.parent / 'output_top.csv'
        df.to_csv(output, index=False, header=False)
        outputs.append(output)
    return outputs


def _get_line_in_file(path: Path, line_number: int):
    with path.open() as lines:
        for file_line in islice(lines, line_number - 1, line_number):
            return file_line


def _get_top_affinities(all_files: List[Path]):
    affinities = np.zeros(len(all_files))
    for i, file_name in enumerate(all_files):
        # 1 - is the 1st line in the file
        line = _get_line_in_file(file_name, 1)
        if not line:
            affinities[i] = None
        else:
            affinities[i] = float(line.split(',')[-1].strip())
    return affinities


def _read_affinity_in_file_at(file_name: Path, line_number: int):
    try:
        line = _get_line_in_file(file_name, line_number + 1)
        if not line:
            return None
        return line.split(',')[-1]
    except:
        return None


def _read_line_in_file_at(file_name: Path, line_number: int):
    try:
        line = _get_line_in_file(file_name, line_number + 1)
        if not line:
            return None
        return line
    except:
        return None


def _merge_sorted_files(all_files: List[Path], output: Path, item_limit: Optional[int]):
    # To hold pointers to which line in each file is being read
    working_indexes = np.zeros(len(all_files), dtype=int)
    affinities = _get_top_affinities(all_files)
    any_items_to_add = True
    i = 0
    while affinities != np.nan:
        i += 1
        if item_limit and 0 < item_limit < i:
            print(f'Compound count limit of {item_limit} reached.')
            break
        min_affinity = np.min(affinities)
        if np.isnan(min_affinity):
            break
        if i % 1000 == 0:
            print(f'{i} compounds sorted.')
        min_affinity_indexes = np.where(affinities == min_affinity)
        if len(min_affinity_indexes) > 0 and len(min_affinity_indexes[0]) > 0:
            min_affinity_i = min_affinity_indexes[0][0]
        else:
            any_items_to_add = False
            break
        # Read file line with the next best affinity and append it to the output file
        min_line = _read_line_in_file_at(all_files[min_affinity_i], working_indexes[min_affinity_i])
        if min_line:
            with open(output, "a") as error_file:
                print(min_line.strip(), file=error_file)
        # Move current index in file by 1
        working_indexes[min_affinity_i] += 1
        # And read next affinity value at the new index
        affinities[min_affinity_i] = _read_affinity_in_file_at(all_files[min_affinity_i],
                                                               working_indexes[min_affinity_i])


@click_config_file.configuration_option(implicit=False, exists=True)
@click.option("--input", envvar="INPUT", type=click.Path(exists=True), required=True,
              help="The input directory under which to search for analysis output")
@click.option("--output", envvar="OUTPUT", required=True, default="./out/collected_output.csv",
              help="The output file where collected results will be saved")
@click.option("--limit", envvar="LIMIT", type=int,
              help='A limit on the number of results to return, within the top percentage. Defaults to no limit')
@click.option("--percentage", envvar="PERCENTAGE", type=int, default=10,
              help="The top percentage of results to collect.")
@click.command(cls=OrderedCommand, help="Collect results from previous analysis runs")
def collect(input: str, output: str, limit: int, percentage: int):
    input_path = Path(input)
    output_path = Path(output)

    all_files = list(input_path.rglob("**/output.txt"))
    logger.info(f'{len(all_files)} files found')
    if len(all_files) < 1:
        logger.info('No output files to collect results from found!')
        return
    if output_path.exists():
        output_path.unlink()
    # Find the margin affinity, that limits the top 10 % of the results
    margin = _get_margin_affinity(percentage, all_files)
    # Filter out output lines that have affinity > margin and save filtered and sorted entries to the a new file
    top_output_paths = _filter_best_affinity(margin, all_files)
    _merge_sorted_files(top_output_paths, output_path, item_limit=limit)
