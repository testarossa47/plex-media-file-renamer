#!/usr/bin/env python3
"""
Plex File Renamer - A GUI tool for renaming video files for Plex Media Server
Styled to match Linux Mint's Nemo file manager
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import os
import json

CONFIG_FILE = os.path.expanduser("~/.config/plex-file-renamer/settings.json")

class FileRenamer(Gtk.Window):
    DEFAULT_SETTINGS = {
        "series_name": "",
        "season": 1,
        "start_episode": 1,
        "source_extension": ".ts",
        "target_extension": ".mp4",
        "sort_by": "ctime_asc",
        "all_files": False,
        "window_width": 900,
        "window_height": 600
    }

    def __init__(self):
        super().__init__(title="Plex File Renamer")
        self.set_border_width(10)

        # Load settings (sets self.settings_load_error if config is corrupted)
        self.settings_load_error = None
        self.settings = self.load_settings()

        # Restore window size from settings
        self.set_default_size(
            self.settings.get("window_width", 900),
            self.settings.get("window_height", 600)
        )

        # Current state
        self.current_folder = None
        self.files = []

        # Undo history: list of tuples (old_path, new_path)
        self.last_rename_operation = []

        # Build UI
        self.build_ui()

        # Apply Nemo-like styling
        self.apply_styling()

        # Keyboard shortcuts
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)
        self.rename_button.add_accelerator(
            "clicked", accel_group,
            Gdk.keyval_from_name("r"), Gdk.ModifierType.CONTROL_MASK,
            Gtk.AccelFlags.VISIBLE
        )

        # Track window size changes for persistence
        self.connect("configure-event", self.on_window_configure)

        # Save window size on close
        self.connect("delete-event", self.on_window_delete)

        # Show warning after UI is ready if settings failed to load
        if self.settings_load_error:
            GLib.idle_add(self._show_settings_load_warning)

    def build_ui(self):
        """Build the main user interface"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)

        # Top toolbar
        toolbar = self.create_toolbar()
        main_box.pack_start(toolbar, False, False, 0)

        # Configuration panel
        config_panel = self.create_config_panel()
        main_box.pack_start(config_panel, False, False, 0)

        # File list with preview
        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        paned.set_position(300)

        # File list
        self.file_frame = Gtk.Frame(label="Files to Rename")
        self.file_frame.set_shadow_type(Gtk.ShadowType.IN)
        self.file_list = self.create_file_list()
        self.file_frame.add(self.file_list)
        paned.add1(self.file_frame)

        # Preview list
        preview_frame = Gtk.Frame(label="Preview")
        preview_frame.set_shadow_type(Gtk.ShadowType.IN)
        self.preview_list = self.create_preview_list()
        preview_frame.add(self.preview_list)
        paned.add2(preview_frame)

        main_box.pack_start(paned, True, True, 0)

        # Bottom action buttons
        action_box = self.create_action_buttons()
        main_box.pack_start(action_box, False, False, 0)

    def create_toolbar(self):
        """Create the top toolbar"""
        toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        # Folder selection
        self.folder_button = Gtk.FileChooserButton(title="Select Folder")
        self.folder_button.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self.folder_button.connect("file-set", self.on_folder_selected)
        toolbar_box.pack_start(Gtk.Label(label="Folder:"), False, False, 0)
        toolbar_box.pack_start(self.folder_button, True, True, 0)

        return toolbar_box

    def create_config_panel(self):
        """Create configuration panel"""
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(5)
        grid.set_margin_top(5)
        grid.set_margin_bottom(5)

        row = 0

        # Series Name
        grid.attach(Gtk.Label(label="Series Name:", xalign=1), 0, row, 1, 1)
        self.series_entry = Gtk.Entry()
        self.series_entry.set_text(self.settings.get("series_name", ""))
        self.series_entry.set_placeholder_text("e.g., The Series")
        self.series_entry.connect("changed", self.on_config_changed)
        grid.attach(self.series_entry, 1, row, 1, 1)

        # Season Number
        grid.attach(Gtk.Label(label="Season:", xalign=1), 2, row, 1, 1)
        season_adj = Gtk.Adjustment(value=self.settings.get("season", 1),
                                     lower=0, upper=99, step_increment=1)
        self.season_spin = Gtk.SpinButton(adjustment=season_adj, digits=0)
        self.season_spin.connect("value-changed", self.on_config_changed)
        grid.attach(self.season_spin, 3, row, 1, 1)

        # Episode Number
        grid.attach(Gtk.Label(label="Start Episode:", xalign=1), 4, row, 1, 1)
        episode_adj = Gtk.Adjustment(value=self.settings.get("start_episode", 1),
                                       lower=1, upper=999, step_increment=1)
        self.episode_spin = Gtk.SpinButton(adjustment=episode_adj, digits=0)
        self.episode_spin.connect("value-changed", self.on_config_changed)
        grid.attach(self.episode_spin, 5, row, 1, 1)

        row += 1

        # Source Extension
        grid.attach(Gtk.Label(label="Source Extension:", xalign=1), 0, row, 1, 1)
        ext_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.source_ext_entry = Gtk.Entry()
        self.source_ext_entry.set_text(self.settings.get("source_extension", ".ts"))
        self.source_ext_entry.set_max_width_chars(10)
        self.source_ext_entry.connect("changed", self.on_extension_changed)
        ext_box.pack_start(self.source_ext_entry, False, False, 0)

        # All files checkbox
        self.all_files_check = Gtk.CheckButton(label="All extensions")
        self.all_files_check.set_tooltip_text("Match files regardless of extension")
        self.all_files_check.set_active(self.settings.get("all_files", False))
        self.all_files_check.connect("toggled", self.on_all_files_toggled)
        ext_box.pack_start(self.all_files_check, False, False, 0)

        # Set initial state of source extension field based on "All files" checkbox
        self.source_ext_entry.set_sensitive(not self.all_files_check.get_active())

        grid.attach(ext_box, 1, row, 1, 1)

        # Target Extension
        grid.attach(Gtk.Label(label="Target Extension:", xalign=1), 2, row, 1, 1)
        self.target_ext_entry = Gtk.Entry()
        self.target_ext_entry.set_text(self.settings.get("target_extension", ".mp4"))
        self.target_ext_entry.set_max_width_chars(10)
        self.target_ext_entry.connect("changed", self.on_config_changed)
        grid.attach(self.target_ext_entry, 3, row, 1, 1)

        # Sort by
        grid.attach(Gtk.Label(label="Sort by:", xalign=1), 4, row, 1, 1)
        self.sort_combo = Gtk.ComboBoxText()
        self.sort_combo.append("ctime_asc", "Creation Date (Ascending)")
        self.sort_combo.append("ctime_desc", "Creation Date (Descending)")
        self.sort_combo.append("mtime_asc", "Modification Date (Ascending)")
        self.sort_combo.append("mtime_desc", "Modification Date (Descending)")
        self.sort_combo.append("name_asc", "Name (A-Z)")
        self.sort_combo.append("name_desc", "Name (Z-A)")
        self.sort_combo.set_active_id(self.settings.get("sort_by", "ctime_asc"))
        self.sort_combo.connect("changed", self.on_sort_changed)
        grid.attach(self.sort_combo, 5, row, 1, 1)

        return grid

    def create_file_list(self):
        """Create the file list view"""
        file_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)

        # Select All / Deselect All buttons
        sel_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        sel_box.set_margin_start(3)
        sel_box.set_margin_top(3)

        select_all_btn = Gtk.Button(label="Select All")
        select_all_btn.connect("clicked", self.on_select_all)
        sel_box.pack_start(select_all_btn, False, False, 0)

        deselect_all_btn = Gtk.Button(label="Deselect All")
        deselect_all_btn.connect("clicked", self.on_deselect_all)
        sel_box.pack_start(deselect_all_btn, False, False, 0)

        file_box.pack_start(sel_box, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # ListStore: selected, filename, full_path
        self.file_store = Gtk.ListStore(bool, str, str)

        self.file_tree_view = Gtk.TreeView(model=self.file_store)
        self.file_tree_view.set_headers_visible(True)
        self.file_tree_view.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        # Column: Checkbox
        toggle_renderer = Gtk.CellRendererToggle()
        toggle_renderer.connect("toggled", self.on_file_toggled)
        toggle_col = Gtk.TreeViewColumn("", toggle_renderer, active=0)
        self.file_tree_view.append_column(toggle_col)

        # Column: Filename
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Original Filename", renderer, text=1)
        column.set_expand(True)
        self.file_tree_view.append_column(column)

        scrolled.add(self.file_tree_view)
        file_box.pack_start(scrolled, True, True, 0)
        return file_box

    def create_preview_list(self):
        """Create the preview list view"""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # ListStore: original_name, arrow, new_name, full_path, fg_color
        self.preview_store = Gtk.ListStore(str, str, str, str, str)

        tree_view = Gtk.TreeView(model=self.preview_store)
        tree_view.set_headers_visible(True)

        # Original filename
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Original", renderer, text=0)
        column.set_expand(True)
        tree_view.append_column(column)

        # Arrow
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("", renderer, text=1)
        tree_view.append_column(column)

        # New filename - foreground color bound to column 4
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("New Name", renderer, text=2, foreground=4)
        column.set_expand(True)
        tree_view.append_column(column)

        scrolled.add(tree_view)
        return scrolled

    def create_action_buttons(self):
        """Create bottom action buttons"""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.END)

        # Save Settings button
        save_settings_btn = Gtk.Button(label="Save Settings")
        save_settings_btn.connect("clicked", self.on_save_settings)
        button_box.pack_start(save_settings_btn, False, False, 0)

        # Undo button
        self.undo_button = Gtk.Button(label="Undo Last Rename")
        self.undo_button.set_sensitive(False)
        self.undo_button.get_style_context().add_class("destructive-action")
        self.undo_button.connect("clicked", self.on_undo_clicked)
        button_box.pack_start(self.undo_button, False, False, 0)

        # Rename button
        self.rename_button = Gtk.Button(label="Rename Files")
        self.rename_button.set_sensitive(False)
        self.rename_button.set_tooltip_text("Rename files (Ctrl+R)")
        self.rename_button.get_style_context().add_class("suggested-action")
        self.rename_button.connect("clicked", self.on_rename_clicked)
        button_box.pack_start(self.rename_button, False, False, 0)

        return button_box

    def apply_styling(self):
        """Apply Nemo-like styling"""
        css_provider = Gtk.CssProvider()
        css = b"""
        window {
            background-color: #f5f5f5;
        }
        frame > border {
            border-radius: 3px;
        }
        """
        css_provider.load_from_data(css)

        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_window_configure(self, widget, event):
        """Track window size changes for persistence"""
        self.settings["window_width"] = event.width
        self.settings["window_height"] = event.height

    def on_window_delete(self, widget, event):
        """Save window size on close"""
        self.save_settings()
        return False

    def on_folder_selected(self, widget):
        """Handle folder selection"""
        self.current_folder = widget.get_filename()
        self.load_files()

    def load_files(self):
        """Load files from selected folder"""
        if not self.current_folder:
            return

        self.file_store.clear()
        self.files = []

        all_files_mode = self.all_files_check.get_active()

        source_ext = self.source_ext_entry.get_text().strip()
        if not source_ext.startswith('.'):
            source_ext = '.' + source_ext

        # Validate source extension when filtering by extension
        if not all_files_mode and not self._is_valid_extension(source_ext):
            self.file_frame.set_label("Files to Rename")
            self.update_preview()
            return

        # Get files
        try:
            for entry in os.listdir(self.current_folder):
                full_path = os.path.join(self.current_folder, entry)
                if os.path.isfile(full_path):
                    # If "All files" is checked, include all files
                    # Otherwise, only include files with matching extension
                    if all_files_mode or entry.lower().endswith(source_ext.lower()):
                        self.files.append(full_path)
        except Exception as e:
            self.show_error(f"Error loading files: {e}")
            return

        # Sort files
        self.sort_files()

        # Update file list (all files selected by default)
        for file_path in self.files:
            self.file_store.append([True, os.path.basename(file_path), file_path])
        self._update_file_frame_label()

        # Update preview
        self.update_preview()

    def sort_files(self):
        """Sort files based on selected criteria"""
        sort_by = self.sort_combo.get_active_id()

        if sort_by == "ctime_asc":
            self.files.sort(key=lambda f: os.path.getctime(f))
        elif sort_by == "ctime_desc":
            self.files.sort(key=lambda f: os.path.getctime(f), reverse=True)
        elif sort_by == "mtime_asc":
            self.files.sort(key=lambda f: os.path.getmtime(f))
        elif sort_by == "mtime_desc":
            self.files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        elif sort_by == "name_asc":
            self.files.sort(key=lambda f: os.path.basename(f).lower())
        elif sort_by == "name_desc":
            self.files.sort(key=lambda f: os.path.basename(f).lower(), reverse=True)
        # Fallback for old settings format
        elif sort_by == "ctime":
            self.files.sort(key=lambda f: os.path.getctime(f))
        elif sort_by == "mtime":
            self.files.sort(key=lambda f: os.path.getmtime(f))
        elif sort_by == "name":
            self.files.sort(key=lambda f: os.path.basename(f).lower())

    def _get_selected_files(self):
        """Return list of full paths for files with checkbox enabled"""
        return [row[2] for row in self.file_store if row[0]]

    def _update_file_frame_label(self):
        """Update the file frame label with selected/total counts"""
        total = len(self.file_store)
        selected = sum(1 for row in self.file_store if row[0])
        if total == 0:
            self.file_frame.set_label("Files to Rename")
        else:
            self.file_frame.set_label(
                f"Files to Rename ({selected} of {total} selected)"
            )

    def _build_rename_plan(self):
        """Build the rename plan for selected files only"""
        series_name = self.series_entry.get_text().strip()
        season = int(self.season_spin.get_value())
        start_episode = int(self.episode_spin.get_value())
        target_ext = self.target_ext_entry.get_text().strip()
        if not target_ext.startswith('.'):
            target_ext = '.' + target_ext

        selected_files = self._get_selected_files()
        plan = []
        for idx, file_path in enumerate(selected_files):
            episode_num = start_episode + idx
            new_name = f"{series_name} - S{season:02d}E{episode_num:02d}{target_ext}"
            new_path = os.path.join(os.path.dirname(file_path), new_name)
            plan.append((file_path, new_path))
        return plan

    def _detect_collisions(self, plan):
        """Detect naming collisions in a rename plan.

        Returns a dict of {dst_path: reason} for each collision:
        - "file already exists": dst exists on disk and isn't being renamed away
        - "duplicate target name": multiple source files share the same dst
        """
        src_set = {src for src, dst in plan}

        dst_counts = {}
        for src, dst in plan:
            dst_counts[dst] = dst_counts.get(dst, 0) + 1

        collisions = {}
        for src, dst in plan:
            if dst_counts[dst] > 1:
                collisions[dst] = "duplicate target name"
            # Don't flag as collision if the existing file is itself being renamed away
            elif dst != src and os.path.exists(dst) and dst not in src_set:
                collisions[dst] = "file already exists"
        return collisions

    def update_preview(self):
        """Update the preview list"""
        self.preview_store.clear()

        series_name = self.series_entry.get_text().strip()
        target_ext = self.target_ext_entry.get_text().strip()
        if not target_ext.startswith('.'):
            target_ext = '.' + target_ext

        selected_files = self._get_selected_files()
        if not series_name or not selected_files or not self._is_valid_extension(target_ext):
            self.rename_button.set_sensitive(False)
            return

        plan = self._build_rename_plan()
        collisions = self._detect_collisions(plan)

        for src, dst in plan:
            original_name = os.path.basename(src)
            new_name = os.path.basename(dst)
            if dst in collisions:
                arrow = "⚠ →"
                fg_color = "#CC0000"
            else:
                arrow = "→"
                fg_color = "#4A90D9"
            self.preview_store.append([original_name, arrow, new_name, src, fg_color])

        self.rename_button.set_sensitive(True)

    def on_config_changed(self, widget):
        """Handle configuration changes"""
        self.update_preview()

    def on_extension_changed(self, widget):
        """Handle source extension change"""
        self.load_files()

    def on_all_files_toggled(self, widget):
        """Handle all files checkbox toggle"""
        # Enable/disable source extension entry based on checkbox state
        is_all_files = widget.get_active()
        self.source_ext_entry.set_sensitive(not is_all_files)
        self.load_files()

    def on_sort_changed(self, widget):
        """Handle sort criteria change"""
        if self.files:
            self.sort_files()
            self.load_files()

    def on_file_toggled(self, renderer, path):
        """Handle individual file checkbox toggle"""
        self.file_store[path][0] = not self.file_store[path][0]
        self._update_file_frame_label()
        self.update_preview()

    def on_select_all(self, widget):
        """Select all files in the list"""
        for row in self.file_store:
            row[0] = True
        self._update_file_frame_label()
        self.update_preview()

    def on_deselect_all(self, widget):
        """Deselect all files in the list"""
        for row in self.file_store:
            row[0] = False
        self._update_file_frame_label()
        self.update_preview()

    def on_save_settings(self, widget):
        """Save current settings"""
        # Preserve window size already tracked by on_window_configure
        width = self.settings.get("window_width", 900)
        height = self.settings.get("window_height", 600)
        self.settings = {
            "series_name": self.series_entry.get_text(),
            "season": int(self.season_spin.get_value()),
            "start_episode": int(self.episode_spin.get_value()),
            "source_extension": self.source_ext_entry.get_text(),
            "target_extension": self.target_ext_entry.get_text(),
            "sort_by": self.sort_combo.get_active_id(),
            "all_files": self.all_files_check.get_active(),
            "window_width": width,
            "window_height": height
        }

        if self.save_settings():
            self._show_result_dialog(
                "Settings Saved",
                "Your default settings have been saved.",
                "Settings Error",
                []
            )

    def on_rename_clicked(self, widget):
        """Handle rename button click"""
        # Confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Confirm Rename"
        )
        selected_count = len(self._get_selected_files())
        dialog.format_secondary_text(
            f"Are you sure you want to rename {selected_count} selected files?"
        )

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            self.perform_rename()

    def perform_rename(self):
        """Perform the actual file renaming"""
        plan = self._build_rename_plan()
        collisions = self._detect_collisions(plan)

        if collisions:
            # Build a human-readable list of collision details
            lines = []
            for dst, reason in collisions.items():
                lines.append(f"• {os.path.basename(dst)} ({reason})")
                if len(lines) == 10:
                    remaining = len(collisions) - 10
                    if remaining:
                        lines.append(f"  … and {remaining} more")
                    break

            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.NONE,
                text="Filename Collisions Detected"
            )
            dialog.format_secondary_text(
                "The following target filenames have conflicts:\n\n" +
                "\n".join(lines) +
                "\n\nHow would you like to proceed?"
            )
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Skip Conflicts", Gtk.ResponseType.NO)
            dialog.add_button("Overwrite", Gtk.ResponseType.YES)
            dialog.set_default_response(Gtk.ResponseType.CANCEL)

            response = dialog.run()
            dialog.destroy()

            if response in (Gtk.ResponseType.CANCEL, Gtk.ResponseType.DELETE_EVENT):
                return
            elif response == Gtk.ResponseType.NO:
                # Remove conflicting entries from the plan
                plan = [(src, dst) for src, dst in plan if dst not in collisions]

        success_count = 0
        errors = []

        # Clear previous undo history and prepare new one
        self.last_rename_operation = []

        for src, dst in plan:
            try:
                if not os.path.exists(src):
                    errors.append(f"{os.path.basename(src)}: source file no longer exists")
                    continue
                os.rename(src, dst)
                self.last_rename_operation.append((src, dst))
                success_count += 1
            except Exception as e:
                errors.append(f"{os.path.basename(src)}: {e}")

        # Enable undo button if any files were successfully renamed
        if success_count > 0:
            self.undo_button.set_sensitive(True)

        # Show results
        self._show_result_dialog(
            "Rename Successful",
            f"Successfully renamed {success_count} files.",
            "Rename Completed with Errors",
            errors
        )

        # Reload files
        self.load_files()

    def on_undo_clicked(self, widget):
        """Handle undo button click"""
        if not self.last_rename_operation:
            return

        # Confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Confirm Undo"
        )
        dialog.format_secondary_text(
            f"Are you sure you want to undo the last rename operation?\n"
            f"This will restore {len(self.last_rename_operation)} files to their original names."
        )

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            self.perform_undo()

    def perform_undo(self):
        """Perform the undo operation"""
        success_count = 0
        errors = []

        # Reverse the rename operations (rename new_path back to old_path)
        for old_path, new_path in self.last_rename_operation:
            try:
                # Check if the new file still exists
                if os.path.exists(new_path):
                    os.rename(new_path, old_path)
                    success_count += 1
                else:
                    errors.append(f"{os.path.basename(new_path)}: File not found")
            except Exception as e:
                errors.append(f"{os.path.basename(new_path)}: {e}")

        # Clear undo history and disable button
        self.last_rename_operation = []
        self.undo_button.set_sensitive(False)

        # Show results
        self._show_result_dialog(
            "Undo Successful",
            f"Successfully restored {success_count} files to their original names.",
            "Undo Completed with Errors",
            errors
        )

        # Reload files
        self.load_files()

    def load_settings(self):
        """Load settings from config file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    return {**self.DEFAULT_SETTINGS, **loaded}
        except Exception as e:
            self.settings_load_error = f"Error loading settings: {e}"

        return dict(self.DEFAULT_SETTINGS)

    def save_settings(self):
        """Save settings to config file"""
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            self.show_error(f"Error saving settings: {e}")
            return False

    def _show_settings_load_warning(self):
        """Show a warning dialog about corrupted settings file"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text="Settings Could Not Be Loaded"
        )
        dialog.format_secondary_text(
            f"Your settings file could not be read and defaults have been "
            f"loaded.\n\n{self.settings_load_error}\n\n"
            f"Settings file: {CONFIG_FILE}"
        )
        dialog.run()
        dialog.destroy()
        return False

    def _is_valid_extension(self, ext):
        """Check if a file extension is valid (not empty or only dots)"""
        return ext.replace('.', '') != ''

    def _show_result_dialog(self, title, success_msg, error_title, errors):
        """Show a result dialog with optional error details.

        Returns None; always shows an OK dialog then destroys it.
        """
        if errors:
            error_text = "\n".join(errors[:5])
            if len(errors) > 5:
                error_text += f"\n... and {len(errors) - 5} more errors"

            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text=error_title
            )
            dialog.format_secondary_text(
                f"{success_msg}\n\nErrors:\n{error_text}"
            )
        else:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=title
            )
            dialog.format_secondary_text(success_msg)
        dialog.run()
        dialog.destroy()

    def show_error(self, message):
        """Show error dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()


def main():
    app = FileRenamer()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
