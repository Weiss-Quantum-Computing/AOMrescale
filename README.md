# AOMrescale

A small Tkinter GUI for rescaling AOM (acousto-optic modulator) calibration
files in the lab's cold-atom experiment control setup. Instead of re-taking a
full calibration curve for a channel, you only re-measure its **maximum power**;
the tool multiplies the whole stored curve by `new_max / old_max` so it matches.

Originally written by Ted Corcovilos (2013). Targets **Python 2** because it
runs on the Windows XP experiment-control machine.

## Files

- `AOMrescale.py` — the application.
- `aomlist.txt` — channel definitions, tab-separated: `Name <TAB> File <TAB> Min`.
  Loaded at startup (one GUI row per line) and rewritten by **Save filenames**.
- `aomlog.txt` — append-only, tab-separated log of the max values written on each
  update, timestamped per run.

## Usage

Run on the control PC:

```
python AOMrescale.py
```

Workflow:

1. **Load old values** — reads each enabled calibration file and shows its current max.
2. Type the freshly measured **New max value** for each channel (turns red if below its configured minimum).
3. **Update calibration** — backs up each file to `<file>.bak` (an existing `.bak` is never overwritten), rescales the curve, writes it back, and appends a row to `aomlog.txt`.
4. **Add AOM** — adds a new channel row; pick its calibration file with the row's Browse button, then **Save filenames** to persist it to `aomlist.txt`.
5. **Save filenames** — writes the current channel list back to `aomlist.txt`.

Re-running **Update** on an already-updated file is safe: the scale factor is
computed against the file's current maximum, so a second run is a no-op rather
than compounding the scaling.

## Notes

- Calibration files are tab-delimited `x <TAB> y` tables with Windows (`\r\n`) line endings.
- `aomlist.txt` must use real tab characters and exactly three fields per line.
