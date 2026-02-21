"""
╔══════════════════════════════════════════════════════════════╗
║              🤖 KAZUHA VIP DISCORD AUTO BOT                  ║
║                  Created by Kazuha VIP Only                  ║
╚══════════════════════════════════════════════════════════════╝
Task Scheduling Module
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Callable, Any, Optional
from collections import defaultdict

from utils.helpers import Helpers


class ScheduledTask:
    """Represents a scheduled task"""
    
    def __init__(self, name: str, interval_minutes: int, 
                 callback: Callable, jitter: int = 5):
        self.name = name
        self.interval_minutes = interval_minutes
        self.callback = callback
        self.jitter = jitter
        self.next_run: Optional[datetime] = None
        self.last_run: Optional[datetime] = None
        self.run_count = 0
        self.enabled = True
        
    def schedule_next(self):
        """Schedule next run time"""
        interval_seconds = Helpers.get_random_interval(
            self.interval_minutes, 
            self.jitter
        )
        self.next_run = datetime.now() + timedelta(seconds=interval_seconds)
    
    def is_due(self) -> bool:
        """Check if task is due to run"""
        if not self.enabled:
            return False
        if not self.next_run:
            return True
        return datetime.now() >= self.next_run
    
    async def execute(self) -> Any:
        """Execute the task"""
        self.last_run = datetime.now()
        self.run_count += 1
        result = await self.callback()
        self.schedule_next()
        return result


class Scheduler:
    """Manages scheduled tasks with human-like timing"""
    
    def __init__(self, active_hours: list = None):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.active_hours = active_hours or list(range(9, 23))
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
    def add_task(self, name: str, interval_minutes: int, 
                 callback: Callable, jitter: int = 5):
        """Add a new scheduled task"""
        task = ScheduledTask(name, interval_minutes, callback, jitter)
        task.schedule_next()
        self.tasks[name] = task
    
    def remove_task(self, name: str):
        """Remove a scheduled task"""
        if name in self.tasks:
            del self.tasks[name]
    
    def pause_task(self, name: str):
        """Pause a task"""
        if name in self.tasks:
            self.tasks[name].enabled = False
    
    def resume_task(self, name: str):
        """Resume a paused task"""
        if name in self.tasks:
            self.tasks[name].enabled = True
            self.tasks[name].schedule_next()
    
    def is_active_time(self) -> bool:
        """Check if current time is in active hours"""
        return Helpers.is_active_hour(self.active_hours)
    
    async def run(self):
        """Main scheduler loop"""
        self.running = True
        
        while self.running:
            try:
                # Check if in active hours
                if not self.is_active_time():
                    await asyncio.sleep(60)  # Check every minute
                    continue
                
                # Process due tasks
                for name, task in self.tasks.items():
                    if task.is_due():
                        try:
                            await task.execute()
                        except Exception as e:
                            # Log error but continue
                            print(f"Task {name} error: {e}")
                
                # Sleep before next check
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Scheduler error: {e}")
                await asyncio.sleep(30)
    
    def start(self):
        """Start scheduler in background"""
        self._task = asyncio.create_task(self.run())
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self._task:
            self._task.cancel()
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            'running': self.running,
            'active_time': self.is_active_time(),
            'active_hours': f"{self.active_hours[0]}:00 - {self.active_hours[-1]}:00",
            'tasks': {
                name: {
                    'enabled': task.enabled,
                    'interval': f"{task.interval_minutes}m (+{task.jitter}m jitter)",
                    'next_run': task.next_run.strftime('%H:%M:%S') if task.next_run else 'Pending',
                    'run_count': task.run_count
                }
                for name, task in self.tasks.items()
            }
        }