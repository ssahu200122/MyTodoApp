from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database.setup import Base

# --- TABLE 1: LISTS ---
class TodoList(Base):
    __tablename__ = 'lists'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    is_default = Column(Boolean, default=False)  # To mark the "Inbox"
    
    # RELATIONSHIP: One List has Many Todos
    # cascade="all, delete" means if we delete a List, all its Todos get deleted too.
    todos = relationship("TodoItem", back_populates="parent_list", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<List(name='{self.name}')>"

# --- TABLE 2: TODOS ---
class TodoItem(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True) # Text is for longer content
    
    # Dates
    created_at = Column(DateTime, default=datetime.now)
    due_date = Column(DateTime, nullable=True)
    
    # Status & Priority
    is_completed = Column(Boolean, default=False)
    priority = Column(String, default="Medium") # Low, Medium, High
    
    # Recurrence (We will store this as a simple string for now, e.g., "DAILY")
    recurrence = Column(String, nullable=True)

    # FOREIGN KEY: Linking to the List
    list_id = Column(Integer, ForeignKey('lists.id'), nullable=False)
    
    # RELATIONSHIPS
    parent_list = relationship("TodoList", back_populates="todos")
    subtasks = relationship("SubTask", back_populates="parent_todo", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Todo(title='{self.title}', done={self.is_completed})>"

# --- TABLE 3: SUBTASKS ---
class SubTask(Base):
    __tablename__ = 'subtasks'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    is_completed = Column(Boolean, default=False)

    # FOREIGN KEY: Linking to the Todo
    todo_id = Column(Integer, ForeignKey('todos.id'), nullable=False)
    
    # RELATIONSHIP
    parent_todo = relationship("TodoItem", back_populates="subtasks")

    def __repr__(self):
        return f"<SubTask(title='{self.title}')>"