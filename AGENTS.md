# AGENTS.md - Plex File Renamer

## Project Overview

Single-file Python 3 GTK 3 desktop application for batch-renaming video files into
Plex Media Server-compatible format (`SeriesName - S01E04.ext`). Styled to match
Linux Mint's Nemo file manager. The entire application lives in `file_renamer.py`
(single class `FileRenamer` extending `Gtk.Window`).

## Build / Run / Test Commands

### Run the application
```bash
python3 file_renamer.py
# or
./file_renamer.py
```

### Install dependencies (system-level, required)
```bash
# Debian/Ubuntu/Mint
sudo apt-get install python3 python3-gi gir1.2-gtk-3.0
# pip dependency (usually not needed if system packages are installed)
pip install -r requirements.txt
```

### Build Debian package
```bash
./packaging/build-deb.sh
# Output: dist/plex-file-renamer_1.0.0_all.deb
```

### Syntax check (no linter configured)
```bash
python3 -m py_compile file_renamer.py
```

### Tests
There is no test suite. No test framework is configured. If adding tests, use `pytest`
and place test files in a `tests/` directory. Run a single test with:
```bash
pytest tests/test_file.py::test_function_name -v
```

### Linting / Formatting
No linter or formatter is configured. If needed, use:
```bash
flake8 file_renamer.py
black file_renamer.py
```

## Architecture

```
file_renamer.py          # Entire application (single-class monolith)
packaging/
  build-deb.sh           # Debian package build script
  copyright              # Debian copyright (DEP-5)
  generate-icons.py      # Icon generation utility (Pillow, not part of build)
icons/                   # App icons (SVG + PNG at all sizes)
plex-file-renamer.desktop # XDG desktop entry
requirements.txt         # PyGObject>=3.30.0
```

Settings are persisted at `~/.config/plex-file-renamer/settings.json`.

## Code Style Guidelines

### Python Version
Python 3.6+. Shebang: `#!/usr/bin/env python3`.

### Imports
1. GTK/GObject introspection imports first (`import gi`, `gi.require_version(...)`,
   `from gi.repository import Gtk, Gdk, GLib`) -- this ordering is mandatory.
2. Standard library imports after (`os`, `json`).
3. No blank line between import groups (the `gi.require_version` call acts as separator).
4. No third-party imports beyond `gi`. No local/project imports.

### Naming Conventions
| Element              | Convention                | Example                          |
|----------------------|---------------------------|----------------------------------|
| Constants            | `UPPER_SNAKE_CASE`        | `CONFIG_FILE`                    |
| Classes              | `PascalCase`              | `FileRenamer`                    |
| Public methods       | `snake_case`              | `build_ui`, `load_files`         |
| Event handlers       | `on_` prefix              | `on_folder_selected`             |
| Internal helpers     | `_snake_case` (underscore)| `_build_rename_plan`             |
| Instance variables   | `snake_case`              | `self.current_folder`            |
| Widget instance vars | Descriptive + type suffix | `self.folder_button`, `self.season_spin` |
| Loop variables       | Short contextual names    | `idx`, `f`, `src`, `dst`         |

### String Formatting
Use **f-strings exclusively**. No `.format()` or `%` formatting.
```python
f"{series_name} - S{season:02d}E{episode_num:02d}{target_ext}"
f"Files to Rename ({count} file{'s' if count != 1 else ''})"
```

### Type Hints
Not used in this codebase. Do not add type annotations to existing code unless
specifically requested.

### Docstrings
- Every method must have a docstring.
- Use triple double-quoted single-line docstrings for most methods:
  ```python
  def build_ui(self):
      """Build the main user interface"""
  ```
- Multi-line docstrings only when return value semantics need explanation.
- No class-level docstrings. Module-level docstring at top of file.

### Comments
- Use `# ` (hash-space) format.
- Comment to explain "why", not "what".
- Document `ListStore` column schemas with inline comments.
- Use section comments as structural guideposts in long methods.

### Error Handling
- Catch broad `Exception` (the existing pattern in this codebase):
  ```python
  try:
      ...
  except Exception as e:
      self.show_error(f"Error doing thing: {e}")
  ```
- For batch operations, **accumulate errors** in a list and display a summary dialog
  after the loop completes. Do not halt on individual failures.
- Use `self.show_error()` (GUI dialog) for error reporting during normal operation.
- Use `print()` only for errors during startup before the GUI is ready.

### Formatting
- **4-space indentation**, no tabs.
- Line length: pragmatic ~80-90 characters, no strict enforcement.
- Break long lines using implicit continuation inside parentheses.
- Multi-line function calls: hanging indent or aligned to opening delimiter (both used).

### GTK Patterns
- Subclass `Gtk.Window` directly (older GTK3 pattern).
- Main loop via `Gtk.main()` / `Gtk.main_quit`.
- Signal handlers: `.connect("signal-name", self.on_handler)`.
- `create_*` factory methods return the widget they build; caller adds to parent.
- Dialogs: create, `dialog.run()`, `dialog.destroy()` in same scope. Never persist.
- CSS via `Gtk.CssProvider` loaded from bytes, applied at screen level.

### File I/O
- Use `os` module exclusively (`os.path.*`, `os.rename`, `os.listdir`, `os.makedirs`).
  Do not use `pathlib`.
- Always use `with open(...)` context managers for file read/write.
- JSON settings: `json.load()` / `json.dump()` with `indent=2`.
- No explicit encoding parameter (relies on system default UTF-8).

### Class Structure
Methods are organized in this order within `FileRenamer`:
1. `__init__` -- state setup, delegates to builders
2. UI construction (`build_ui`, `create_toolbar`, `create_config_panel`, etc.)
3. Event handlers (`on_*` methods)
4. Business logic (`load_files`, `sort_files`, `_build_rename_plan`, etc.)
5. Settings I/O (`load_settings`, `save_settings`)
6. Utilities (`show_error`)

All instance variables must be initialized in `__init__`.

### Guard Clauses
Use early returns for precondition checks:
```python
if not self.current_folder:
    return
```

### No Decorators
No `@property`, `@staticmethod`, `@classmethod`, or custom decorators are used.

### Git Workflow
- Two branches: `main` (release) and `develop` (active development).
- Work on `develop`, merge to `main` for releases.
- Remote: `origin` at `git@github.com:testarossa47/plex-media-file-renamer.git`.
