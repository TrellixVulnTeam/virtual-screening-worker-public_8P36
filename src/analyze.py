import shutil
import tarfile
from pathlib import Path

import click
import click_config_file

import logging
from cli import OrderedCommand
from processing.duration_logger import DurationLogger
from processing import vina, open_babel

from processing.vina_options import VinaPublicOptions, VinaOptions

logger = logging.getLogger(__name__)


def _extract_archive(input_path, output_path):
    with tarfile.open(input_path, 'r:gz') as f:
        f.extractall(output_path)


VINA_HELP = "See vina --help"


@click_config_file.configuration_option(implicit=False, exists=True)
@click.option("--input", envvar="INPUT", type=click.Path(exists=True), required=True,
              help="the .tar.gz archive containing the ligands")
@click.option("--output", envvar="OUTPUT", default="./out", help="The path where output will be saved")
@click.option("--receptor", envvar="RECEPTOR", type=click.Path(exists=True), required=True, help=VINA_HELP)
@click.option("--center_x", envvar="CENTER_X", type=float, required=True, help=VINA_HELP)
@click.option("--center_y", envvar="CENTER_Y", type=float, required=True, help=VINA_HELP)
@click.option("--center_z", envvar="CENTER_Z", type=float, required=True, help=VINA_HELP)
@click.option("--size_x", envvar="SIZE_X", type=float, required=True, help=VINA_HELP)
@click.option("--size_y", envvar="SIZE_Y", type=float, required=True, help=VINA_HELP)
@click.option("--size_z", envvar="SIZE_Z", type=float, required=True, help=VINA_HELP)
@click.option("--flex", envvar="FLEX", type=str, help=VINA_HELP)
@click.option("--cpu", envvar="CPU", type=int, help=VINA_HELP)
@click.option("--seed", envvar="SEED", type=int, help=VINA_HELP)
@click.option("--exhaustiveness", envvar="EXHAUSTIVENESS", type=int, help=VINA_HELP)
@click.option("--num_modes", envvar="NUM_MODES", type=int, help=VINA_HELP)
@click.option("--energy_range", envvar="ENERGY_RANGE", type=int, help=VINA_HELP)
@click.option("--weight_hydrogen", envvar="WEIGHT_HYDROGEN", type=float, help=VINA_HELP)
@click.option("--limit", envvar="LIMIT", type=int, help='Limit the number of ligands analysed. Defaults to no limit')
@click.command(cls=OrderedCommand, help="Analyze a receptor with a .tar.gz collection")
def analyze(input: str, output: str, receptor: str, center_x: float, center_y: float, center_z: float,
            size_x: float, size_y: float, size_z: float, flex: str, cpu: int, seed: int, exhaustiveness: int, num_modes: int,
            energy_range: int, weight_hydrogen: float, limit: int):
    input_path = Path(input)
    output_path = Path(output)
    vina_public_options = VinaPublicOptions(
        receptor=Path(receptor),
        center_x=center_x,
        center_y=center_y,
        center_z=center_z,
        size_x=size_x,
        size_y=size_y,
        size_z=size_z,
        flex=flex,
        cpu=cpu,
        seed=seed,
        exhaustiveness=exhaustiveness,
        num_modes=num_modes,
        energy_range=energy_range,
        weight_hydrogen=weight_hydrogen
    )

    tranche = input_path.parent.stem
    collection = input_path.name.split('.')[0]

    collection_path = output_path / tranche / collection

    if collection_path.exists():
        shutil.rmtree(collection_path)

    ligands_path = collection_path / "ligands"

    duration_logger = DurationLogger(collection_path / "durations.txt")

    with duration_logger.log_time(f"Extracted archive {input_path}"):
        _extract_archive(input_path, ligands_path)
    ligands = list(ligands_path.rglob("*.pdbqt"))
    ligand_count = len(ligands)
    logger.info(f'{ligand_count} ligands found.')
    if limit and limit < ligand_count:
        logger.info(f'Only {limit} ligands will be analyzed.')
        ligands = ligands[:limit]

    output_log_path = collection_path / "output.txt"

    with duration_logger.log_time("Total duration"):
        for ligand in ligands:
            ligand_path = collection_path / ligand.stem
            ligand_path.mkdir(parents=True, exist_ok=True)

            vina_options = VinaOptions(
                public=vina_public_options,
                ligand=ligand,
                out=ligand_path / 'output.pdbqt',
                log=ligand_path / 'vina-log.txt'
            )

            with duration_logger.log_time(f'Analyzed ligand {ligand}'):
                try:
                    affinity = vina.run(vina_options)
                    smi = open_babel.run(vina_options.out, ligand_path / 'output.smi')
                    with output_log_path.open('a') as f:
                        f.write(f"{tranche}_{collection},{ligand.name},{smi},{affinity}\n")
                except Exception:
                    logger.exception(f"Failed to analyze {ligand}")
