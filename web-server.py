#!/usr/bin/env python3
"""
Claude-Tasker Web Server
Simple Flask web interface for task management
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import task manager
try:
    from task_manager import ClaudeTaskManager
    TASK_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Task manager not available: {e}")
    TASK_MANAGER_AVAILABLE = False

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'claude-tasker-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize task manager
task_manager = None
if TASK_MANAGER_AVAILABLE:
    try:
        task_manager = ClaudeTaskManager()
        print("✅ Task manager initialized")
    except Exception as e:
        print(f"❌ Failed to initialize task manager: {e}")

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Get system status"""
    if not task_manager:
        return jsonify({'error': 'Task manager not available'}), 500
    
    try:
        status = task_manager.get_status()
        status['claude_sdk_available'] = task_manager.claude_executor is not None
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks')
def api_tasks():
    """Get all tasks"""
    if not task_manager:
        return jsonify({'error': 'Task manager not available'}), 500
    
    try:
        status = request.args.get('status')
        limit = request.args.get('limit', type=int)
        tasks = task_manager.get_all_tasks(status, limit)
        return jsonify(tasks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
def api_add_task():
    """Add a new task"""
    if not task_manager:
        return jsonify({'error': 'Task manager not available'}), 500
    
    try:
        data = request.get_json()
        if not data or 'task' not in data:
            return jsonify({'error': 'Task description required'}), 400
        
        task_id = task_manager.add_task(
            task=data['task'],
            priority=data.get('priority', 3),
            tags=data.get('tags', []),
            description=data.get('description', '')
        )
        
        # Emit socket event for real-time updates
        socketio.emit('task_added', {'task_id': task_id, 'task': data['task']})
        
        return jsonify({'task_id': task_id, 'status': 'added'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    """Delete a task"""
    if not task_manager:
        return jsonify({'error': 'Task manager not available'}), 500
    
    try:
        success = task_manager.delete_task(task_id)
        if success:
            socketio.emit('task_deleted', {'task_id': task_id})
            return jsonify({'status': 'deleted'})
        else:
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<task_id>/status', methods=['PUT'])
def api_update_task_status(task_id):
    """Update task status"""
    if not task_manager:
        return jsonify({'error': 'Task manager not available'}), 500
    
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'Status required'}), 400
        
        task = task_manager.update_task_status(task_id, data['status'])
        if task:
            socketio.emit('task_updated', {'task_id': task_id, 'status': data['status']})
            return jsonify(task)
        else:
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

# Create templates and static directories with basic files
def create_web_files():
    """Create basic web interface files"""
    templates_dir = Path(__file__).parent / 'templates'
    static_dir = Path(__file__).parent / 'static'
    
    templates_dir.mkdir(exist_ok=True)
    static_dir.mkdir(exist_ok=True)
    
    # Create index.html template
    index_html = templates_dir / 'index.html'
    if not index_html.exists():
        index_html.write_text("""<!DOCTYPE html>
<html>
<head>
    <title>Claude-Tasker Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .status-card { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-number { font-size: 2em; font-weight: bold; color: #007bff; }
        .add-task { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 500; }
        .form-group input, .form-group textarea, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .btn { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .tasks-container { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .task-item { padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .task-item:last-child { border-bottom: none; }
        .task-info h4 { margin: 0 0 5px 0; color: #333; }
        .task-info p { margin: 0; color: #666; font-size: 0.9em; }
        .task-status { padding: 4px 12px; border-radius: 12px; font-size: 0.8em; font-weight: 500; }
        .status-pending { background: #fff3cd; color: #856404; }
        .status-in_progress { background: #d1ecf1; color: #0c5460; }
        .status-completed { background: #d4edda; color: #155724; }
        .status-failed { background: #f8d7da; color: #721c24; }
        .priority { display: inline-block; margin-left: 10px; }
        .priority-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 2px; }
        .priority-1 .priority-dot { background: #28a745; }
        .priority-2 .priority-dot { background: #6f42c1; }
        .priority-3 .priority-dot { background: #17a2b8; }
        .priority-4 .priority-dot { background: #fd7e14; }
        .priority-5 .priority-dot { background: #dc3545; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .success { color: #155724; background: #d4edda; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Claude-Tasker Dashboard</h1>
            <p>Autonomous task execution for Claude Code</p>
            <div id="sdk-status"></div>
        </div>

        <div class="status-grid" id="status-grid">
            <div class="status-card">
                <div class="status-number" id="queue-size">-</div>
                <div>Pending Tasks</div>
            </div>
            <div class="status-card">
                <div class="status-number" id="in-progress">-</div>
                <div>In Progress</div>
            </div>
            <div class="status-card">
                <div class="status-number" id="completed-today">-</div>
                <div>Completed Today</div>
            </div>
            <div class="status-card">
                <div class="status-number" id="failed-tasks">-</div>
                <div>Failed Tasks</div>
            </div>
        </div>

        <div class="add-task">
            <h3>Add New Task</h3>
            <form id="add-task-form">
                <div class="form-group">
                    <label for="task">Task Description *</label>
                    <input type="text" id="task" name="task" required placeholder="e.g., Update project documentation">
                </div>
                <div class="form-group">
                    <label for="priority">Priority</label>
                    <select id="priority" name="priority">
                        <option value="1">1 - Low</option>
                        <option value="2">2 - Below Normal</option>
                        <option value="3" selected>3 - Normal</option>
                        <option value="4">4 - High</option>
                        <option value="5">5 - Critical</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="description">Description (optional)</label>
                    <textarea id="description" name="description" rows="2" placeholder="Additional details..."></textarea>
                </div>
                <button type="submit" class="btn">Add Task</button>
            </form>
        </div>

        <div class="tasks-container">
            <div style="padding: 20px; border-bottom: 1px solid #eee; background: #f8f9fa;">
                <h3 style="margin: 0;">Recent Tasks</h3>
            </div>
            <div id="tasks-list">
                <div style="padding: 40px; text-align: center; color: #666;">
                    Loading tasks...
                </div>
            </div>
        </div>
    </div>

    <script src="/socket.io/socket.io.js"></script>
    <script>
        const socket = io();
        
        // Load initial data
        loadStatus();
        loadTasks();
        
        // Refresh data every 5 seconds
        setInterval(loadStatus, 5000);
        setInterval(loadTasks, 10000);
        
        // Handle form submission
        document.getElementById('add-task-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const taskData = {
                task: formData.get('task'),
                priority: parseInt(formData.get('priority')),
                description: formData.get('description'),
                tags: []
            };
            
            try {
                const response = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(taskData)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    showMessage('Task added successfully!', 'success');
                    e.target.reset();
                    loadTasks();
                } else {
                    const error = await response.json();
                    showMessage('Error: ' + error.error, 'error');
                }
            } catch (err) {
                showMessage('Error: ' + err.message, 'error');
            }
        });
        
        // Socket event handlers
        socket.on('task_added', (data) => {
            loadTasks();
            loadStatus();
        });
        
        socket.on('task_updated', (data) => {
            loadTasks();
            loadStatus();
        });
        
        socket.on('task_deleted', (data) => {
            loadTasks();
            loadStatus();
        });
        
        async function loadStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                document.getElementById('queue-size').textContent = data.queue_size || 0;
                document.getElementById('in-progress').textContent = data.in_progress || 0;
                document.getElementById('completed-today').textContent = data.completed_today || 0;
                document.getElementById('failed-tasks').textContent = data.failed_tasks || 0;
                
                // Update SDK status
                const sdkStatus = document.getElementById('sdk-status');
                if (data.claude_sdk_available) {
                    sdkStatus.innerHTML = '<div class="success">✅ Claude SDK Connected - Autonomous execution enabled</div>';
                } else {
                    sdkStatus.innerHTML = '<div class="error">❌ Claude SDK not available - Add API key to ~/.claude-tasker/.env</div>';
                }
            } catch (err) {
                console.error('Failed to load status:', err);
            }
        }
        
        async function loadTasks() {
            try {
                const response = await fetch('/api/tasks?limit=20');
                const tasks = await response.json();
                
                const tasksList = document.getElementById('tasks-list');
                
                if (tasks.length === 0) {
                    tasksList.innerHTML = '<div style="padding: 40px; text-align: center; color: #666;">No tasks found. Add one above!</div>';
                    return;
                }
                
                tasksList.innerHTML = tasks.map(task => `
                    <div class="task-item">
                        <div class="task-info">
                            <h4>${escapeHtml(task.task)}
                                <span class="priority priority-${task.priority}">
                                    ${Array(task.priority).fill('<span class="priority-dot"></span>').join('')}
                                </span>
                            </h4>
                            <p>Created: ${new Date(task.created_at).toLocaleString()}</p>
                            ${task.description ? `<p>${escapeHtml(task.description)}</p>` : ''}
                        </div>
                        <div>
                            <span class="task-status status-${task.status}">${task.status.replace('_', ' ')}</span>
                        </div>
                    </div>
                `).join('');
            } catch (err) {
                console.error('Failed to load tasks:', err);
                document.getElementById('tasks-list').innerHTML = '<div style="padding: 40px; text-align: center; color: #dc3545;">Error loading tasks</div>';
            }
        }
        
        function showMessage(message, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = type;
            messageDiv.textContent = message;
            
            const form = document.getElementById('add-task-form');
            form.parentNode.insertBefore(messageDiv, form.nextSibling);
            
            setTimeout(() => messageDiv.remove(), 5000);
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>""")

if __name__ == '__main__':
    # Create web files if they don't exist
    create_web_files()
    
    # Get port from config or use default
    port = 8080
    if task_manager and task_manager.config:
        port = task_manager.config.get('web_port', 8080)
    
    print(f"🌐 Starting Claude-Tasker web server on port {port}")
    print(f"📊 Dashboard: http://localhost:{port}")
    
    if not task_manager:
        print("⚠️  Task manager not available - limited functionality")
    elif task_manager.claude_executor is None:
        print("⚠️  Claude SDK not configured - add API key to ~/.claude-tasker/.env")
    else:
        print("✅ Claude SDK ready for autonomous execution")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False)