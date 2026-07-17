# CLAUDE.md

Context for AI coding agents (and humans) working on this repo. Read this before
editing.

## What this is

`AOMrescale.py` is a single-file **Tkinter GUI** used in an atomic-physics lab
(Weiss group, cold-atom / optical-lattice experiment) to rescale AOM
calibration files. See `README.md` for the user-facing description. This file
covers the things that aren't obvious from reading the code and that are easy to
break.

## Hard constraint: this is Python 2, and must stay Python 2

**Do not port this to Python 3 unless the user explicitly asks.** It runs on the
lab's **Windows XP** experiment-control machine, whose Python is 2.x. A Py3
"cleanup" would silently break the machine that matters. Py2-isms that are load-
bearing and must be preserved:

- `import Tkinter`, `tkFileDialog`, `tkMessageBox`, `tkSimpleDialog` (not the
  `tkinter.*` Py3 names).
- `xrange`, iterator `.next()` (e.g. `csv.reader(...).next()`).
- Files opened in binary `'rb'`/`'wb'`/`'ab'` and `csv` reader/writer semantics
  as they behave in Py2.
- `str`/`unicode` comparison assumptions (e.g. the log-header check in
  `writelog`).

There is **no Python 2 available in the typical dev sandbox**, so you usually
**cannot run this file**. Validate changes by parsing the grammar instead, e.g.
`python3 -c "import ast; ast.parse(open('AOMrescale.py').read())"`, and reason
carefully about runtime behavior. Do not "verify" by running under Python 3 and
concluding it's broken — of course it is under Py3.

## Architecture (one class, `App`)

- State is held in **parallel lists**, one entry per AOM channel, all the same
  length as `self.Number` (the channel count). Index `i` addresses a channel
  across every list (`self.Names[i]`, `self.AOMfile[i]`, `self.newvalues[i]`, …).
- **`add_row(name, fname, minval, enabled)`** builds one channel: it appends to
  every parallel list AND creates/grids that row's widgets. It is the single
  source of truth for row creation — used both at startup (looping over the list
  file) and by the **Add AOM** button at runtime. If you add a new per-channel
  piece of state or widget, append it inside `add_row` so both paths stay in
  sync, and initialize the list to `[]` in `__init__`.
- `readlistfile()` returns a list of `(name, file, min)` tuples; it does **not**
  mutate state. `__init__` feeds those tuples to `add_row`.
- `reposition_buttons()` keeps the button bar at grid row `Number+2`; call it
  after adding rows.
- Widgets grid at `row = i + 2` (row 0 = headers, rows shift down as channels
  are added).

## Invariants that encode past bug fixes — do not regress these

1. **No compounding rescale.** `update()` computes the "old max" by reading it
   fresh from the file (`oldmax = max(self.yvalues[i])`), NOT from the cached
   `self.oldvalues`. This makes a second Update a no-op instead of scaling twice.
   Keep scaling relative to the file's current max.
2. **Never overwrite an existing `.bak`.** `update()` only creates the backup
   `if not os.path.isfile(bakfile)`. This preserves the pristine original across
   re-runs. Do not "simplify" this back to an unconditional `shutil.copyfile`.
3. **Log header stays in sync.** `writelog()` compares the current channel set to
   the last `#Date` header in `aomlog.txt` and writes a fresh header when they
   differ, so columns never silently drift from the header.
4. **It's `tkMessageBox`, not `tkMessagebox`.** The original had this typo, which
   turned the log-error path into a `NameError`. Keep the capital B.
5. **`reset()` skips bad files with `continue`**, not `break` — one unreadable
   file must not stop the rest from loading.
6. `readlistfile()` **skips blank lines**; `pickfile()` does **not** overwrite the
   filename when the dialog is cancelled (guards against `os.path.normpath('') == '.'`).

## Data files & formats

- `aomlist.txt` — `Name <TAB> File <TAB> Min`, real tabs, exactly 3 fields/line,
  header + blank lines ignored. Paths are Windows paths on the control PC.
- `aomlog.txt` — append-only tab-separated log; header row starts with `#Date`.
- Calibration files (referenced by `aomlist.txt`) — tab-separated `x <TAB> y`
  with `\r\n` line endings. The tool reads and rewrites them in this format.
- `*.bak` — auto-created backups, git-ignored.

## Known gaps / TODOs (from the source)

- Lattice channels (X/Y/Z…) are treated as independent though they may be
  physically coupled — see the header TODO.
- The GUI can add channels but not rename/delete them (delete a line from
  `aomlist.txt` to remove one). Add-only was a deliberate scope choice.
- Backups are never auto-cleaned; the first `.bak` persists until deleted by hand.

## Repo / workflow notes

- Public repo: `Weiss-Quantum-Computing/AOMrescale`, default branch `main`.
- `aomlist.txt` and `aomlog.txt` (real lab paths and calibration history) are
  committed and public by the owner's choice — don't add new sensitive data
  without checking.
- Keep edits minimal and match the existing Py2 style; this is production lab
  software, not a greenfield project.
