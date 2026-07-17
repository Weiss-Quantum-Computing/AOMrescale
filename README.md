# AOMrescale

A small Tkinter desktop GUI for **rescaling AOM (acousto-optic modulator)
calibration files** in the Weiss group's cold-atom experiment-control setup.

Each AOM channel has a stored calibration curve mapping a control setting (`x`)
to measured optical power (`y`). Over time the achievable maximum power drifts
(laser aging, alignment, etc.). Rather than re-measuring the whole curve, you
re-measure only the **maximum power** and this tool multiplies the entire stored
curve by `new_max / old_max`, so the shape is preserved and the peak matches
reality again.

Originally written by Ted Corcovilos (2013). It targets **Python 2** because it
runs on the Windows XP machine that controls the experiment.

---

## Requirements

- **Python 2.7** (uses `Tkinter`, `xrange`, `iterator.next()`, `print`-free but
  Py2 string/`open` semantics). It will **not** run unmodified on Python 3.
- Tkinter (bundled with standard CPython 2 on Windows).
- No third-party packages.

Run it from the directory containing `aomlist.txt`:

```
python AOMrescale.py
```

> The GUI reads `aomlist.txt` from the **current working directory** at startup,
> and writes `aomlog.txt` there too, so launch it from the folder that holds
> those files (typically by double-clicking or from a shortcut with the right
> "Start in" directory).

---

## Files in this repo

| File | Purpose |
|------|---------|
| `AOMrescale.py` | The application. |
| `aomlist.txt` | Channel definitions. Tab-separated: `Name <TAB> File <TAB> Min`. Loaded at startup (one GUI row per line) and rewritten by **Save filenames**. |
| `aomlog.txt` | Append-only, tab-separated audit log of the max values written on each update, timestamped per run. |
| `*.bak` | Backups of calibration files, created automatically on update. Git-ignored. |

### `aomlist.txt` format

```
#Name<TAB>File<TAB>Min
Molasses<TAB>C:\...\OM-2014-9-3.txt<TAB>6.0
MOT<TAB>C:\...\MOT-20250910.txt<TAB>30.0
```

- **Name** — label shown in the GUI.
- **File** — full path to that channel's calibration file (Windows paths, on the control PC).
- **Min** — minimum acceptable new max; the New-value field turns red below it (a soft warning, not a hard block). Use `0.0` for no threshold.
- Separators must be **real tab characters**, exactly **three fields** per line. The header line and any blank lines are ignored.

### Calibration file format

Each referenced calibration file is a tab-delimited `x <TAB> y` table with
Windows (`\r\n`) line endings — the same format the tool writes back out.

---

## Using the GUI

The window shows one row per channel, with an **Enable** checkbox, the channel
name, its file path + a **Browse** button, the **Old max value**, an editable
**New max value**, and the **Min** threshold. Disabled rows are greyed out and
ignored by every action.

Buttons along the bottom:

1. **Load old values** — opens each enabled calibration file and displays its current maximum `y`.
2. **Add AOM** — prompts for a channel name and a min value, then adds a new enabled row. Pick its calibration file with the row's **Browse** button, then **Save filenames** to persist it.
3. **Save filenames** — writes the current channel list (names, paths, mins) back to `aomlist.txt`.
4. **Update calibration** — the main action (see below).
5. **Quit**.

### What "Update calibration" does

For each enabled channel whose file exists:

1. Reads the calibration file and takes its current maximum `y`.
2. Validates that both the current max and your entered new value are positive.
3. Computes `scale = new_max / current_max` and multiplies every `y` by it.
4. Backs the file up to `<file>.bak` — **an existing `.bak` is never overwritten**, so the pristine original is preserved across re-runs.
5. Overwrites the calibration file with the rescaled curve.
6. Appends a timestamped row to `aomlog.txt`.

**Re-running Update is safe.** The scale factor is computed against the file's
*current* maximum, so a second run scales by `new/new = 1.0` (a no-op) rather
than compounding the rescale.

---

## Notes & caveats

- **Backups accumulate.** Because an existing `.bak` is never overwritten, the
  first backup of a file is kept forever. After you've confirmed a good
  calibration, delete stale `.bak` files manually if you want a future update to
  capture a fresh backup. (Cleanup is intentionally left manual.)
- **The GUI can add channels but not rename or delete them.** To remove a
  channel, delete its line from `aomlist.txt`.
- **Lattice files** (X/Y/Z etc.) are treated as independent channels even though
  they may be physically interrelated — see the TODO in the source.
- **Windows paths** in `aomlist.txt` are specific to the control PC; the tool is
  meant to run there.

## License

MIT — see [LICENSE](LICENSE). Original code © 2013 Ted Corcovilos; © 2026 Weiss
Quantum Computing.
