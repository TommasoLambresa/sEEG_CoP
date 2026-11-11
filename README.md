
# sEEG_CoP

Center-out task driven by the center of pressure (CoP) measured by a force plate. During development the cursor is moved with the mouse.

## Setup

```
conda activate khymeia
pip install -r requirements.txt
pip install -e .
```

`pip install -e .` makes the `cop` folder importable from the programs in `scripts/` and from `tests/`.

## Folders

- `cop/`: reusable modules (all settings in `cop/config.py`)
- `scripts/`: programs launched from the terminal
- `tests/`: run with `python -m pytest`
- `devices/`: force plate software and streaming scripts
- `data/`: saved sessions, not tracked by git
