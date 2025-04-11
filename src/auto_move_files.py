import os
import time
import shutil
import json
from tkinter import Tk, filedialog

class AutoFileMover:
    def __init__(self, config_file=None):
        """
        Initialize the AutoFileMover with a config file path.
        
        Args:
            config_file (str, optional): Path to configuration file. If None, uses default path
        """
        if config_file is None:
            config_file = os.path.join(os.path.expanduser("~"), 'auto_move_config.json')
        self.config_file = os.path.expanduser(config_file)
        
        # Load or create configuration
        self.config = self._load_config()
        
        # Ensure required config sections exist
        if 'watch_dirs' not in self.config:
            self.config['watch_dirs'] = []
        if 'extension_dirs' not in self.config:
            self.config['extension_dirs'] = {}
        
        # Create destination directories if they don't exist
        for dest in self.config['extension_dirs'].values():
            if dest:  # Only create if destination is set
                os.makedirs(dest, exist_ok=True)

    def _load_config(self):
        """Load the configuration file if it exists, otherwise return empty dict."""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {}

    def _save_config(self):
        """Save the current configuration to file."""
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)

    def add_watch_directory(self, directory):
        """Add a directory to watch list."""
        directory = os.path.expanduser(directory)
        if directory not in self.config['watch_dirs']:
            self.config['watch_dirs'].append(directory)
            self._save_config()

    def remove_watch_directory(self, directory):
        """Remove a directory from watch list."""
        directory = os.path.expanduser(directory)
        if directory in self.config['watch_dirs']:
            self.config['watch_dirs'].remove(directory)
            self._save_config()

    def set_extension_destination(self, extension, destination):
        """Set the destination directory for a file extension."""
        extension = extension.lower()
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        destination = os.path.expanduser(destination) if destination else None
        self.config['extension_dirs'][extension] = destination
        
        if destination:
            os.makedirs(destination, exist_ok=True)
        
        self._save_config()

    def get_extension_destination(self, extension):
        """Get the destination directory for a file extension."""
        if not extension.startswith('.'):
            extension = f'.{extension}'
        return self.config['extension_dirs'].get(extension.lower())

    def move_files(self):
        """Move files from watch directories to their designated locations."""
        for watch_dir in self.config['watch_dirs']:
            if not os.path.exists(watch_dir):
                continue
                
            for filename in os.listdir(watch_dir):
                filepath = os.path.join(watch_dir, filename)
                if os.path.isfile(filepath):
                    _, extension = os.path.splitext(filename)
                    extension = extension.lower()
                    
                    dest = self.config['extension_dirs'].get(extension)
                    if dest:
                        # Skip if file is already in the correct destination
                        if os.path.dirname(filepath) == dest:
                            continue
                            
                        try:
                            dest_path = os.path.join(dest, filename)
                            # Handle duplicate filenames
                            if os.path.exists(dest_path):
                                base, ext = os.path.splitext(filename)
                                counter = 1
                                while os.path.exists(dest_path):
                                    new_filename = f"{base}_{counter}{ext}"
                                    dest_path = os.path.join(dest, new_filename)
                                    counter += 1
                            
                            print(f"Moving {filename} from {watch_dir} to {dest}")
                            shutil.move(filepath, dest_path)
                        except Exception as e:
                            print(f"Error moving {filename}: {str(e)}")

    def start_monitoring(self, interval=5):
        """
        Start continuous monitoring of the watch directories.
        
        Args:
            interval (int): Time in seconds between checks
        """
        print(f"Monitoring folders: {', '.join(self.config['watch_dirs'])}")
        while True:
            self.move_files()
            time.sleep(interval)

    def get_watch_directories(self):
        """Get list of watched directories."""
        return self.config['watch_dirs']

    def get_extension_mappings(self):
        """Get dictionary of extension to destination mappings."""
        return self.config['extension_dirs']