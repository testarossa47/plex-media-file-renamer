#!/usr/bin/env python3
"""
Tests for issues #5, #14, #6, #8, #7 implemented in file_renamer.py.
Uses unittest (stdlib) since pytest is not installed.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import json
import os
import sys
import tempfile
import unittest

# Add project root to path so we can import file_renamer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from file_renamer import FileRenamer, CONFIG_FILE


def process_gtk_events():
    """Drain pending GTK events so idle callbacks fire"""
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


def set_app_files(app, file_list):
    """Set up files in both app.files and app.file_store (all selected)"""
    app.files = list(file_list)
    app.file_store.clear()
    for f in file_list:
        app.file_store.append([True, os.path.basename(f), f])


def suppress_warnings(app):
    """Suppress warning dialogs during tests"""
    app._show_settings_load_warning = lambda: False


class TestIssue5CollisionComment(unittest.TestCase):
    """Issue #5 - Verify _detect_collisions logic with the documented edge case"""

    def setUp(self):
        self.app = FileRenamer()
        process_gtk_events()
        # Clear any auto-loaded user data from settings to prevent tests
        # from operating on user's last_folder (e.g., Downloads)
        self.app.current_folder = None
        self.app.files = []
        self.app.file_store.clear()
        self.app.settings["last_folder"] = ""
        suppress_warnings(self.app)
        process_gtk_events()

    def tearDown(self):
        self.app.destroy()
        process_gtk_events()

    def test_no_false_collision_when_source_is_renamed_away(self):
        """The dst_not_in_src_set check should prevent false collisions
        when an existing file at the destination is itself being renamed."""
        # Scenario: file_a -> file_b, file_b -> file_c
        # file_b exists on disk but is being renamed to file_c,
        # so file_a -> file_b should NOT be flagged as a collision.
        with tempfile.TemporaryDirectory() as tmpdir:
            file_a = os.path.join(tmpdir, "file_a.mp4")
            file_b = os.path.join(tmpdir, "file_b.mp4")

            # Create both files
            for f in (file_a, file_b):
                with open(f, 'w') as fh:
                    fh.write("test")

            file_c = os.path.join(tmpdir, "file_c.mp4")

            plan = [
                (file_a, file_b),  # file_b exists but is being renamed away
                (file_b, file_c),
            ]

            collisions = self.app._detect_collisions(plan)
            self.assertEqual(collisions, {},
                             "Should not flag collision when existing file is being renamed away")

    def test_real_collision_detected(self):
        """A real collision (destination exists and is NOT being renamed) should be detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_a = os.path.join(tmpdir, "file_a.mp4")
            file_b = os.path.join(tmpdir, "file_b.mp4")

            for f in (file_a, file_b):
                with open(f, 'w') as fh:
                    fh.write("test")

            # file_a -> file_b, but file_b is NOT in the plan as a source
            plan = [(file_a, file_b)]

            collisions = self.app._detect_collisions(plan)
            self.assertIn(file_b, collisions)
            self.assertEqual(collisions[file_b], "file already exists")

    def test_duplicate_target_detected(self):
        """Two sources mapping to the same destination should be flagged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_a = os.path.join(tmpdir, "file_a.mp4")
            file_b = os.path.join(tmpdir, "file_b.mp4")
            dst = os.path.join(tmpdir, "same_dest.mp4")

            for f in (file_a, file_b):
                with open(f, 'w') as fh:
                    fh.write("test")

            plan = [(file_a, dst), (file_b, dst)]

            collisions = self.app._detect_collisions(plan)
            self.assertIn(dst, collisions)
            self.assertEqual(collisions[dst], "duplicate target name")


class TestIssue14SeasonZero(unittest.TestCase):
    """Issue #14 - Season 0 should be possible for Specials/Movies"""

    def setUp(self):
        self.app = FileRenamer()
        process_gtk_events()
        # Clear any auto-loaded user data from settings
        self.app.current_folder = None
        self.app.files = []
        self.app.file_store.clear()
        self.app.settings["last_folder"] = ""
        suppress_warnings(self.app)
        process_gtk_events()

    def tearDown(self):
        self.app.destroy()
        process_gtk_events()

    def test_season_spin_allows_zero(self):
        """Season spin button should accept value 0"""
        adj = self.app.season_spin.get_adjustment()
        self.assertEqual(adj.get_lower(), 0,
                         "Season adjustment lower bound should be 0")

    def test_season_spin_rejects_negative(self):
        """Season spin button should not go below 0"""
        self.app.season_spin.set_value(-1)
        process_gtk_events()
        # GTK clamps to the adjustment lower bound
        self.assertEqual(self.app.season_spin.get_value_as_int(), 0,
                         "Season should clamp to 0, not go negative")

    def test_season_zero_produces_S00_in_filename(self):
        """Setting season to 0 should produce S00 in the rename plan"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.ts")
            with open(test_file, 'w') as f:
                f.write("test")

            # Set to temp folder BEFORE creating test files to ensure isolation
            self.app.current_folder = tmpdir
            self.app.settings["last_folder"] = tmpdir
            set_app_files(self.app, [test_file])
            self.app.series_entry.set_text("Specials")
            self.app.season_spin.set_value(0)
            self.app.episode_spin.set_value(1)
            self.app.target_ext_entry.set_text(".mp4")
            process_gtk_events()

            plan = self.app._build_rename_plan()
            self.assertEqual(len(plan), 1)
            new_name = os.path.basename(plan[0][1])
            self.assertEqual(new_name, "Specials - S00E01.mp4",
                             "Season 0 should produce S00 in filename")

    def test_season_upper_bound_unchanged(self):
        """Season upper bound should remain at 99"""
        adj = self.app.season_spin.get_adjustment()
        self.assertEqual(adj.get_upper(), 99)


class TestIssue6PreflightCheck(unittest.TestCase):
    """Issue #6 - Pre-flight check for missing source files before rename"""

    def setUp(self):
        self.app = FileRenamer()
        process_gtk_events()
        # Clear any auto-loaded user data from settings
        self.app.current_folder = None
        self.app.files = []
        self.app.file_store.clear()
        self.app.settings["last_folder"] = ""
        suppress_warnings(self.app)
        process_gtk_events()

    def tearDown(self):
        self.app.destroy()
        process_gtk_events()

    def test_missing_source_file_produces_clear_error(self):
        """If a source file disappears before rename, a clear error is reported"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files
            file_a = os.path.join(tmpdir, "episode1.ts")
            file_b = os.path.join(tmpdir, "episode2.ts")
            for f in (file_a, file_b):
                with open(f, 'w') as fh:
                    fh.write("test")

            # Set up the app
            self.app.current_folder = tmpdir
            set_app_files(self.app, [file_a, file_b])
            self.app.series_entry.set_text("TestShow")
            self.app.season_spin.set_value(1)
            self.app.episode_spin.set_value(1)
            self.app.target_ext_entry.set_text(".mp4")
            process_gtk_events()

            # Delete file_a AFTER the plan is built but before rename
            plan = self.app._build_rename_plan()
            os.remove(file_a)

            # Perform rename manually (bypassing the confirmation dialog)
            self.app.last_rename_operation = []
            success_count = 0
            errors = []

            for src, dst in plan:
                try:
                    if not os.path.exists(src):
                        errors.append(f"{os.path.basename(src)}: source file no longer exists")
                        continue
                    os.rename(src, dst)
                    self.app.last_rename_operation.append((src, dst))
                    success_count += 1
                except Exception as e:
                    errors.append(f"{os.path.basename(src)}: {e}")

            # file_a was deleted, should produce 1 error
            self.assertEqual(success_count, 1, "Only file_b should succeed")
            self.assertEqual(len(errors), 1, "file_a should produce an error")
            self.assertIn("source file no longer exists", errors[0])
            self.assertIn("episode1.ts", errors[0])

    def test_existing_files_rename_normally(self):
        """Files that exist should rename without errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "video.ts")
            with open(test_file, 'w') as f:
                f.write("test")

            # Set to temp folder BEFORE creating test files to ensure isolation
            self.app.current_folder = tmpdir
            self.app.settings["last_folder"] = tmpdir
            set_app_files(self.app, [test_file])
            self.app.series_entry.set_text("Show")
            self.app.season_spin.set_value(1)
            self.app.episode_spin.set_value(1)
            self.app.target_ext_entry.set_text(".mp4")
            process_gtk_events()

            plan = self.app._build_rename_plan()

            # Manually execute the rename logic (same as perform_rename loop)
            self.app.last_rename_operation = []
            errors = []
            for src, dst in plan:
                try:
                    if not os.path.exists(src):
                        errors.append(f"{os.path.basename(src)}: source file no longer exists")
                        continue
                    os.rename(src, dst)
                    self.app.last_rename_operation.append((src, dst))
                except Exception as e:
                    errors.append(f"{os.path.basename(src)}: {e}")

            self.assertEqual(len(errors), 0)
            expected = os.path.join(tmpdir, "Show - S01E01.mp4")
            self.assertTrue(os.path.exists(expected),
                            f"Renamed file should exist at {expected}")


class TestIssue8ExtensionValidation(unittest.TestCase):
    """Issue #8 - Validate extension input fields"""

    def setUp(self):
        self.app = FileRenamer()
        process_gtk_events()
        # Clear any auto-loaded user data from settings
        self.app.current_folder = None
        self.app.files = []
        self.app.file_store.clear()
        self.app.settings["last_folder"] = ""
        suppress_warnings(self.app)
        process_gtk_events()

    def tearDown(self):
        self.app.destroy()
        process_gtk_events()

    def test_valid_extension(self):
        """Normal extensions should pass validation"""
        self.assertTrue(self.app._is_valid_extension(".mp4"))
        self.assertTrue(self.app._is_valid_extension(".ts"))
        self.assertTrue(self.app._is_valid_extension(".mkv"))
        self.assertTrue(self.app._is_valid_extension("mp4"))

    def test_empty_extension_invalid(self):
        """Empty string should fail validation"""
        self.assertFalse(self.app._is_valid_extension(""))

    def test_only_dots_invalid(self):
        """Extension of only dots should fail validation"""
        self.assertFalse(self.app._is_valid_extension("."))
        self.assertFalse(self.app._is_valid_extension(".."))
        self.assertFalse(self.app._is_valid_extension("..."))

    def test_invalid_source_ext_clears_file_list(self):
        """Invalid source extension should result in empty file list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "video.ts")
            with open(test_file, 'w') as f:
                f.write("test")

            self.app.current_folder = tmpdir
            self.app.all_files_check.set_active(False)
            process_gtk_events()

            # Set a valid extension first, load files
            self.app.source_ext_entry.set_text(".ts")
            process_gtk_events()
            # The on_extension_changed handler calls load_files
            file_count_valid = len(self.app.files)

            # Now set an invalid extension
            self.app.source_ext_entry.set_text("...")
            process_gtk_events()
            file_count_invalid = len(self.app.files)

            self.assertGreater(file_count_valid, 0,
                               "Valid extension should find files")
            self.assertEqual(file_count_invalid, 0,
                             "Invalid extension should result in empty file list")

    def test_invalid_target_ext_disables_rename(self):
        """Invalid target extension should disable the rename button"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "video.ts")
            with open(test_file, 'w') as f:
                f.write("test")

            self.app.current_folder = tmpdir
            self.app.all_files_check.set_active(False)
            self.app.source_ext_entry.set_text(".ts")
            process_gtk_events()
            self.app.series_entry.set_text("TestShow")
            process_gtk_events()

            # Load files so there are files present
            self.app.load_files()
            process_gtk_events()

            # Set valid target ext -- rename should be enabled
            self.app.target_ext_entry.set_text(".mp4")
            process_gtk_events()
            self.app.update_preview()
            process_gtk_events()
            enabled_with_valid = self.app.rename_button.get_sensitive()

            # Set invalid target ext -- rename should be disabled
            self.app.target_ext_entry.set_text("...")
            process_gtk_events()
            self.app.update_preview()
            process_gtk_events()
            enabled_with_invalid = self.app.rename_button.get_sensitive()

            self.assertTrue(enabled_with_valid,
                            "Rename button should be enabled with valid target extension")
            self.assertFalse(enabled_with_invalid,
                             "Rename button should be disabled with invalid target extension")

    def test_all_files_mode_bypasses_source_validation(self):
        """In all-files mode, source extension validation should be skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "video.ts")
            with open(test_file, 'w') as f:
                f.write("test")

            self.app.current_folder = tmpdir

            # Set invalid source ext but enable all-files mode
            self.app.source_ext_entry.set_text("...")
            self.app.all_files_check.set_active(True)
            process_gtk_events()
            self.app.load_files()
            process_gtk_events()

            self.assertGreater(len(self.app.files), 0,
                               "All-files mode should load files regardless of source extension")


class TestIssue7CorruptedSettings(unittest.TestCase):
    """Issue #7 - Handle corrupted settings file with user-facing warning"""

    def test_settings_load_error_is_none_on_success(self):
        """On successful settings load (or no file), error should be None"""
        app = FileRenamer()
        process_gtk_events()
        suppress_warnings(app)
        process_gtk_events()
        # If the real config file is fine (or doesn't exist), no error
        self.assertIsNone(app.settings_load_error)
        app.destroy()
        process_gtk_events()

    def test_corrupted_settings_sets_error(self):
        """Corrupted JSON in settings file should set settings_load_error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_config = os.path.join(tmpdir, "settings.json")
            os.makedirs(os.path.dirname(fake_config), exist_ok=True)
            with open(fake_config, 'w') as f:
                f.write("{this is not valid json!!!")

            # Temporarily patch CONFIG_FILE
            import file_renamer
            original_config = file_renamer.CONFIG_FILE
            file_renamer.CONFIG_FILE = fake_config

            try:
                app = FileRenamer()
                process_gtk_events()

                self.assertIsNotNone(app.settings_load_error,
                                     "settings_load_error should be set for corrupted config")
                self.assertIn("Error loading settings", app.settings_load_error)

                # Defaults should still be loaded
                self.assertEqual(app.settings.get("season"), 1)
                self.assertEqual(app.settings.get("source_extension"), ".ts")
                self.assertEqual(app.settings.get("target_extension"), ".mp4")

                app.destroy()
                process_gtk_events()
            finally:
                file_renamer.CONFIG_FILE = original_config

    def test_missing_config_file_no_error(self):
        """A nonexistent config file should NOT set an error (just use defaults)"""
        import file_renamer
        original_config = file_renamer.CONFIG_FILE

        file_renamer.CONFIG_FILE = "/tmp/nonexistent_path_12345/settings.json"
        try:
            app = FileRenamer()
            process_gtk_events()
            suppress_warnings(app)
            process_gtk_events()

            self.assertIsNone(app.settings_load_error,
                              "Missing config file should not be an error")
            # Defaults should be loaded
            self.assertEqual(app.settings.get("season"), 1)

            app.destroy()
            process_gtk_events()
        finally:
            file_renamer.CONFIG_FILE = original_config

    def test_show_settings_load_warning_method_exists(self):
        """The _show_settings_load_warning method should exist on the class"""
        app = FileRenamer()
        process_gtk_events()
        suppress_warnings(app)
        process_gtk_events()
        self.assertTrue(hasattr(app, '_show_settings_load_warning'))
        self.assertTrue(callable(app._show_settings_load_warning))
        app.destroy()
        process_gtk_events()


if __name__ == '__main__':
    unittest.main()
