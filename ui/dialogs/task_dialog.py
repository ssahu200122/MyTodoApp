import customtkinter as ctk
from database.setup import SessionLocal
from database.models import TodoItem, SubTask, TodoList
from datetime import datetime, time
import calendar
from PIL import Image
import os

# --- HELPER: Custom Input Dialog (Topmost) ---
class TopmostInputDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Input", text="Enter value:", default_value=""):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x160")
        self.resizable(False, False)
        self.value = None
        
        # Layout
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.main, text=text, font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        self.entry = ctk.CTkEntry(self.main)
        self.entry.insert(0, default_value)
        self.entry.pack(fill="x", pady=10)
        self.entry.focus()
        self.entry.bind("<Return>", lambda e: self.on_ok())
        
        btn_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="gray", width=80, command=self.destroy).pack(side="right", padx=(10,0))
        ctk.CTkButton(btn_frame, text="OK", width=80, command=self.on_ok).pack(side="right")
        
        # Window Management
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()
        self.grab_set() # Make modal
        
        self.wait_window() # Block until closed

    def on_ok(self):
        self.value = self.entry.get()
        self.destroy()

    def get_input(self):
        return self.value

# --- HELPER: Calendar Date Picker ---
class DatePickerDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_date=None, on_select=None):
        super().__init__(parent)
        self.on_select = on_select
        self.title("Select Date")
        self.geometry("300x320")
        self.resizable(False, False)
        
        # State
        self.selected_date = current_date if current_date else datetime.now()
        self.current_month = self.selected_date.month
        self.current_year = self.selected_date.year
        
        # Main Layout
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header (Month Year + Nav)
        self.header = ctk.CTkFrame(self.main, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 10))
        
        self.btn_prev = ctk.CTkButton(self.header, text="<", width=30, command=self.prev_month)
        self.btn_prev.pack(side="left")
        
        self.lbl_month = ctk.CTkLabel(self.header, text="Month Year", font=ctk.CTkFont(weight="bold", size=16))
        self.lbl_month.pack(side="left", fill="x", expand=True)
        
        self.btn_next = ctk.CTkButton(self.header, text=">", width=30, command=self.next_month)
        self.btn_next.pack(side="right")
        
        # Days Grid
        self.days_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.days_frame.pack(fill="both", expand=True)
        
        # Weekday Headers
        weekdays = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
        for i, day in enumerate(weekdays):
            lbl = ctk.CTkLabel(self.days_frame, text=day, text_color="gray", width=35)
            lbl.grid(row=0, column=i, padx=2, pady=2)
            
        self.build_calendar()
        
        # Window Management
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()
        self.grab_set()

    def build_calendar(self):
        # Clear existing days (rows 1+)
        for widget in self.days_frame.winfo_children():
            if int(widget.grid_info()["row"]) > 0:
                widget.destroy()
        
        # Update Header
        month_name = calendar.month_name[self.current_month]
        self.lbl_month.configure(text=f"{month_name} {self.current_year}")
        
        # Get Month Layout
        cal = calendar.Calendar(firstweekday=6) # Sunday first
        month_days = cal.monthdayscalendar(self.current_year, self.current_month)
        
        for r, week in enumerate(month_days):
            for c, day in enumerate(week):
                if day != 0:
                    # Highlight selected
                    is_selected = (day == self.selected_date.day and 
                                 self.current_month == self.selected_date.month and 
                                 self.current_year == self.selected_date.year)
                    
                    fg_color = "dodgerblue" if is_selected else "transparent"
                    text_color = "white" if is_selected else ("black", "white")
                    
                    btn = ctk.CTkButton(self.days_frame, text=str(day), width=35, height=35,
                                        fg_color=fg_color, text_color=text_color,
                                        command=lambda d=day: self.select_day(d))
                    btn.grid(row=r+1, column=c, padx=2, pady=2)

    def prev_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.build_calendar()

    def next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.build_calendar()

    def select_day(self, day):
        new_date = self.selected_date.replace(year=self.current_year, month=self.current_month, day=day)
        if self.on_select:
            self.on_select(new_date)
        self.destroy()


# --- HELPER: Time Picker Dialog ---
class TimePickerDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_time=None, on_select=None):
        super().__init__(parent)
        self.on_select = on_select
        self.title("Select Time")
        self.geometry("300x200")
        self.resizable(False, False)
        
        target = current_time if current_time else datetime.now().time()
        
        # Layout
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.main, text="Set Time", font=ctk.CTkFont(weight="bold", size=16)).pack(pady=(0, 20))
        
        # Selectors Frame
        sel_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        sel_frame.pack()
        
        # Hour
        hours = [str(h).zfill(2) for h in range(0, 24)]
        self.var_hour = ctk.StringVar(value=str(target.hour).zfill(2))
        self.opt_hour = ctk.CTkOptionMenu(sel_frame, values=hours, variable=self.var_hour, width=70, height=40, font=("Arial", 20))
        self.opt_hour.pack(side="left", padx=5)
        
        ctk.CTkLabel(sel_frame, text=":", font=("Arial", 20)).pack(side="left")
        
        # Minute
        minutes = [str(m).zfill(2) for m in range(0, 60)] # Changed step to 1
        self.var_minute = ctk.StringVar(value=str(target.minute).zfill(2))
        self.opt_minute = ctk.CTkOptionMenu(sel_frame, values=minutes, variable=self.var_minute, width=70, height=40, font=("Arial", 20))
        self.opt_minute.pack(side="left", padx=5)
        
        # Save Button
        ctk.CTkButton(self.main, text="Confirm", command=self.confirm).pack(side="bottom", fill="x")
        
        # Window Management
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()
        self.grab_set()

    def confirm(self):
        t = time(int(self.var_hour.get()), int(self.var_minute.get()))
        if self.on_select:
            self.on_select(t)
        self.destroy()


# --- MAIN DIALOG CLASS ---
class TaskDetailDialog(ctk.CTkToplevel):
    def __init__(self, parent, task_id=None, list_id=None, default_date=None, on_close=None):
        super().__init__(parent)
        self.task_id = task_id
        self.list_id = list_id # Required if task_id is None
        self.on_close = on_close
        self.session = SessionLocal()
        
        # Load Icons with Theme Support
        self.icon_edit = self.load_themed_icon("assets/edit_icon.png", (16, 16))
        self.icon_delete = self.load_themed_icon("assets/delete_icon.png", (16, 16))

        # 1. Fetch Task or Create New Transient Object
        if self.task_id:
            self.task = self.session.query(TodoItem).get(task_id)
            window_title = "Edit Task"
        else:
            # Create a new instance but don't add to DB yet
            self.task = TodoItem(title="", list_id=self.list_id)
            if default_date:
                self.task.due_date = default_date
            window_title = "New Task"

        # Fetch All Lists for Dropdown
        self.all_lists = self.session.query(TodoList).all()
        self.list_names = [l.name for l in self.all_lists]
        self.list_map = {l.name: l.id for l in self.all_lists}
        
        # Determine current list name
        current_list_obj = self.session.query(TodoList).get(self.task.list_id if self.task.list_id else self.list_id)
        current_list_name = current_list_obj.name if current_list_obj else self.list_names[0]

        # Temp variable to hold date before saving
        self.selected_due_date = self.task.due_date

        # 2. Window Setup
        self.title(window_title)
        self.geometry("750x500") # Slightly taller for extra field
        
        # Main Container
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Content Split Container
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, pady=(0, 15))

        # --- LEFT COLUMN (Details) ---
        self.left_col = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Title
        ctk.CTkLabel(self.left_col, text="Title", anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", pady=(0, 2))
        self.title_entry = ctk.CTkEntry(self.left_col)
        self.title_entry.insert(0, self.task.title)
        self.title_entry.pack(fill="x", pady=(0, 10))
        if not self.task_id:
            self.title_entry.focus()

        # Description
        ctk.CTkLabel(self.left_col, text="Description", anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", pady=(0, 2))
        self.desc_entry = ctk.CTkTextbox(self.left_col, height=100)
        if self.task.description:
            self.desc_entry.insert("0.0", self.task.description)
        self.desc_entry.pack(fill="x", pady=(0, 10))

        # Priority
        ctk.CTkLabel(self.left_col, text="Priority", anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", pady=(0, 2))
        self.priority_var = ctk.StringVar(value=self.task.priority or "Medium")
        self.priority_menu = ctk.CTkOptionMenu(self.left_col, values=["Low", "Medium", "High"], 
                                             variable=self.priority_var)
        self.priority_menu.pack(fill="x", pady=(0, 10))

        # List (Move to...)
        ctk.CTkLabel(self.left_col, text="List", anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", pady=(0, 2))
        self.list_var = ctk.StringVar(value=current_list_name)
        self.list_menu = ctk.CTkOptionMenu(self.left_col, values=self.list_names, variable=self.list_var)
        self.list_menu.pack(fill="x", pady=(0, 10))

        # Date & Time
        ctk.CTkLabel(self.left_col, text="Due Date & Time", anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", pady=(0, 2))
        dt_frame = ctk.CTkFrame(self.left_col, fg_color="transparent")
        dt_frame.pack(fill="x", pady=(0, 10))

        self.btn_date = ctk.CTkButton(dt_frame, text="Select Date", fg_color="gray70", text_color="black",
                                      command=self.open_calendar)
        self.btn_date.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_time = ctk.CTkButton(dt_frame, text="Select Time", fg_color="gray70", text_color="black",
                                      command=self.open_time_picker)
        self.btn_time.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Clear Date Button (With Icon)
        if self.icon_delete:
            self.btn_clear_dt = ctk.CTkButton(dt_frame, text="", image=self.icon_delete, width=30, 
                                              fg_color="transparent", hover_color=("gray85", "gray25"), 
                                              command=self.clear_datetime)
        else:
            self.btn_clear_dt = ctk.CTkButton(dt_frame, text="×", width=30, fg_color="transparent", text_color="red",
                                              hover_color=("gray85", "gray25"), command=self.clear_datetime)
        self.btn_clear_dt.pack(side="right", padx=(5, 0))
        
        self.update_datetime_buttons()

        # --- RIGHT COLUMN (Subtasks) ---
        self.right_col = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))

        sub_header = ctk.CTkFrame(self.right_col, fg_color="transparent")
        sub_header.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(sub_header, text="Subtasks", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        self.btn_add_sub = ctk.CTkButton(sub_header, text="+ Add", width=60, height=24, command=self.add_subtask)
        self.btn_add_sub.pack(side="right")

        self.sub_list_frame = ctk.CTkScrollableFrame(self.right_col)
        self.sub_list_frame.pack(fill="both", expand=True, pady=(5, 0))

        self.refresh_subtasks()

        # --- BOTTOM ---
        btn_text = "Create Task" if not self.task_id else "Save All Changes"
        self.save_btn = ctk.CTkButton(self.main_frame, text=btn_text, height=40, font=ctk.CTkFont(weight="bold"), command=self.save_details)
        self.save_btn.pack(side="bottom", fill="x")

        # Window Management
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()

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

    # ... (Date/Time methods unchanged) ...
    def update_datetime_buttons(self):
        if self.selected_due_date:
            date_str = self.selected_due_date.strftime("%Y-%m-%d")
            time_str = self.selected_due_date.strftime("%H:%M")
            self.btn_date.configure(text=date_str, fg_color="dodgerblue", text_color="white")
            self.btn_time.configure(text=time_str, fg_color="dodgerblue", text_color="white")
        else:
            self.btn_date.configure(text="Select Date", fg_color="gray70", text_color="black")
            self.btn_time.configure(text="Select Time", fg_color="gray70", text_color="black")

    def open_calendar(self):
        DatePickerDialog(self, current_date=self.selected_due_date, on_select=self.set_date)

    def set_date(self, new_date):
        current_time = self.selected_due_date.time() if self.selected_due_date else time(0, 0)
        self.selected_due_date = datetime.combine(new_date.date(), current_time)
        self.update_datetime_buttons()

    def open_time_picker(self):
        current = self.selected_due_date.time() if self.selected_due_date else None
        TimePickerDialog(self, current_time=current, on_select=self.set_time)

    def set_time(self, new_time):
        base_date = self.selected_due_date.date() if self.selected_due_date else datetime.now().date()
        self.selected_due_date = datetime.combine(base_date, new_time)
        self.update_datetime_buttons()

    def clear_datetime(self):
        self.selected_due_date = None
        self.update_datetime_buttons()

    # --- SUBTASK LOGIC ---
    def refresh_subtasks(self):
        for w in self.sub_list_frame.winfo_children():
            w.destroy()
            
        subs = sorted(self.task.subtasks, key=lambda x: x.is_completed)

        if not subs:
            ctk.CTkLabel(self.sub_list_frame, text="No subtasks yet.", text_color="gray").pack(pady=10)

        for sub in subs:
            row = ctk.CTkFrame(self.sub_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            text_color = "gray60" if sub.is_completed else ("gray10", "gray90")
            chk = ctk.CTkCheckBox(row, text=sub.title, text_color=text_color,
                                  command=lambda s=sub: self.toggle_subtask(s))
            if sub.is_completed: chk.select()
            chk.pack(side="left", padx=5)
            
            # Delete Button
            if self.icon_delete:
                btn_del = ctk.CTkButton(row, text="", image=self.icon_delete, width=24, height=24,
                                        fg_color="transparent", hover_color=("gray85", "gray25"),
                                        command=lambda s=sub: self.delete_subtask(s))
            else:
                btn_del = ctk.CTkButton(row, text="×", width=24, height=24, fg_color="transparent",
                                        text_color="red", hover_color=("gray85", "gray25"),
                                        command=lambda s=sub: self.delete_subtask(s))
            btn_del.pack(side="right")
            
            # Edit Button
            if self.icon_edit:
                btn_edit = ctk.CTkButton(row, text="", image=self.icon_edit, width=24, height=24,
                                         fg_color="transparent", hover_color=("gray85", "gray25"),
                                         command=lambda s=sub: self.edit_subtask(s))
            else:
                btn_edit = ctk.CTkButton(row, text="✎", width=24, height=24, fg_color="transparent",
                                        text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                        command=lambda s=sub: self.edit_subtask(s))
            btn_edit.pack(side="right", padx=2)

    def ensure_task_saved(self):
        if not self.task.id:
            self.task.title = self.title_entry.get() or "(No Title)" 
            self.task.priority = self.priority_var.get()
            self.session.add(self.task)
            self.session.commit()
            self.task_id = self.task.id 

    def add_subtask(self):
        self.ensure_task_saved()
        dialog = TopmostInputDialog(self, title="New Subtask", text="Enter subtask title:")
        text = dialog.get_input()
        if text and text.strip():
            new_sub = SubTask(title=text.strip(), parent_todo=self.task)
            self.session.add(new_sub)
            self.session.commit()
            self.refresh_subtasks()

    def edit_subtask(self, subtask):
        dialog = TopmostInputDialog(self, title="Edit Subtask", text="Edit subtask title:", default_value=subtask.title)
        text = dialog.get_input()
        if text and text.strip():
            subtask.title = text.strip()
            self.session.commit()
            self.refresh_subtasks()

    def toggle_subtask(self, subtask):
        subtask.is_completed = not subtask.is_completed
        self.session.commit()
        self.refresh_subtasks()

    def delete_subtask(self, subtask):
        self.session.delete(subtask)
        self.session.commit()
        self.refresh_subtasks()

    def save_details(self):
        self.task.title = self.title_entry.get()
        self.task.description = self.desc_entry.get("0.0", "end").strip()
        self.task.priority = self.priority_var.get()
        self.task.due_date = self.selected_due_date
        
        # Update List ID based on selection
        selected_list_name = self.list_var.get()
        if selected_list_name in self.list_map:
            self.task.list_id = self.list_map[selected_list_name]

        if not self.task.id:
            self.session.add(self.task)
        self.session.commit()
        if self.on_close:
            self.on_close()
        self.destroy()