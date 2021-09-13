import logging
import subprocess
from os import PathLike
from pathlib import Path

from processing.vina_options import VinaOptions

logger = logging.getLogger(__name__)


def _chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def _get_affinity(vina_log_path: Path) -> str:
    log_text = vina_log_path.read_text()
    affinity_title_index = log_text.find('affinity')
    sliced_log_text_lines = log_text[affinity_title_index:].splitlines()
    first_mode_line = sliced_log_text_lines[3]
    return first_mode_line.split()[1]


def run(vina_options: VinaOptions):
    arguments = [
        "vina",
        "--out", vina_options.out,
        "--log", vina_options.log,
        "--ligand", vina_options.ligand
    ]
    for name, value in vars(vina_options.public).items():
        if not value:
            continue
        if not isinstance(value, (str, bytes, PathLike)):
            value = str(value)
        arguments.append(f"--{name}")
        arguments.append(value)

    message = "Running vina with the following settings:"
    for name, value in _chunker(arguments[1:], 2):
        message += f"\n  {name}: {value}"
    logger.info(message)

    try:
        subprocess.run(arguments, check=True, capture_output=True)
        return _get_affinity(vina_options.log)
    except subprocess.CalledProcessError as ex:
        stderr = ex.stderr.decode("utf-8")
        receptor = vina_options.public.receptor
        ligand = vina_options.ligand
        message = f'Error running vina. receptor: {receptor}, ligand: {ligand}, stderr:\n{stderr}'
        raise RuntimeError(message) from ex
