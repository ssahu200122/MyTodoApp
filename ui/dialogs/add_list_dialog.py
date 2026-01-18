import customtkinter as ctk
from database.setup import SessionLocal
from database.models import TodoList

class AddListDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_close=None):
        super().__init__(parent)
        self.on_close = on_close
        self.session = SessionLocal()

        # 1. Window Setup
        self.title("New List")
        self.geometry("300x180")
        self.resizable(False, False)
        
        # 2. Input Field
        self.label = ctk.CTkLabel(self, text="List Name:")
        self.label.pack(pady=(20, 5))
        
        self.name_entry = ctk.CTkEntry(self, width=200)
        self.name_entry.pack(pady=5)
        self.name_entry.focus() # Focus so user can type immediately

        # 3. Buttons
        self.save_btn = ctk.CTkButton(self, text="Create", command=self.create_list)
        self.save_btn.pack(pady=20)
        
        # Ensure window is on top
        self.attributes("-topmost", True)

    def create_list(self):
        name = self.name_entry.get().strip()
        if not name:
            return

        # Check if list already exists to prevent duplicates
        exists = self.session.query(TodoList).filter_by(name=name).first()
        if exists:
            # In a real app we would show an error label
            print("List already exists") 
            return

        # Save to DB
        new_list = TodoList(name=name)
        self.session.add(new_list)
        self.session.commit()

        # Notify Sidebar to refresh
        if self.on_close:
            self.on_close()
        
        self.destroy()