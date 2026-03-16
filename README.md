# Plex File Renamer

A GUI tool for Linux to rename video files for Plex Media Server compatibility. Styled to match Linux Mint's Nemo file manager.

## Features

- **Nemo-style GUI** - Integrates seamlessly with Linux Mint's look and feel
- **Batch Renaming** - Rename multiple video files at once
- **Plex-Compatible Format** - Outputs files in "SeriesName - S01E04.mp4" format
- **File Selection with Checkboxes** - Cherry-pick which files to rename; skip already-renamed files
- **Shift/Ctrl Multi-Select** - Shift+click to select ranges, Ctrl+click to toggle individual files
- **Season 0 Support** - Use season 0 for Specials and Movies (Plex/TheTVDB convention)
- **Flexible Sorting** - Sort files by creation date, modification date, or name
- **Custom Extensions** - Define both source and target file extensions
- **Live Preview** - See exactly how files will be renamed before applying changes
- **Collision Detection** - Warns about filename conflicts before renaming
- **Undo Feature** - Revert the last rename operation with one click
- **Save Settings** - Store your default preferences for quick reuse
- **Persistent Window Size** - Window dimensions are saved and restored across sessions
- **Folder Memory** - Remembers the last-used folder and auto-loads files on startup
- **Keyboard Shortcut** - Ctrl+R to trigger rename

## Requirements

- Linux (tested on Linux Mint, works on any GTK 3 distribution)
- Python 3.6+
- GTK 3.0
- PyGObject

## Installation

### Debian Package (Recommended)

Download the `.deb` from the [latest release](https://github.com/testarossa47/plex-media-file-renamer/releases/latest) and install:

```bash
sudo dpkg -i plex-file-renamer_2.0.0_all.deb
```

This installs the application, desktop entry, and icons system-wide. Launch from your application menu or run `plex-file-renamer` from the terminal.

To uninstall:

```bash
sudo apt remove plex-file-renamer
```

### Manual Installation

Install dependencies on Linux Mint/Ubuntu/Debian:

```bash
sudo apt-get install python3 python3-gi gir1.2-gtk-3.0
```

On Fedora:

```bash
sudo dnf install python3 python3-gobject gtk3
```

On Arch Linux:

```bash
sudo pacman -S python python-gobject gtk3
```

Then run directly:

```bash
chmod +x file_renamer.py
./file_renamer.py
```

## Usage

### Step-by-Step Guide

1. **Select a Folder**
   - Click "Browse..." to open a folder chooser dialog
   - Navigate to the folder containing your video files
   - The app remembers your last-used folder and auto-loads it on startup

2. **Filter and Sort Files**
   - **Source Extension**: Only files matching this extension are shown (default: .ts)
   - Check **All ext** to show all files regardless of extension
   - **Sort by**: Choose how files are ordered (creation date, modification date, or name)

3. **Select Files to Rename**
   - All files are selected by default (checked)
   - Uncheck files you want to skip (e.g., already-renamed files)
   - **Shift+click** a checkbox to select/deselect a range of files
   - **Ctrl+click** a checkbox to toggle individual files without affecting others
   - Use **Select All** / **Deselect All** buttons for bulk operations

4. **Configure Output Settings**
   - **Series Name**: Enter the name of your TV series (e.g., "Breaking Bad")
   - **Season**: Set the season number (0 for Specials, 1-99 for regular seasons)
   - **Start Ep**: Set the starting episode number
   - **Target Ext**: The file extension for renamed files (default: .mp4)

5. **Preview Changes**
   - The preview panel shows how each selected file will be renamed
   - Original filename on the left, new filename on the right
   - Collisions are highlighted in red with a warning icon
   - Episode numbers are sequential across selected files only

6. **Rename Files**
   - Click "Rename Files" or press **Ctrl+R**
   - Confirm the operation in the dialog
   - If collisions are detected, choose to cancel, skip conflicts, or overwrite

7. **Undo Rename** (If needed)
   - Click "Undo Last Rename" to restore files to their original names
   - Only available immediately after a rename operation

8. **Save Settings** (Optional)
   - Click "Save Settings" to store your current configuration as defaults
   - Settings are also auto-saved on window close (including window size and folder)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+R   | Rename files |

## Example

If you have files:
```
video_001.ts
video_002.ts
video_003.ts
```

With settings:
- Series Name: "The Mandalorian"
- Season: 2
- Start Episode: 5
- Target Extension: .mp4

They will be renamed to:
```
The Mandalorian - S02E05.mp4
The Mandalorian - S02E06.mp4
The Mandalorian - S02E07.mp4
```

## Configuration

Settings are saved to `~/.config/plex-file-renamer/settings.json` and restored on startup.

```json
{
  "series_name": "My Series",
  "season": 1,
  "start_episode": 1,
  "source_extension": ".ts",
  "target_extension": ".mp4",
  "sort_by": "ctime_asc",
  "all_files": false,
  "window_width": 900,
  "window_height": 600,
  "last_folder": "/home/user/Videos"
}
```

Sort options: `ctime_asc`, `ctime_desc`, `mtime_asc`, `mtime_desc`, `name_asc`, `name_desc`

## Building the .deb Package

```bash
./packaging/build-deb.sh
```

Output: `dist/plex-file-renamer_2.0.0_all.deb`

## Troubleshooting

### Application won't start

Check if GTK dependencies are installed:
```bash
python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk"
```

### Files aren't appearing

- Check that the source extension matches your files (including the dot)
- Extensions are case-insensitive
- Try checking "All ext" to show all files
- Make sure you have read permissions on the folder

### Permission denied when renaming

- Ensure you have write permissions on the folder
- Check if any files are currently open in another program

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.
