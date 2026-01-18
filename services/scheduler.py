from apscheduler.schedulers.background import BackgroundScheduler
from database.setup import SessionLocal
from database.models import TodoItem
from datetime import datetime, timedelta
from plyer import notification
from utils.config import ConfigManager # <--- IMPORT CONFIG
import sys

class NotificationService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.config = ConfigManager() # <--- INIT CONFIG
        # Run the check function every 60 seconds
        self.scheduler.add_job(self.check_due_tasks, 'interval', seconds=60)

    def start(self):
        """Starts the background scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            print("Background Scheduler Started.")

    def stop(self):
        """Stops the scheduler safely"""
        if self.scheduler.running:
            self.scheduler.shutdown()

    def check_due_tasks(self):
        """Queries DB for tasks due right now"""
        # CHECK CONFIG FIRST
        if not self.config.get("notifications_enabled"):
            return

        # We must create a new session for this thread
        session = SessionLocal()
        try:
            now = datetime.now()
            
            # We look for tasks due within the current minute window
            # e.g., if now is 10:30:45, we look for 10:30:00 to 10:31:00
            start_window = now.replace(second=0, microsecond=0)
            end_window = start_window + timedelta(minutes=1)

            tasks = session.query(TodoItem).filter(
                TodoItem.is_completed == False,
                TodoItem.due_date >= start_window,
                TodoItem.due_date < end_window
            ).all()

            for task in tasks:
                self.send_notification(task)
                
        except Exception as e:
            print(f"Scheduler Error: {e}")
        finally:
            session.close()

    def send_notification(self, task):
        print(f"triggering notification for: {task.title}")
        try:
            notification.notify(
                title="Task Due Now!",
                message=f"{task.title}",
                app_name="MyTodo",
                timeout=10  # Seconds to stay on screen
            )
        except Exception as e:
            print(f"Failed to send notification: {e}")
            # Fallback for systems where plyer might fail
            print("\a") # System beep