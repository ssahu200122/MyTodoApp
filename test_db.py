from database.setup import init_db, SessionLocal
from database.models import TodoList, TodoItem, SubTask
from datetime import datetime

# 1. Initialize the Database (Creates the file todo_app.db)
print("Initializing Database...")
init_db()

# 2. Start a Session
session = SessionLocal()

# 3. Create Data
try:
    # Check if we already have data to avoid duplicates
    if not session.query(TodoList).filter_by(name="Inbox").first():
        print("Creating 'Inbox' List...")
        
        # A. Create List
        inbox = TodoList(name="Inbox", is_default=True)
        session.add(inbox)
        session.commit() # Save to get the ID
        
        # B. Create Todo (Linked to Inbox)
        task1 = TodoItem(
            title="Learn CustomTkinter", 
            description="Read the documentation",
            priority="High",
            due_date=datetime.now(),
            parent_list=inbox # We pass the object, SQLAlchemy handles the ID!
        )
        session.add(task1)
        session.commit()

        # C. Create Subtask (Linked to Todo)
        sub1 = SubTask(title="Install Library", parent_todo=task1)
        session.add(sub1)
        session.commit()
        
        print("Data created successfully!")
    else:
        print("Data already exists.")

    # 4. Verify Data (Read it back)
    my_list = session.query(TodoList).first()
    print(f"\nList Found: {my_list.name}")
    print(f"Tasks in List: {my_list.todos}")
    print(f"Subtasks in First Task: {my_list.todos[0].subtasks}")

except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()