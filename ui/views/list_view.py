import customtkinter as ctk
from database.setup import SessionLocal
from database.models import TodoList, TodoItem
from datetime import datetime, timedelta
from ui.dialogs.task_dialog import TaskDetailDialog
from PIL import Image
import os
import calendar

# ... (MoveTaskDialog remains unchanged) ...
class MoveTaskDialog(ctk.CTkToplevel):
    def __init__(self, parent, session, task, on_close):
        super().__init__(parent)
        self.session = session
        self.task = task
        self.on_close = on_close
        self.title("Move Task")
        self.geometry("300x160")
        self.resizable(False, False)
        
        # Get Lists
        self.lists = self.session.query(TodoList).all()
        self.list_names = [l.name for l in self.lists]
        self.list_map = {l.name: l.id for l in self.lists}
        
        # Get current list name
        current = self.session.query(TodoList).get(self.task.list_id)
        current_name = current.name if current else self.list_names[0]
        
        # Layout
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.main, text="Move to List:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        
        self.var = ctk.StringVar(value=current_name)
        self.opt = ctk.CTkOptionMenu(self.main, values=self.list_names, variable=self.var)
        self.opt.pack(fill="x", pady=5)
        
        ctk.CTkButton(self.main, text="Move", command=self.move).pack(pady=(20, 0), fill="x")
        
        # Modal
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()
        self.grab_set()
        
    def move(self):
        target = self.var.get()
        if target in self.list_map:
            self.task.list_id = self.list_map[target]
            self.session.commit()
            if self.on_close:
                self.on_close()
        self.destroy()

class TodoListView(ctk.CTkFrame):
    def __init__(self, master, current_list, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.current_list = current_list 
        self.session = SessionLocal()

        # Load Icons with Theme Support
        self.icon_edit = self.load_themed_icon("assets/edit_icon.png", (20, 20))
        self.icon_delete = self.load_themed_icon("assets/delete_icon.png", (20, 20))
        self.icon_move = self.load_themed_icon("assets/move_icon.png", (20, 20))
        # Smaller search icon for inside the box
        self.icon_search = self.load_themed_icon("assets/search_icon.png", (16, 16)) 

        # 1. Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(20, 5))

        # Title
        self.title_label = ctk.CTkLabel(self.header_frame, text=self.current_list.name, 
                                        font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(side="left")

        # Add Button (Packed First to stay on the Far Right)
        self.add_btn = ctk.CTkButton(self.header_frame, text="+ Add New", width=100, height=32,
                                     font=ctk.CTkFont(size=14, weight="bold"),
                                     command=self.open_add_dialog)
        self.add_btn.pack(side="right")

        # SEARCH BAR (Custom Frame to look like Entry)
        # These colors mimic the default CTkEntry look
        entry_bg = ("#F9F9FA", "#343638")
        entry_border = ("#979DA2", "#565B5E")
        
        self.search_container = ctk.CTkFrame(self.header_frame, 
                                             width=220, 
                                             height=32, 
                                             corner_radius=6,
                                             fg_color=entry_bg,
                                             border_width=1, 
                                             border_color=entry_border)
        self.search_container.pack(side="right", padx=(10, 10))
        
        # This prevents the container from shrinking to fit the content, keeping it 220px wide
        self.search_container.pack_propagate(False)

        # Search Icon (Inside Container)
        if self.icon_search:
            self.search_icon_lbl = ctk.CTkLabel(self.search_container, text="", image=self.icon_search)
            self.search_icon_lbl.pack(side="left", padx=(8, 2))

        # Search Entry (Inside Container - Transparent & Borderless)
        self.search_entry = ctk.CTkEntry(self.search_container, 
                                         placeholder_text="Search...", 
                                         border_width=0, 
                                         fg_color="transparent",
                                         height=28)
        self.search_entry.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", self.on_search_change)

        # 2. Tabs
        self.tab_var = ctk.StringVar(value="Inbox")
        self.tabs = ctk.CTkSegmentedButton(self, values=["Inbox", "Today", "Upcoming", "Overdue", "Pending", "Done"],
                                           command=self.on_tab_change,
                                           variable=self.tab_var)
        self.tabs.pack(fill="x", padx=30, pady=(10, 20))

        # 3. Tasks Container
        self.tasks_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.tasks_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.refresh_tasks()

    def load_themed_icon(self, path, size):
        if not os.path.exists(path): return None
        try:
            original = Image.open(path).convert("RGBA")
            white_solid = Image.new("RGBA", original.size, "white")
            white_icon = Image.new("RGBA", original.size, (0, 0, 0, 0))
            white_icon.paste(white_solid, (0, 0), original)
            black_solid = Image.new("RGBA", original.size, "black")
            black_icon = Image.new("RGBA", original.size, (0, 0, 0, 0))
            black_icon.paste(black_solid, (0, 0), original)
            return ctk.CTkImage(light_image=black_icon, dark_image=white_icon, size=size)
        except: return None

    def update_title(self, new_name):
        self.title_label.configure(text=new_name)

    def on_tab_change(self, value):
        self.refresh_tasks()
        
    def on_search_change(self, event=None):
        self.refresh_tasks()

    def refresh_tasks(self):
        self.session.expire_all()
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()

        now = datetime.now()
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_tomorrow = start_of_today + timedelta(days=1)
        current_tab = self.tab_var.get()
        # Get value directly from entry
        search_query = self.search_entry.get().lower()

        try:
            query = self.session.query(TodoItem).filter(TodoItem.list_id == self.current_list.id)
        except:
            return

        # 1. Apply Search Filter
        if search_query:
            query = query.filter(TodoItem.title.ilike(f"%{search_query}%"))

        # 2. Apply Tabs
        tasks = []
        is_grouped = False

        if current_tab == "Today":
            query = query.filter(TodoItem.due_date >= start_of_today,
                                 TodoItem.due_date < start_of_tomorrow)
            query = query.order_by(TodoItem.is_completed)
            tasks = query.all()
            
        elif current_tab == "Upcoming":
            # 1. Fetch real upcoming tasks
            query = query.filter(TodoItem.due_date >= start_of_tomorrow)
            query = query.order_by(TodoItem.due_date, TodoItem.is_completed)
            tasks = query.all()
            
            # 2. Project Recurring Tasks (Virtual)
            # Find all active tasks with recurrence (even if not currently in "Upcoming" DB query)
            if not search_query: # Only show projections if not searching
                all_recurring = self.session.query(TodoItem).filter(
                    TodoItem.list_id == self.current_list.id,
                    TodoItem.is_completed == False,
                    TodoItem.recurrence != None
                ).all()
                
                projected_tasks = self.generate_projections(all_recurring, start_of_tomorrow)
                tasks.extend(projected_tasks)
                
                # Sort combined list by date
                tasks.sort(key=lambda x: x.due_date if x.due_date else datetime.max)

            is_grouped = True

        elif current_tab == "Overdue":
            query = query.filter(TodoItem.due_date < now, TodoItem.is_completed == False)
            query = query.order_by(TodoItem.due_date)
            tasks = query.all()

        elif current_tab == "Done":
            query = query.filter(TodoItem.is_completed == True)
            query = query.order_by(TodoItem.due_date.desc())
            tasks = query.all()

        elif current_tab == "Pending":
            query = query.filter(TodoItem.is_completed == False)
            query = query.order_by(TodoItem.due_date)
            tasks = query.all()
            
        else: # Inbox
            query = query.order_by(TodoItem.is_completed)
            tasks = query.all()

        if not tasks:
            msg = "No tasks found" if not search_query else f"No results for '{search_query}'"
            lbl = ctk.CTkLabel(self.tasks_frame, text=msg, text_color="gray")
            lbl.pack(pady=20)
            return

        if is_grouped and not search_query:
            self.render_grouped_tasks(tasks)
        else:
            for task in tasks:
                self.create_task_widget(task)

    def generate_projections(self, recurring_tasks, start_from):
        """Generates virtual TodoItem objects for the next 30 days"""
        projections = []
        end_date = start_from + timedelta(days=30) # Project 1 month ahead
        
        for task in recurring_tasks:
            if not task.due_date: continue
            
            current_date = task.due_date
            
            # Find next occurrences
            while True:
                next_date = None
                if task.recurrence == "Daily":
                    next_date = current_date + timedelta(days=1)
                elif task.recurrence == "Weekly":
                    next_date = current_date + timedelta(weeks=1)
                elif task.recurrence == "Monthly":
                    year = current_date.year + (current_date.month // 12)
                    month = (current_date.month % 12) + 1
                    day = min(current_date.day, calendar.monthrange(year, month)[1])
                    next_date = current_date.replace(year=year, month=month, day=day)
                
                if not next_date or next_date > end_date:
                    break
                
                current_date = next_date
                
                # Only add if it falls in the "Upcoming" window
                if current_date >= start_from:
                    # Create a "Virtual" object (Not added to DB session)
                    virtual_task = TodoItem()
                    virtual_task.id = "VIRTUAL" # Flag to disable editing
                    virtual_task.title = task.title
                    virtual_task.description = task.description
                    virtual_task.priority = task.priority
                    virtual_task.due_date = current_date
                    virtual_task.recurrence = task.recurrence
                    virtual_task.is_completed = False
                    virtual_task.list_id = task.list_id
                    
                    projections.append(virtual_task)
        
        return projections

    def render_grouped_tasks(self, tasks):
        current_header = None
        for task in tasks:
            date_str = "No Date"
            if task.due_date:
                dt = task.due_date.date()
                today = datetime.now().date()
                tomorrow = today + timedelta(days=1)
                
                if dt == tomorrow:
                    date_str = "Tomorrow"
                else:
                    date_str = dt.strftime("%A, %b %d")
            
            if date_str != current_header:
                current_header = date_str
                header_frame = ctk.CTkFrame(self.tasks_frame, fg_color="transparent")
                header_frame.pack(fill="x", pady=(15, 5))
                ctk.CTkLabel(header_frame, text=current_header, 
                             font=ctk.CTkFont(size=15, weight="bold"),
                             text_color=("gray30", "gray70")).pack(side="left", padx=5)
                line = ctk.CTkFrame(header_frame, height=2, fg_color=("gray80", "gray40"))
                line.pack(side="left", fill="x", expand=True, padx=(10, 5))

            self.create_task_widget(task)

    def create_task_widget(self, task):
        # Check if Virtual
        is_virtual = (task.id == "VIRTUAL")
        
        is_done = task.is_completed
        card_bg = ("white", "gray20")
        if is_done:
            card_bg = ("gray95", "gray15") 
        if is_virtual:
            card_bg = ("white", "gray20") # Keep normal, but maybe distinct later
            
        title_color = ("gray10", "gray90") if not is_done else "gray60"
        if is_virtual:
            title_color = ("gray50", "gray50") # Dimmer text for projections

        row_frame = ctk.CTkFrame(self.tasks_frame, fg_color=card_bg, corner_radius=8)
        row_frame.pack(fill="x", pady=4, padx=5)
        row_frame.grid_columnconfigure(1, weight=1)

        # Checkbox (Disabled for Virtual)
        chk_state = "disabled" if is_virtual else "normal"
        chk = ctk.CTkCheckBox(row_frame, text="", width=24, height=24, 
                              checkbox_width=22, checkbox_height=22, 
                              corner_radius=11, border_width=2,
                              state=chk_state,
                              command=lambda t=task: self.toggle_task(t))
        if is_done: chk.select()
        chk.grid(row=0, column=0, padx=(12, 8), pady=12, sticky="n")

        content_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        content_frame.grid(row=0, column=1, sticky="nsew", pady=8)

        # Title
        title_text = task.title
        if is_virtual: title_text += " (Future)"
        
        title_font = ctk.CTkFont(size=14, weight="normal" if is_done else "bold", overstrike=is_done)
        lbl_title = ctk.CTkLabel(content_frame, text=title_text, font=title_font, 
                                 text_color=title_color, anchor="w")
        lbl_title.pack(fill="x", anchor="w")
        
        # Description
        if task.description:
            desc_text = task.description.replace("\n", " ")
            if len(desc_text) > 80: desc_text = desc_text[:80] + "..."
            lbl_desc = ctk.CTkLabel(content_frame, text=desc_text, 
                                  font=ctk.CTkFont(size=12), text_color=("gray40", "gray60"), anchor="w")
            lbl_desc.pack(fill="x", anchor="w", pady=(0, 2))

        # Details
        # Handle case where subtasks might not exist on virtual objects (list vs query result)
        total_subs = len(task.subtasks) if hasattr(task, 'subtasks') else 0
        done_subs = len([s for s in task.subtasks if s.is_completed]) if hasattr(task, 'subtasks') else 0
        
        has_details = (task.priority != "Medium" and task.priority is not None) or task.due_date or total_subs > 0 or task.recurrence
        
        if has_details:
            details_frame = ctk.CTkFrame(content_frame, fg_color="transparent", height=18)
            details_frame.pack(fill="x", anchor="w", pady=(2, 4))

            if task.priority == "High":
                prio_lbl = ctk.CTkLabel(details_frame, text="High Priority", text_color="#E53935", 
                                      font=ctk.CTkFont(size=11, weight="bold"))
                prio_lbl.pack(side="left", padx=(0, 10))
            elif task.priority == "Low":
                prio_lbl = ctk.CTkLabel(details_frame, text="Low Priority", text_color="#43A047", 
                                      font=ctk.CTkFont(size=11, weight="bold"))
                prio_lbl.pack(side="left", padx=(0, 10))

            if task.due_date:
                date_str = task.due_date.strftime("%b %d %H:%M")
                is_overdue = (not is_done) and (task.due_date < datetime.now()) and not is_virtual
                date_color = "#E53935" if is_overdue else "gray50"
                date_lbl = ctk.CTkLabel(details_frame, text=f"📅 {date_str}", text_color=date_color, 
                                      font=ctk.CTkFont(size=11))
                date_lbl.pack(side="left", padx=(0, 10))
            
            if task.recurrence:
                rec_lbl = ctk.CTkLabel(details_frame, text=f"🔁 {task.recurrence}", text_color="gray50",
                                     font=ctk.CTkFont(size=11))
                rec_lbl.pack(side="left", padx=(0, 10))

            if total_subs > 0:
                sub_color = "gray50"
                if done_subs == total_subs: sub_color = "#43A047"
                sub_lbl = ctk.CTkLabel(details_frame, text=f"Subtasks: {done_subs}/{total_subs}", 
                                     text_color=sub_color, font=ctk.CTkFont(size=11))
                sub_lbl.pack(side="left")

        # Subtasks (Skip for Virtual)
        if hasattr(task, 'subtasks') and task.subtasks and not is_virtual:
            sub_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            sub_frame.pack(fill="x", pady=(2, 0))
            sorted_subs = sorted(task.subtasks, key=lambda s: (s.is_completed, s.id))
            for sub in sorted_subs:
                self.create_subtask_widget(sub_frame, sub)

        # Actions (Skip for Virtual)
        if not is_virtual:
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=2, padx=10, sticky="ne", pady=8)

            if self.icon_edit:
                btn_edit = ctk.CTkButton(actions_frame, text="", image=self.icon_edit, width=30, height=30, 
                                         fg_color="transparent", hover_color=("gray90", "gray30"),
                                         command=lambda t=task: self.open_edit_dialog(t))
            else:
                btn_edit = ctk.CTkButton(actions_frame, text="✎", width=30, height=30, 
                                         fg_color="transparent", text_color="gray60",
                                         command=lambda t=task: self.open_edit_dialog(t))
            btn_edit.pack(side="left", padx=(0, 2))

            if self.icon_move:
                btn_move = ctk.CTkButton(actions_frame, text="", image=self.icon_move, width=30, height=30, 
                                         fg_color="transparent", hover_color=("gray90", "gray30"),
                                         command=lambda t=task: self.open_move_dialog(t))
            else:
                btn_move = ctk.CTkButton(actions_frame, text="➜", width=30, height=30, 
                                         fg_color="transparent", text_color="gray60",
                                         command=lambda t=task: self.open_move_dialog(t))
            btn_move.pack(side="left", padx=(0, 2))

            if self.icon_delete:
                btn_del = ctk.CTkButton(actions_frame, text="", image=self.icon_delete, width=30, height=30, 
                                        fg_color="transparent", hover_color=("gray90", "darkred"),
                                        command=lambda t=task: self.delete_task(t))
            else:
                btn_del = ctk.CTkButton(actions_frame, text="×", width=30, height=30, 
                                        fg_color="transparent", text_color="gray60", 
                                        command=lambda t=task: self.delete_task(t))
            btn_del.pack(side="left")

    def create_subtask_widget(self, parent_frame, subtask):
        st_row = ctk.CTkFrame(parent_frame, fg_color="transparent")
        st_row.pack(fill="x", pady=1)
        is_sub_done = subtask.is_completed
        sub_text_color = "gray60" if is_sub_done else ("gray30", "gray80")
        sub_font = ctk.CTkFont(size=12, overstrike=is_sub_done)
        sub_chk = ctk.CTkCheckBox(st_row, text=subtask.title, text_color=sub_text_color, font=sub_font,
                                  width=18, height=18, checkbox_width=16, checkbox_height=16,
                                  corner_radius=4, border_width=1,
                                  command=lambda s=subtask: self.toggle_subtask(s))
        if is_sub_done: sub_chk.select()
        sub_chk.pack(anchor="w")

    def open_add_dialog(self):
        due = None
        current_tab = self.tab_var.get()
        if current_tab == "Today": due = datetime.now()
        elif current_tab == "Upcoming": due = datetime.now() + timedelta(days=1)
        TaskDetailDialog(self, task_id=None, list_id=self.current_list.id, default_date=due, on_close=self.refresh_tasks)

    def open_move_dialog(self, task):
        MoveTaskDialog(self, self.session, task, on_close=self.refresh_tasks)

    def open_edit_dialog(self, task):
        TaskDetailDialog(self, task_id=task.id, on_close=self.refresh_tasks)

    def toggle_task(self, task):
        if task.id == "VIRTUAL": return # Safety check
        was_completed = task.is_completed
        task.is_completed = not task.is_completed
        if not was_completed and task.is_completed and task.recurrence:
            self.handle_recurrence(task)
        self.session.commit()
        self.refresh_tasks()

    def handle_recurrence(self, task):
        if not task.due_date: return
        new_date = None
        if task.recurrence == "Daily":
            new_date = task.due_date + timedelta(days=1)
        elif task.recurrence == "Weekly":
            new_date = task.due_date + timedelta(weeks=1)
        elif task.recurrence == "Monthly":
            year = task.due_date.year + (task.due_date.month // 12)
            month = (task.due_date.month % 12) + 1
            day = min(task.due_date.day, calendar.monthrange(year, month)[1])
            new_date = task.due_date.replace(year=year, month=month, day=day)
        
        if new_date:
            new_task = TodoItem(
                title=task.title,
                description=task.description,
                priority=task.priority,
                due_date=new_date,
                recurrence=task.recurrence,
                list_id=task.list_id
            )
            self.session.add(new_task)
            task.recurrence = None 

    def toggle_subtask(self, subtask):
        subtask.is_completed = not subtask.is_completed
        self.session.commit()
        self.refresh_tasks()

    def delete_task(self, task):
        self.session.delete(task)
        self.session.commit()
        self.refresh_tasks()