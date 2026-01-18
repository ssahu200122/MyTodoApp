import customtkinter as ctk
from ui.sidebar import Sidebar
from ui.views.list_view import TodoListView
from ui.views.settings_view import SettingsView
from database.setup import SessionLocal, init_db
from database.models import TodoList
from services.scheduler import NotificationService
from utils.config import ConfigManager
import pystray
from PIL import Image, ImageDraw
import threading
import sys
import os
import ctypes # Required for Taskbar Icon fix

# Initialize Config FIRST to set theme before window loads
config = ConfigManager()
ctk.set_appearance_mode(config.get("appearance_mode"))
ctk.set_default_color_theme(config.get("color_theme"))

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- FIX 1: TASKBAR ICON ---
        # Tells Windows this is a unique app, not just "Python", allowing the custom icon to show on the Taskbar
        try:
            myappid = 'myorg.mytodo.modern.1.0' 
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

        # --- FIX 2: WINDOW ICON ---
        # Locate the asset correctly whether running as code or as EXE
        if getattr(sys, 'frozen', False):
            # If run as EXE, assets are next to the executable
            application_path = os.path.dirname(sys.executable)
        else:
            # If run as script, assets are next to the script
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(application_path, "assets", "logo.ico")
        
        if os.path.exists(icon_path):
            self.iconbitmap(default=icon_path) # Standard Tkinter method to set .ico
        
        # 1. Setup DB and ensure Default List exists
        init_db()
        self.session = SessionLocal()
        self.ensure_default_list()

        # 2. Start Notification Scheduler
        self.notifier = NotificationService()
        self.notifier.start()

        # 3. Window Setup
        self.title("My Modern Todo")
        self.geometry("1100x700")
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 4. Sidebar
        self.sidebar = Sidebar(self, 
                               on_navigate=self.navigate,
                               on_settings=self.open_settings,
                               on_list_changed=self.handle_list_change,
                               width=250, 
                               corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 5. Content Area
        self.current_view = None
        
        # Load the default list on startup
        default_list = self.session.query(TodoList).filter_by(is_default=True).first()
        if default_list:
            self.navigate(default_list)
            self.sidebar.highlight_button(default_list.id)

        # 6. Handle App Closing -> Minimize to Tray
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.tray_icon = None

    def ensure_default_list(self):
        """Creates a 'Personal' list if DB is empty"""
        if not self.session.query(TodoList).first():
            print("Creating Default List...")
            default_list = TodoList(name="Personal", is_default=True)
            self.session.add(default_list)
            self.session.commit()

    def navigate(self, todo_list):
        """Switches view to the selected TodoList object"""
        if self.current_view is not None:
            self.current_view.destroy()

        self.current_view = TodoListView(self, current_list=todo_list)
        self.current_view.grid(row=0, column=1, sticky="nsew")

    def open_settings(self):
        """Switches view to the Settings page"""
        if self.current_view is not None:
            self.current_view.destroy()
            
        self.current_view = SettingsView(self)
        self.current_view.grid(row=0, column=1, sticky="nsew")

    def handle_list_change(self, action, todo_list):
        """Called when sidebar performs an action (rename/delete)"""
        if action == "delete":
            self.sidebar.refresh_lists()
            # Check if current view is the deleted list OR Settings view
            is_list_view = isinstance(self.current_view, TodoListView)
            
            if is_list_view and self.current_view.current_list.id == todo_list.id:
                first_available = self.session.query(TodoList).first()
                if first_available:
                    self.navigate(first_available)
                    self.sidebar.highlight_button(first_available.id)
                else:
                    self.ensure_default_list()
                    new_default = self.session.query(TodoList).first()
                    self.navigate(new_default)
                    self.sidebar.refresh_lists()
                    self.sidebar.highlight_button(new_default.id)
        
        elif action == "rename":
            is_list_view = isinstance(self.current_view, TodoListView)
            if is_list_view and self.current_view.current_list.id == todo_list.id:
                self.current_view.update_title(todo_list.name)

    # --- TRAY ICON LOGIC ---

    def on_closing(self):
        """Hides window instead of closing, starts tray icon"""
        self.withdraw() # Hide the window
        
        # Start tray icon in a separate thread to not block the GUI loop
        threading.Thread(target=self.setup_tray_icon, daemon=True).start()

    def create_default_icon(self):
        """Generates a simple blue square icon if no file found"""
        image = Image.new('RGB', (64, 64), color='dodgerblue')
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill='white')
        return image

    def setup_tray_icon(self):
        """Configures and runs the system tray icon"""
        # Determine path to icon
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(application_path, "assets", "logo.png") # Use PNG for tray, ICO for window

        if os.path.exists(icon_path):
            image = Image.open(icon_path)
        else:
            image = self.create_default_icon()

        menu = (
            pystray.MenuItem("Open MyTodo", self.show_window),
            pystray.MenuItem("Quit", self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("name", image, "MyTodo App", menu)
        self.tray_icon.run()

    def show_window(self, icon=None, item=None):
        """Restores the window from the tray"""
        if self.tray_icon:
            self.tray_icon.stop() # Stop the tray icon loop
            self.tray_icon = None
        
        # Schedule the UI update on the main thread
        self.after(0, self.deiconify)

    def quit_app(self, icon=None, item=None):
        """Completely stops the application"""
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.notifier.stop()
        self.quit()
        sys.exit(0)

if __name__ == "__main__":
    app = App()
    app.mainloop()