import customtkinter as ctk
from utils.config import ConfigManager
import os
import glob
import sys

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config = ConfigManager()

        # 1. Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=40, pady=(40, 20))
        
        ctk.CTkLabel(self.header_frame, text="Settings", 
                     font=ctk.CTkFont(size=32, weight="bold")).pack(side="left")

        # 2. Settings Container (Scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # --- LOAD THEMES ---
        self.default_themes = ["blue", "green", "dark-blue"]
        self.custom_themes = self.scan_custom_themes() # Returns dict {Name: Path}
        
        # Prepare list for dropdown
        self.theme_display_names = self.default_themes + list(self.custom_themes.keys())
        
        # Determine current selection display name
        current_val = self.config.get("color_theme")
        self.current_theme_name = current_val # Default fallback
        
        # Check if current config matches a custom theme path
        for name, path in self.custom_themes.items():
            if path == current_val:
                self.current_theme_name = name
                break

        # --- SECTIONS ---
        
        # 1. Appearance Card
        self.create_card("Appearance")
        
        self.add_setting_row(
            "Appearance Mode", 
            "Switch between Light and Dark mode.",
            lambda parent: ctk.CTkOptionMenu(
                parent, 
                values=["System", "Light", "Dark"],
                command=self.change_appearance_mode,
                width=200
            ),
            self.config.get("appearance_mode")
        )
        
        self.add_separator()

        self.add_setting_row(
            "Color Theme", 
            "Accent color. Changing this will restart the app.",
            lambda parent: ctk.CTkOptionMenu(
                parent, 
                values=self.theme_display_names,
                command=self.change_color_theme,
                width=200
            ),
            self.current_theme_name
        )

        # 2. Notifications Card
        self.create_card("Notifications")
        
        # Switch Creation Logic
        def create_notif_switch(parent):
            return ctk.CTkSwitch(
                parent, 
                text="", 
                command=self.toggle_notifications,
                onvalue=True, 
                offvalue=False,
                width=60,
                height=30
            )

        self.notif_switch = self.add_setting_row(
            "Desktop Notifications", 
            "Get reminders for tasks due now.",
            create_notif_switch,
            None
        )
        
        # Initialize Switch State Manually
        if self.config.get("notifications_enabled"):
            self.notif_switch.select()
        else:
            self.notif_switch.deselect()

        # 3. About Card
        self.create_card("About")
        
        about_frame = ctk.CTkFrame(self.current_card, fg_color="transparent")
        about_frame.pack(fill="x", padx=25, pady=15)
        
        ctk.CTkLabel(about_frame, text="My Modern Todo", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(about_frame, text="Version 1.0.0", text_color="gray").pack(anchor="w")
        ctk.CTkLabel(about_frame, text="A simple, elegant task manager built with Python and CustomTkinter.", 
                     text_color="gray60", wraplength=400, justify="left").pack(anchor="w", pady=(5, 0))

    # --- HELPERS ---

    def scan_custom_themes(self):
        """Scans assets/themes/ for .json files"""
        themes = {}
        theme_dir = "assets/themes"
        if os.path.exists(theme_dir):
            files = glob.glob(os.path.join(theme_dir, "*.json"))
            for f in files:
                # Clean name: "assets/themes\my_theme.json" -> "My Theme"
                filename = os.path.basename(f)
                name = filename.replace(".json", "").replace("_", " ").title()
                themes[name] = f # Store path
        return themes

    def create_card(self, title):
        """Creates a rounded visual container for a group of settings"""
        # Spacer
        ctk.CTkFrame(self.scroll_frame, height=10, fg_color="transparent").pack()
        
        # Card Frame
        self.current_card = ctk.CTkFrame(self.scroll_frame, fg_color=("white", "gray20"), corner_radius=15)
        self.current_card.pack(fill="x", padx=20)
        
        # Card Title
        title_lbl = ctk.CTkLabel(self.current_card, text=title, font=ctk.CTkFont(size=18, weight="bold"),
                                 text_color=("gray20", "gray80"))
        title_lbl.pack(anchor="w", padx=25, pady=(20, 10))

    def add_setting_row(self, title, description, render_widget_func, current_value):
        """Adds a consistent row: Text on left, Widget on right"""
        # Improved Layout using Grid for better vertical alignment
        row = ctk.CTkFrame(self.current_card, fg_color="transparent")
        row.pack(fill="x", padx=25, pady=12)
        
        row.grid_columnconfigure(0, weight=1) # Text expands
        row.grid_columnconfigure(1, weight=0) # Widget fixed
        
        # Left Side: Text
        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.grid(row=0, column=0, sticky="w")
        
        ctk.CTkLabel(text_frame, text=title, font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(text_frame, text=description, font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")
        
        # Right Side: Widget (Centered vertically)
        # Create widget with 'row' as parent
        widget = render_widget_func(row)
        widget.grid(row=0, column=1, sticky="e")
        
        # Set Value if applicable
        if current_value is not None and hasattr(widget, "set"):
            widget.set(current_value)
            
        return widget

    def add_separator(self):
        """Adds a thin line inside the card"""
        line = ctk.CTkFrame(self.current_card, height=1, fg_color=("gray90", "gray30"))
        line.pack(fill="x", padx=25, pady=5)

    # --- ACTIONS ---

    def change_appearance_mode(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self.config.set("appearance_mode", new_appearance_mode)

    def change_color_theme(self, display_name: str):
        # Determine actual value (path or default name)
        value = display_name
        
        # Check if it's a custom theme name
        if display_name in self.custom_themes:
            value = self.custom_themes[display_name]
            
        self.config.set("color_theme", value)
        
        # Restart the application
        print(f"Theme set to: {value}. Restarting app...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def toggle_notifications(self):
        val = self.notif_switch.get()
        self.config.set("notifications_enabled", bool(val))