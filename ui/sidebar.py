import customtkinter as ctk
from database.setup import SessionLocal
from database.models import TodoList
from ui.dialogs.add_list_dialog import AddListDialog
from PIL import Image
import os

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate=None, on_settings=None, on_list_changed=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_navigate = on_navigate
        self.on_settings = on_settings 
        self.on_list_changed = on_list_changed 
        self.session = SessionLocal()
        self.list_buttons = {} 

        # Load Icons with Theme Support
        self.icon_edit = self.load_themed_icon("assets/edit_icon.png", (16, 16))
        self.icon_delete = self.load_themed_icon("assets/delete_icon.png", (16, 16))
        self.icon_settings = self.load_themed_icon("assets/settings.png", (20, 20)) # New Settings Icon

        # 1. App Logo
        self.logo_label = ctk.CTkLabel(self, text="MyTodo", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # 2. "Lists" Label
        self.lists_label = ctk.CTkLabel(self, text="MY LISTS", anchor="w", font=ctk.CTkFont(size=12, weight="bold"))
        self.lists_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="ew")

        # 3. Scrollable Area for Lists
        self.lists_frame = ctk.CTkScrollableFrame(self, label_text="")
        self.lists_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)

        # 4. Add List Button
        self.btn_add_list = ctk.CTkButton(self, text="+ Add List", 
                                          fg_color="transparent", 
                                          border_width=1, 
                                          text_color=("gray10", "gray90"),
                                          command=self.open_add_list_dialog)
        self.btn_add_list.grid(row=3, column=0, padx=20, pady=(10, 5))

        # 5. Settings Button (Updated)
        if self.icon_settings:
            self.btn_settings = ctk.CTkButton(self, text=" Settings", 
                                              image=self.icon_settings,
                                              fg_color="transparent",
                                              anchor="w",
                                              height=40,
                                              text_color=("gray10", "gray90"),
                                              hover_color=("gray70", "gray30"),
                                              command=self.handle_settings_click)
        else:
            self.btn_settings = ctk.CTkButton(self, text="⚙️ Settings", 
                                              fg_color="transparent",
                                              anchor="w",
                                              height=40,
                                              text_color=("gray10", "gray90"),
                                              hover_color=("gray70", "gray30"),
                                              command=self.handle_settings_click)
                                              
        self.btn_settings.grid(row=4, column=0, padx=10, pady=(5, 20), sticky="ew")
        
        # 6. Initial Load
        self.refresh_lists()

    def load_themed_icon(self, path, size):
        """Creates a CTkImage with Black (Light Mode) and White (Dark Mode) versions"""
        if not os.path.exists(path):
            return None
        try:
            original = Image.open(path).convert("RGBA")
            
            white_solid = Image.new("RGBA", original.size, "white")
            white_icon = Image.new("RGBA", original.size, (0, 0, 0, 0))
            white_icon.paste(white_solid, (0, 0), original)
            
            black_solid = Image.new("RGBA", original.size, "black")
            black_icon = Image.new("RGBA", original.size, (0, 0, 0, 0))
            black_icon.paste(black_solid, (0, 0), original)
            
            return ctk.CTkImage(light_image=black_icon, dark_image=white_icon, size=size)
        except Exception as e:
            print(f"Error loading icon {path}: {e}")
            return None

    def refresh_lists(self):
        """Fetches ALL lists from DB and creates button rows"""
        for widget in self.lists_frame.winfo_children():
            widget.destroy()
        self.list_buttons = {}

        all_lists = self.session.query(TodoList).all()

        for todo_list in all_lists:
            # Row Container
            row = ctk.CTkFrame(self.lists_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            # A. Name Button
            btn = ctk.CTkButton(row, 
                                text=todo_list.name,
                                height=30,
                                fg_color="transparent",
                                anchor="w",
                                text_color=("gray10", "gray90"),
                                hover_color=("gray70", "gray30"),
                                command=lambda l=todo_list: self.handle_click(l))
            btn.pack(side="left", fill="x", expand=True)
            self.list_buttons[todo_list.id] = btn

            # B. Rename Button
            if self.icon_edit:
                btn_edit = ctk.CTkButton(row, text="", image=self.icon_edit, width=24, height=24,
                                         fg_color="transparent", hover_color=("gray85", "gray25"),
                                         command=lambda l=todo_list: self.rename_list(l))
            else:
                btn_edit = ctk.CTkButton(row, text="✎", width=24, height=24,
                                         fg_color="transparent", text_color="gray",
                                         hover_color=("gray85", "gray25"),
                                         command=lambda l=todo_list: self.rename_list(l))
            btn_edit.pack(side="right", padx=1)

            # C. Delete Button
            if self.icon_delete:
                btn_del = ctk.CTkButton(row, text="", image=self.icon_delete, width=24, height=24,
                                        fg_color="transparent", hover_color=("gray85", "gray25"),
                                        command=lambda l=todo_list: self.delete_list(l))
            else:
                btn_del = ctk.CTkButton(row, text="×", width=24, height=24,
                                        fg_color="transparent", text_color="red",
                                        hover_color=("gray85", "gray25"),
                                        command=lambda l=todo_list: self.delete_list(l))
            btn_del.pack(side="right", padx=1)

    def rename_list(self, todo_list):
        dialog = ctk.CTkInputDialog(text="Enter new name:", title="Rename List")
        new_name = dialog.get_input()
        if new_name and new_name.strip():
            todo_list.name = new_name.strip()
            self.session.commit()
            self.refresh_lists()
            self.highlight_button(todo_list.id)
            if self.on_list_changed:
                self.on_list_changed("rename", todo_list)

    def delete_list(self, todo_list):
        self.session.delete(todo_list)
        self.session.commit()
        self.refresh_lists()
        if self.on_list_changed:
            self.on_list_changed("delete", todo_list)

    def open_add_list_dialog(self):
        AddListDialog(self, on_close=self.refresh_lists)

    def handle_click(self, todo_list):
        self.highlight_button(todo_list.id)
        if self.on_navigate:
            self.on_navigate(todo_list)

    def handle_settings_click(self):
        """Highlights settings button and calls callback"""
        for btn in self.list_buttons.values():
            btn.configure(fg_color="transparent")
        
        self.btn_settings.configure(fg_color=("gray75", "gray25"))
        
        if self.on_settings:
            self.on_settings()

    def highlight_button(self, list_id):
        self.btn_settings.configure(fg_color="transparent")
        for btn in self.list_buttons.values():
            btn.configure(fg_color="transparent")
        if list_id in self.list_buttons:
            self.list_buttons[list_id].configure(fg_color=("gray75", "gray25"))