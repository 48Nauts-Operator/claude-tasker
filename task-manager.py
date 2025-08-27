#!/usr/bin/env python3
"""
🎯 Claude-Tasker - Core Task Management System
Manages task queue and triggers autonomous Claude execution
"""

import json
import time
import os
import argparse
from pathlib import Path
from datetime import datetime
import subprocess
import threading
import asyncio
import sys

# Import Claude SDK executor
try:
    from claude_sdk_executor import ClaudeSDKExecutor
    CLAUDE_SDK_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Claude SDK not available: {e}")
    print("Install with: pip install anthropic")
    CLAUDE_SDK_AVAILABLE = False

class ClaudeTaskManager:
    def __init__(self):
        """Initialize Claude-Tasker with configuration"""
        self.config_dir = Path.home() / '.claude-tasker'
        self.config_dir.mkdir(exist_ok=True)
        
        self.queue_file = self.config_dir / 'task-queue.jsonl'
        self.completed_file = self.config_dir / 'completed-tasks.jsonl'
        self.execution_log = self.config_dir / 'execution.log'
        self.config_file = self.config_dir / 'config.json'
        
        self.load_config()
        
        # Initialize Claude SDK executor if available
        self.claude_executor = None
        if CLAUDE_SDK_AVAILABLE:
            try:
                self.claude_executor = ClaudeSDKExecutor()
                self._log("✅ Claude SDK initialized successfully")
            except Exception as e:
                self._log(f"❌ Failed to initialize Claude SDK: {e}")
                self._log("💡 Make sure CLAUDE_API_KEY environment variable is set")
        else:
            self._log("⚠️  Claude SDK not available - autonomous execution disabled")
        
    def load_config(self):
        """Load configuration from file or create defaults"""
        default_config = {
            'task_check_interval': 30,
            'max_retry_attempts': 3,
            'enable_auto_execution': True,
            'log_level': 'info',
            'webhook_token': self._generate_token()
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = {**default_config, **json.load(f)}
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save current configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def add_task(self, task, priority=3, tags=None, description=''):
        """Add a task to the queue"""
        if tags is None:
            tags = []
            
        task_obj = {
            'id': f"task_{int(time.time() * 1000)}",
            'task': task,
            'priority': max(1, min(5, priority)),  # Clamp between 1-5
            'tags': tags,
            'description': description,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'attempts': 0,
            'estimated_duration': None,
            'dependencies': []
        }
        
        with open(self.queue_file, 'a') as f:
            f.write(json.dumps(task_obj) + '\n')
        
        self._log(f"✅ Task added: {task} (Priority: {priority})")
        return task_obj['id']
    
    def get_next_task(self):
        """Get highest priority pending task"""
        if not self.queue_file.exists():
            return None
            
        tasks = []
        with open(self.queue_file, 'r') as f:
            for line in f:
                if line.strip():
                    task = json.loads(line)
                    if task['status'] == 'pending':
                        tasks.append(task)
        
        if not tasks:
            return None
            
        # Sort by priority (higher first) then by creation time
        tasks.sort(key=lambda x: (-x['priority'], x['created_at']))
        return tasks[0]
    
    def get_all_tasks(self, status=None, limit=None):
        """Get all tasks, optionally filtered by status"""
        tasks = []
        
        if self.queue_file.exists():
            with open(self.queue_file, 'r') as f:
                for line in f:
                    if line.strip():
                        task = json.loads(line)
                        if status is None or task['status'] == status:
                            tasks.append(task)
        
        # Sort by creation time (newest first)
        tasks.sort(key=lambda x: x['created_at'], reverse=True)
        
        if limit:
            tasks = tasks[:limit]
            
        return tasks
    
    def update_task_status(self, task_id, status, **kwargs):
        """Update task status and other fields"""
        tasks = []
        updated_task = None
        
        if self.queue_file.exists():
            with open(self.queue_file, 'r') as f:
                for line in f:
                    if line.strip():
                        task = json.loads(line)
                        if task['id'] == task_id:
                            task['status'] = status
                            task.update(kwargs)
                            if status == 'completed':
                                task['completed_at'] = datetime.now().isoformat()
                            updated_task = task
                        tasks.append(task)
        
        # Rewrite queue file
        with open(self.queue_file, 'w') as f:
            for task in tasks:
                f.write(json.dumps(task) + '\n')
        
        # Archive completed tasks
        if status == 'completed' and updated_task:
            with open(self.completed_file, 'a') as f:
                f.write(json.dumps(updated_task) + '\n')
        
        return updated_task
    
    def delete_task(self, task_id):
        """Delete a task from the queue"""
        tasks = []
        deleted_task = None
        
        if self.queue_file.exists():
            with open(self.queue_file, 'r') as f:
                for line in f:
                    if line.strip():
                        task = json.loads(line)
                        if task['id'] != task_id:
                            tasks.append(task)
                        else:
                            deleted_task = task
        
        # Rewrite queue file
        with open(self.queue_file, 'w') as f:
            for task in tasks:
                f.write(json.dumps(task) + '\n')
        
        if deleted_task:
            self._log(f"🗑️ Task deleted: {deleted_task['task']}")
            
        return deleted_task is not None
    
    def trigger_claude_execution(self, task):
        """Trigger Claude to execute the task"""
        trigger_file = self.config_dir / 'execute-now.json'
        
        trigger_data = {
            'task': task,
            'timestamp': datetime.now().isoformat(),
            'auto_execute': True,
            'trigger_source': 'claude-tasker'
        }
        
        with open(trigger_file, 'w') as f:
            json.dump(trigger_data, f, indent=2)
        
        self._log(f"🚀 Triggered Claude execution: {task['task']}")
        return True
    
    def run_autonomous_mode(self, interval=None):
        """Run in autonomous mode, executing tasks automatically with Claude SDK"""
        if interval is None:
            interval = self.config['task_check_interval']
            
        self._log("🤖 Starting Claude-Tasker autonomous mode...")
        
        if self.claude_executor is None:
            self._log("❌ Claude SDK not available - falling back to legacy mode")
            return self._run_legacy_autonomous_mode(interval)
        
        self._log("🚀 Using Claude SDK for true autonomous execution")
        self._log(f"📊 Checking for tasks every {interval} seconds")
        
        try:
            # Run the async autonomous loop
            asyncio.run(self._async_autonomous_loop(interval))
        except KeyboardInterrupt:
            self._log("\n🛑 Autonomous mode stopped by user")
        except Exception as e:
            self._log(f"❌ Error in autonomous mode: {e}")
    
    async def _async_autonomous_loop(self, interval):
        """Async loop for autonomous task execution"""
        while True:
            task = self.get_next_task()
            
            if task:
                self._log(f"\n⚡ Found task: {task['task']} (Priority: {task['priority']})")
                
                # Update status to in-progress
                self.update_task_status(task['id'], 'in_progress', 
                                      started_at=datetime.now().isoformat())
                
                # Execute with Claude SDK
                try:
                    result = await self.claude_executor.execute_task_autonomously(task)
                    
                    if result['success']:
                        # Mark as completed
                        self.update_task_status(task['id'], 'completed',
                                              completed_at=datetime.now().isoformat(),
                                              execution_result=result,
                                              actions_executed=result.get('actions_executed', 0))
                        
                        self._log(f"✅ Task completed: {task['task']}")
                        self._log(f"📊 Actions executed: {result.get('actions_executed', 0)}")
                    else:
                        # Mark as failed
                        self.update_task_status(task['id'], 'failed',
                                              error=result.get('error', 'Unknown error'),
                                              failed_at=datetime.now().isoformat())
                        self._log(f"❌ Task failed: {task['task']} - {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    self.update_task_status(task['id'], 'failed',
                                          error=f"SDK execution error: {str(e)}",
                                          failed_at=datetime.now().isoformat())
                    self._log(f"❌ SDK execution error: {e}")
            else:
                # No tasks - show a dot to indicate we're still running
                print(".", end="", flush=True)
            
            await asyncio.sleep(interval)
    
    def _run_legacy_autonomous_mode(self, interval):
        """Legacy autonomous mode without Claude SDK (fallback)"""
        self._log(f"📊 Checking for tasks every {interval} seconds (legacy mode)")
        
        try:
            while True:
                task = self.get_next_task()
                
                if task:
                    self._log(f"\n⚡ Found task: {task['task']} (Priority: {task['priority']})")
                    
                    # Update status to in-progress
                    self.update_task_status(task['id'], 'in_progress', 
                                          started_at=datetime.now().isoformat())
                    
                    # Trigger Claude execution (legacy file-based method)
                    if self.trigger_claude_execution(task):
                        # Simulate execution time based on task complexity
                        execution_time = self._estimate_execution_time(task)
                        
                        self._log(f"⏳ Estimated execution time: {execution_time} seconds")
                        time.sleep(min(execution_time, 60))  # Cap at 1 minute for demo
                        
                        # Mark as completed (in reality, this would be done by the hook)
                        self.update_task_status(task['id'], 'completed',
                                              duration=execution_time)
                        
                        self._log(f"✅ Task completed: {task['task']}")
                    else:
                        self.update_task_status(task['id'], 'failed',
                                              error='Failed to trigger execution')
                        self._log(f"❌ Task failed: {task['task']}")
                else:
                    # No tasks - show a dot to indicate we're still running
                    print(".", end="", flush=True)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self._log("\n🛑 Legacy autonomous mode stopped by user")
        except Exception as e:
            self._log(f"❌ Error in legacy autonomous mode: {e}")
    
    def get_status(self):
        """Get system status"""
        tasks = self.get_all_tasks()
        
        status = {
            'running': True,
            'queue_size': len([t for t in tasks if t['status'] == 'pending']),
            'in_progress': len([t for t in tasks if t['status'] == 'in_progress']),
            'completed_today': len([t for t in tasks if 
                                  t['status'] == 'completed' and 
                                  self._is_today(t.get('completed_at'))]),
            'failed_tasks': len([t for t in tasks if t['status'] == 'failed']),
            'total_tasks': len(tasks),
            'last_activity': datetime.now().isoformat(),
            'config': self.config
        }
        
        return status
    
    def _estimate_execution_time(self, task):
        """Estimate execution time based on task complexity"""
        base_time = 30  # Base 30 seconds
        
        # Adjust based on keywords
        complexity_keywords = {
            'update': 20, 'install': 30, 'build': 45, 'test': 25, 
            'deploy': 60, 'fix': 15, 'create': 30, 'refactor': 45
        }
        
        task_lower = task['task'].lower()
        for keyword, time_adj in complexity_keywords.items():
            if keyword in task_lower:
                base_time = time_adj
                break
        
        # Adjust based on priority (higher priority = more complex)
        priority_multiplier = {5: 1.5, 4: 1.2, 3: 1.0, 2: 0.8, 1: 0.5}
        base_time *= priority_multiplier.get(task['priority'], 1.0)
        
        return int(base_time)
    
    def _is_today(self, timestamp_str):
        """Check if timestamp is from today"""
        if not timestamp_str:
            return False
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return timestamp.date() == datetime.now().date()
        except:
            return False
    
    def _log(self, message):
        """Log message to console and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        
        print(log_entry)
        
        # Also log to file
        with open(self.execution_log, 'a') as f:
            f.write(log_entry + '\n')
    
    def _generate_token(self):
        """Generate a secure token for webhooks"""
        import secrets
        return secrets.token_urlsafe(32)

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='🎯 Claude-Tasker - Autonomous task execution for Claude Code')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add task command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('task', help='Task description')
    add_parser.add_argument('--priority', '-p', type=int, default=3, choices=range(1, 6),
                           help='Task priority (1-5, 5 is highest)')
    add_parser.add_argument('--tags', '-t', nargs='*', default=[],
                           help='Task tags (space-separated)')
    add_parser.add_argument('--description', '-d', default='',
                           help='Detailed task description')
    
    # List tasks command
    list_parser = subparsers.add_parser('list', help='List tasks')
    list_parser.add_argument('--status', choices=['pending', 'in_progress', 'completed', 'failed'],
                            help='Filter by status')
    list_parser.add_argument('--limit', type=int, help='Limit number of results')
    
    # Status command
    subparsers.add_parser('status', help='Show system status')
    
    # Run command
    subparsers.add_parser('run', help='Run next task')
    
    # Autonomous mode command
    auto_parser = subparsers.add_parser('autonomous', help='Start autonomous mode')
    auto_parser.add_argument('--interval', type=int, default=30,
                            help='Check interval in seconds')
    
    # Delete task command
    del_parser = subparsers.add_parser('delete', help='Delete a task')
    del_parser.add_argument('task_id', help='Task ID to delete')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = ClaudeTaskManager()
    
    if args.command == 'add':
        task_id = manager.add_task(args.task, args.priority, args.tags, args.description)
        print(f"Task added with ID: {task_id}")
        
    elif args.command == 'list':
        tasks = manager.get_all_tasks(args.status, args.limit)
        
        if not tasks:
            print("No tasks found.")
            return
        
        print(f"\n📋 Tasks ({len(tasks)}):")
        print("=" * 60)
        
        status_icons = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅', 'failed': '❌'}
        
        for task in tasks:
            icon = status_icons.get(task['status'], '❓')
            priority = '●' * task['priority'] + '○' * (5 - task['priority'])
            tags_str = ' '.join(f"#{tag}" for tag in task['tags']) if task['tags'] else ''
            
            print(f"{icon} [{priority}] {task['task']}")
            if tags_str:
                print(f"    🏷️  {tags_str}")
            print(f"    📅 {task['created_at'][:19]} | ID: {task['id']}")
            print()
    
    elif args.command == 'status':
        status = manager.get_status()
        print(f"\n🎯 Claude-Tasker Status")
        print("=" * 30)
        print(f"📊 Queue Size: {status['queue_size']}")
        print(f"🔄 In Progress: {status['in_progress']}")
        print(f"✅ Completed Today: {status['completed_today']}")
        print(f"❌ Failed Tasks: {status['failed_tasks']}")
        print(f"📈 Total Tasks: {status['total_tasks']}")
        print(f"⏰ Last Activity: {status['last_activity'][:19]}")
        print(f"⚙️  Check Interval: {status['config']['task_check_interval']}s")
        
    elif args.command == 'run':
        task = manager.get_next_task()
        if task:
            print(f"🚀 Executing: {task['task']}")
            manager.trigger_claude_execution(task)
        else:
            print("📭 No pending tasks")
            
    elif args.command == 'autonomous':
        manager.run_autonomous_mode(args.interval)
        
    elif args.command == 'delete':
        if manager.delete_task(args.task_id):
            print("✅ Task deleted")
        else:
            print("❌ Task not found")

if __name__ == "__main__":
    main()