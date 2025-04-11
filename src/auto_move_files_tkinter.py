import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import logging
from datetime import datetime
from auto_move_files import AutoFileMover
import sys

class SimpleAutoFileGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Auto File Organizer")
        self.root.geometry("400x600")
        self.root.configure(bg='#1E1E1E')

        # Define system extensions to ignore
        self.system_extensions = {
            '.ini', '.sys', '.dll', '.exe', '.bat', '.cmd', '.com', '.msi',
            '.tmp', '.log', '.cache', '.lnk', '.url', '.reg', '.drv', '.dat'
        }

        # Initialize AutoFileMover
        self.mover = AutoFileMover()
        self._setup_logger()
        
        # Initialize monitoring state
        self.monitoring = False
        
        self._init_ui()
        self._configure_styles()

    def _setup_logger(self):
        # Get the project root directory (two levels up from the current file)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(project_root, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"auto_filer_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('AutoFiler')

    def _configure_styles(self):
        # Configure style for dark theme
        style = ttk.Style()
        style.configure("Dark.TFrame", background="#1E1E1E")
        style.configure("Dark.TLabel", 
                       background="#1E1E1E", 
                       foreground="white",
                       font=('Segoe UI', 10))
        style.configure("Dark.TButton",
                       padding=5,
                       background="#333333",
                       foreground="white")
        style.configure("Monitor.TButton",
                       padding=10,
                       font=('Segoe UI', 10, 'bold'))

    def _init_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Watch Folders Section
        watch_frame = self._create_section(main_frame, "Watched Folders")
        self.watch_list = tk.Listbox(watch_frame, height=5, bg='#2A2A2A', fg='white')
        self.watch_list.pack(fill=tk.X, pady=5)
        
        watch_btn_frame = ttk.Frame(watch_frame, style="Dark.TFrame")
        watch_btn_frame.pack(fill=tk.X)
        ttk.Button(watch_btn_frame, text="Add Folder", 
                   command=self.add_watch_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(watch_btn_frame, text="Remove Folder", 
                   command=self.remove_watch_folder).pack(side=tk.LEFT, padx=2)

        # Extension Mappings Section
        mappings_frame = self._create_section(main_frame, "Extension Mappings")
        self.mappings_list = tk.Listbox(mappings_frame, height=5, bg='#2A2A2A', fg='white')
        self.mappings_list.pack(fill=tk.X, pady=5)
        
        mappings_btn_frame = ttk.Frame(mappings_frame, style="Dark.TFrame")
        mappings_btn_frame.pack(fill=tk.X)
        ttk.Button(mappings_btn_frame, text="Add Extension", 
                   command=self.add_extension).pack(side=tk.LEFT, padx=2)
        ttk.Button(mappings_btn_frame, text="Remove Extension", 
                   command=self.remove_extension).pack(side=tk.LEFT, padx=2)

        # Detected Extensions Section
        detected_frame = self._create_section(main_frame, "Detected Extensions")
        self.detected_list = tk.Listbox(detected_frame, height=5, bg='#2A2A2A', fg='white')
        self.detected_list.pack(fill=tk.X, pady=5)
        
        detected_btn_frame = ttk.Frame(detected_frame, style="Dark.TFrame")
        detected_btn_frame.pack(fill=tk.X)
        ttk.Button(detected_btn_frame, text="Refresh", 
                   command=self._scan_for_extensions).pack(side=tk.LEFT, padx=2)
        ttk.Button(detected_btn_frame, text="Add Selected", 
                   command=self.add_selected_extension).pack(side=tk.LEFT, padx=2)

        # Create frame for monitor button and log button
        button_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        button_frame.pack(pady=10)

        self.monitor_button = ttk.Button(button_frame, text="Start Monitoring",
                                       command=self.toggle_monitoring,
                                       style="Monitor.TButton")
        self.monitor_button.pack(side=tk.LEFT, padx=5)

        log_button = ttk.Button(button_frame, text="View Logs",
                               command=self.open_latest_log,
                               style="Monitor.TButton")
        log_button.pack(side=tk.LEFT, padx=5)

        # Status Label
        self.status_label = ttk.Label(main_frame, 
                                    text="Ready", 
                                    style="Dark.TLabel",
                                    background="#2A2A2A",
                                    foreground="#45A262")
        self.status_label.pack(fill=tk.X, pady=5)

        # Load initial data
        self._load_current_config()
        self._scan_for_extensions()

    def _create_section(self, parent, title):
        frame = ttk.Frame(parent, style="Dark.TFrame")
        frame.pack(fill=tk.X, pady=5)
        ttk.Label(frame, text=title, style="Dark.TLabel").pack(anchor=tk.W)
        return frame

    def _load_current_config(self):
        # Load watch directories
        for directory in self.mover.get_watch_directories():
            self.watch_list.insert(tk.END, directory)
        
        # Load extension mappings
        self._update_extension_list()

    def _update_extension_list(self):
        self.mappings_list.delete(0, tk.END)
        for ext, dest in self.mover.get_extension_mappings().items():
            self.mappings_list.insert(tk.END, f"{ext} → {dest or 'None'}")

    def add_watch_folder(self):
        folder = filedialog.askdirectory(title="Select folder to watch")
        if folder:
            self.mover.add_watch_directory(folder)
            self.watch_list.insert(tk.END, folder)
            self._update_status(f"Added watch folder: {folder}")

    def remove_watch_folder(self):
        selection = self.watch_list.curselection()
        if selection:
            folder = self.watch_list.get(selection[0])
            self.mover.remove_watch_directory(folder)
            self.watch_list.delete(selection[0])
            self._update_status(f"Removed watch folder: {folder}")

    def add_extension(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Extension Mapping")
        dialog.geometry("300x150")
        dialog.configure(bg='#1E1E1E')
        
        ttk.Label(dialog, text="Extension (e.g., .pdf):", style="Dark.TLabel").pack(pady=5)
        ext_entry = ttk.Entry(dialog)
        ext_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Destination folder:", style="Dark.TLabel").pack(pady=5)
        dest_entry = ttk.Entry(dialog)
        dest_entry.pack(pady=5)
        
        def save_mapping():
            ext = ext_entry.get().strip()
            dest = dest_entry.get().strip()
            if ext and dest:
                self.mover.set_extension_destination(ext, dest)
                self._update_extension_list()
                self._scan_for_extensions()
                dialog.destroy()
        
        ttk.Button(dialog, text="Save", command=save_mapping).pack(pady=10)

    def remove_extension(self):
        selection = self.mappings_list.curselection()
        if selection:
            ext = self.mappings_list.get(selection[0]).split(" → ")[0]
            self.mover.set_extension_destination(ext, None)
            self._update_extension_list()
            self._update_status(f"Removed mapping for: {ext}")

    def _scan_for_extensions(self):
        self.detected_list.delete(0, tk.END)
        extensions = set()
        mapped_extensions = set(self.mover.get_extension_mappings().keys())
        
        for watch_dir in self.mover.get_watch_directories():
            if os.path.exists(watch_dir):
                self._update_status(f"Scanning directory: {watch_dir}")
                for file in os.listdir(watch_dir):
                    filepath = os.path.join(watch_dir, file)
                    if os.path.isfile(filepath):
                        _, ext = os.path.splitext(file.lower())
                        if ext and ext not in self.system_extensions and ext not in mapped_extensions:
                            extensions.add(ext)
        
        for ext in sorted(extensions):
            self.detected_list.insert(tk.END, ext)
        
        self._update_status(f"Found {len(extensions)} unmapped extensions")

    def add_selected_extension(self):
        selection = self.detected_list.curselection()
        if selection:
            ext = self.detected_list.get(selection[0])
            dialog = tk.Toplevel(self.root)
            dialog.title("Add Extension Mapping")
            dialog.geometry("400x200")
            dialog.configure(bg='#1E1E1E')
            
            ttk.Label(dialog, text="Extension:", style="Dark.TLabel").pack(pady=5)
            ext_label = ttk.Label(dialog, text=ext, style="Dark.TLabel")
            ext_label.pack(pady=5)
            
            ttk.Label(dialog, text="Destination folder:", style="Dark.TLabel").pack(pady=5)
            
            dest_frame = ttk.Frame(dialog, style="Dark.TFrame")
            dest_frame.pack(fill=tk.X, padx=20, pady=5)
            
            dest_entry = ttk.Entry(dest_frame)
            dest_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
            
            def browse_folder():
                folder = filedialog.askdirectory(title="Select destination folder")
                if folder:
                    dest_entry.delete(0, tk.END)
                    dest_entry.insert(0, folder)
            
            browse_btn = ttk.Button(dest_frame, text="Browse", command=browse_folder)
            browse_btn.pack(side=tk.RIGHT)
            
            def save_mapping():
                dest = dest_entry.get().strip()
                if dest:
                    self.mover.set_extension_destination(ext, dest)
                    self._update_extension_list()
                    self._scan_for_extensions()
                    dialog.destroy()
            
            ttk.Button(dialog, text="Save", command=save_mapping).pack(pady=10)

    def toggle_monitoring(self):
        if not self.monitoring:
            self.monitoring = True
            self.monitor_button.configure(text="Stop Monitoring")
            self._update_status("File monitoring started")
            self._monitor()
        else:
            self.monitoring = False
            self.monitor_button.configure(text="Start Monitoring")
            self._update_status("File monitoring stopped")

    def _monitor(self):
        if self.monitoring:
            try:
                self.mover.move_files()
                self._update_status("Checking for files...")
                self.root.after(5000, self._monitor)  # Check every 5 seconds
            except Exception as e:
                error_msg = f"Error during monitoring: {str(e)}"
                self._update_status(error_msg, level="error")

    def _update_status(self, message, level="info"):
        self.status_label.configure(text=message)
        
        if level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def open_latest_log(self):
        """Open the most recent log file with the default system application."""
        try:
            # Get the project root directory (two levels up from the current file)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(project_root, "logs")
            
            if not os.path.exists(log_dir):
                self._update_status("No log files found - log directory doesn't exist", level="warning")
                return

            # Get list of log files
            log_files = [f for f in os.listdir(log_dir) if f.startswith("auto_filer_") and f.endswith(".log")]
            
            if not log_files:
                self._update_status("No log files found", level="warning")
                return
                
            # Sort by modification time to get the latest
            latest_log = max(log_files, key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))
            log_path = os.path.join(log_dir, latest_log)
            
            # Open the log file with default system application
            if sys.platform == 'win32':
                os.startfile(log_path)
            elif sys.platform == 'darwin':  # macOS
                os.system(f'open "{log_path}"')
            else:  # Linux
                os.system(f'xdg-open "{log_path}"')
                
            self._update_status(f"Opened log file: {latest_log}")
        except Exception as e:
            self._update_status(f"Error opening log file: {str(e)}", level="error")

def main():
    root = tk.Tk()
    app = SimpleAutoFileGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 