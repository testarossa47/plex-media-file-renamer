# Plex File Renamer

A GUI tool for Linux Mint to rename video files for Plex Media Server compatibility. Styled to match the Nemo file manager.

## Features

- **Nemo-style GUI** - Integrates seamlessly with Linux Mint's look and feel
- **Batch Renaming** - Rename multiple video files at once
- **Plex-Compatible Format** - Outputs files in "SeriesName - S01E04.mp4" format
- **Flexible Sorting** - Sort files by creation date, modification date, or name
- **Custom Extensions** - Define both source and target file extensions
- **Live Preview** - See exactly how files will be renamed before applying changes
- **Undo Feature** - Revert the last rename operation with one click
- **Save Settings** - Store your default preferences for quick reuse
- **Configurable Episode Numbering** - Set custom starting season and episode numbers

## Requirements

- Linux Mint (or any Linux distribution with GTK 3)
- Python 3.6+
- GTK 3.0
- PyGObject

## Installation

### Install Dependencies

On Linux Mint/Ubuntu/Debian:

```bash
sudo apt-get update
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

### Make the Script Executable

```bash
chmod +x file_renamer.py
```

## Usage

### Running the Application

```bash
./file_renamer.py
```

Or with Python:

```bash
python3 file_renamer.py
```

### Step-by-Step Guide

1. **Select a Folder**
   - Click the folder chooser button at the top
   - Navigate to the folder containing your video files
   - Click "Select"

2. **Configure Settings**
   - **Series Name**: Enter the name of your TV series (e.g., "Breaking Bad")
   - **Season**: Set the season number (e.g., 1 for Season 1)
   - **Start Episode**: Set the episode number to start from (e.g., 1)
   - **Source Extension**: The file extension to look for (default: .ts)
     - Check **All files** to rename all files in the folder regardless of extension
     - When "All files" is checked, the source extension field is disabled
   - **Target Extension**: The file extension for renamed files (default: .mp4)
   - **Sort by**: Choose how to order files
     - Creation Date (Ascending) - oldest first (default)
     - Creation Date (Descending) - newest first
     - Modification Date (Ascending) - oldest first
     - Modification Date (Descending) - newest first
     - Name (A-Z) - alphabetical order
     - Name (Z-A) - reverse alphabetical order

3. **Preview Changes**
   - The bottom panel shows exactly how each file will be renamed
   - Original filename on the left, new filename on the right
   - Verify the order is correct

4. **Rename Files**
   - Click "Rename Files" when ready
   - Confirm the operation in the dialog
   - Files will be renamed in place

5. **Undo Rename** (If needed)
   - If you made a mistake, click "Undo Last Rename"
   - This will restore all files from the last rename operation to their original names
   - The undo button is only available immediately after a rename operation
   - Performing a new rename will clear the previous undo history

6. **Save Settings** (Optional)
   - Click "Save Settings" to store your current configuration as defaults
   - These settings will be loaded automatically next time you open the app

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

Settings are automatically saved to `~/.config/plex-file-renamer/settings.json`

You can manually edit this file to set defaults:

```json
{
  "series_name": "My Series",
  "season": 1,
  "start_episode": 1,
  "source_extension": ".ts",
  "target_extension": ".mp4",
  "sort_by": "ctime_asc",
  "all_files": false
}
```

Sort options:
- `ctime_asc` - Creation date ascending (default)
- `ctime_desc` - Creation date descending
- `mtime_asc` - Modification date ascending
- `mtime_desc` - Modification date descending
- `name_asc` - Name A-Z
- `name_desc` - Name Z-A

All files option:
- `true` - Rename all files in the folder
- `false` - Only rename files matching the source extension (default)

## Creating a Desktop Launcher

To add the application to your menu:

1. Create a `.desktop` file:

```bash
nano ~/.local/share/applications/plex-file-renamer.desktop
```

2. Add this content (adjust the path):

```ini
[Desktop Entry]
Name=Plex File Renamer
Comment=Rename video files for Plex Media Server
Exec=/home/fabio/Datadrive/FileRenamer/file_renamer.py
Icon=video-x-generic
Terminal=false
Type=Application
Categories=AudioVideo;Utility;
```

3. Save and close. The application should now appear in your application menu.

## Troubleshooting

### Application won't start

Check if GTK dependencies are installed:
```bash
python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk"
```

If you get an error, reinstall the dependencies.

### Files aren't appearing

- Check that the source extension matches your files (including the dot)
- Extensions are case-insensitive
- Make sure you have read permissions on the folder

### Permission denied when renaming

- Ensure you have write permissions on the folder
- Check if any files are currently open in another program

## License

This project is free and open-source software.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.
