# QMP-4

This is a fork of QMP-4 built to provide MacOS support.  Support for certain windows-only features has been removed, but it aims to maintain the core quadstick functionality and make it a great choice for mac users.

All credit and love goes to Fred Davidson for building an incredible accessibility product that has brought much joy into the world. Hopefully this fork brings a little more!

## Building

Create a python3.10 virtual environment and install requirements.txt . (To-do: actually add this file)

```sh
conda create -n qmp4 python=3.10
conda activate qmp4
python3 -m pip install -r requirements.txt
```

To run it for development, simply execute.

```sh
python3 QuadStick.py
```

### Building for prod

... is coming in a commit soon.
