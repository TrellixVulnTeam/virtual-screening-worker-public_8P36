import subprocess
from pathlib import Path


def _get_smi(smi_path: Path) -> str:
    first_line = smi_path.read_text().splitlines()[0]
    return first_line.split()[0]


def run(input_path: Path, output_path: Path):

    try:
        subprocess.run(
            [
                "obabel",
                "-i", "pdbqt", input_path,
                '-o', 'smi', '-O', output_path
            ],
            check=True,
            capture_output=True,
        )
        return _get_smi(output_path)
    except subprocess.CalledProcessError as ex:
        stderr = ex.stderr.decode("utf-8")
        message = f'Error running open babel. input: {input_path}, output: {output_path}, stderr:\n{stderr}'
        raise RuntimeError(message) from ex
