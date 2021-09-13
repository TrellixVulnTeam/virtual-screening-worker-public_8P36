# YellowDog Virtual Screening Worker

Contains AutoDock Vina, Open Babel and a Python wrapper for processing their output. Intended to be used by a worker
as part of the YellowDog Scheduler.

# Requirements

Python 3.8+, AutoDock Vina and Open Babel:

```shell
sudo apt install python3 autodock-vina openbabel
```

Install required Python libraries:

```shell
python3 -m pip install -r requirements.txt
```

# Usage

Note that any Python script configuration mentioned below may be provided in 3 ways:

* As command line arguments e.g. `--an_example "an_example_value"`. Most useful for values you wish to change regularly
  between runs.
* As environment variables e.g. `AN_EXAMPLE="an_example_value"`. Most useful for sensitive data like passwords.
* Via a configuration file e.g. if `an_example="an_example_value` is a line inside the file `config`, then this can be
  fed into application via the command line argument `--config ./config`. Most useful for values that will stay the
  same between runs.

## Analyze

Download a tranche `.tar` from virtual-flow.org and extract it somewhere locally. The collections are expected to be in
a sub-directory named after the tranche e.g. for tranche `HHBEEC`, the directory structure should look like this:
`HHBEEC/00000.tar.gz`

You must also have a receptor in `pdbqt` format.

In this example, it will be assumed that both the extracted ligands, and the receptor are in a directory named `in`
sitting alongside this `README.MD` and that you execute all commands in the same directory as this `README.MD`.

To analyze all the ligands contained in a collection against a given receptor:

```shell
python3 src/main.py analyze \
    --receptor in/example.pdbqt \
    --input in/HHBEEC/000000.tar.gz \
    --center_x "0.0" \
    --center_y "0.0" \
    --center_z "0.0" \
    --size_x "0.0" \
    --size_y "0.0" \
    --size_z "0.0"
```

The command line arguments are identical to AutoDock Vina except that:
* `--input` replaces the `--ligand` argument
* the `out` and `log` arguments are not configurable and set internally

All output will be generated to a directory `out` relative to where the script is run. Inside will be the following
structure (here for example tranche `HHBEEC`:

```shell
out
  HHBEEC                    # the tranche name
    00000                   # the collection name
      durations.txt         # performance metrics
      output.txt            # a summary of results for all ligands
      ligands               # the extracted contents of the collection `.tar.gz`
      Z449871492_1_T1       # a directory for each ligand in the collection
        output.pdpqt        # output from AutoDock Vina
        vina-log.txt        # log output from AutoDock Vina
        output.smi          # output from Open Babel
      Z449871492_2_T1
      ...
```

`output.txt` contains output in the following format, with 1 line per ligand:

```text
HHBEEC_00000,Z449871492_1_T1.pdbqt,C(=O)(N1[C]([C][C]1)[C]NC(=O)C1([C][C]O[C][C]1)[C])[C]C1=[C]C(=[C]N=[C]1)[C],-8.7
HHBEEC_00000,Z449871492_2_T1.pdbqt,C(=O)(N[C][C]1N(C(=O)C#C[C]2[C][C]2)[C][C]1)[C]([C])c1c([C])onc1[C],-9.2
...
```

Note that the directory for a collection  e.g. `out/HHBEEC/00000` will be deleted and recreated if it already exists.

## Collect

To collect results from the output of previous runs:

```shell
python3 src/main.py collect --input "./out"
```

The `--input` parameter should be the same directory as was output to by the `analyze` command (`./out` by default).

Output will be to the file `out/collected_output.csv`. Note that this file is deleted and recreated each time results
are collected.

The top 10% of results are collected, sorted by affinity.

## Advanced

To see all available options add `--help` after specifying a command:

```shell
python3 src/main.py analyze --help
```

# Docker

The application may also be executed as a docker container.

## Building

Build docker image:

```shell
DOCKER_BUILDKIT=1 docker build . -t virtual-screening-worker
```

## Running

Use the same parameters as when running outside of Docker.

Any input files must be mounted as a volume on the container.

To access output, the output directory must also be shared from the container to the host:

```shell
docker run -v "$(pwd)/in:/in" -v "$(pwd)/out:/out" virtual-screening-worker analyze --receptor /in/example.pdbqt ...
```
