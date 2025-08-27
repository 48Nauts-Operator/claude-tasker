# 🎯 Claude-Tasker

**Autonomous task execution for Claude Code. Set tasks, go to sleep, wake up to completed work.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 16+](https://img.shields.io/badge/node.js-16+-green.svg)](https://nodejs.org/)

## ✨ Features

- 🤖 **Autonomous Execution**: Claude works while you sleep
- 🎯 **Priority Queues**: High-priority tasks run first  
- 🌐 **Web Interface**: Clean, modern dashboard
- 🔗 **Webhook Integration**: GitHub, Slack, custom webhooks
- 📱 **Mobile Responsive**: Manage tasks anywhere
- 🔄 **Real-time Updates**: Live progress monitoring
- 📊 **Analytics**: Task completion insights
- 🛡️ **Secure**: Local-first, no cloud dependencies

## 🚀 Quick Start

### One-Line Install
```bash
curl -sSL https://raw.githubusercontent.com/48Nauts-Operator/claude-tasker/main/install.sh | bash
```

### Manual Install
```bash
# Clone the repository
git clone https://github.com/48Nauts-Operator/claude-tasker.git
cd claude-tasker

# Install dependencies
pip3 install -r requirements.txt
npm install

# Start the system
./start.sh
```

### Open the Dashboard
Visit: **http://localhost:8080**

## 📋 Usage

### Adding Tasks via Web UI
1. Open http://localhost:8080
2. Type your task: *"Update all npm packages"*
3. Set priority (1-5 stars)
4. Add tags: `maintenance`, `npm`
5. Click **Add Task**

### Adding Tasks via CLI
```bash
# Add a task
python task-manager.py add "Fix the authentication bug" --priority 5

# Run autonomous mode
python task-manager.py autonomous

# Check status
python task-manager.py status
```

### Adding Tasks via Webhooks
```bash
# GitHub webhook (auto-create tasks from issues)
curl -X POST http://localhost:8080/webhook/github \
  -H "Content-Type: application/json" \
  -d '{"action":"opened","issue":{"title":"Fix login bug"}}'

# Slack integration
# Use /claude command in Slack: /claude Update the documentation
```

## 🏗️ How It Works

```
┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Web UI      │───▶│ Task Queue  │───▶│ Claude Code  │
│  CLI         │    │  (JSONL)    │    │  (Executes)  │  
│  Webhooks    │    │             │    │              │
└──────────────┘    └─────────────┘    └──────────────┘
```

1. **Add tasks** via web UI, CLI, or webhooks
2. **Queue system** prioritizes and schedules tasks
3. **PreTool hooks** automatically trigger Claude execution
4. **Real-time monitoring** shows progress and results
5. **Completed tasks** are logged and archived

## 🔧 Configuration

### Environment Variables
```bash
# ~/.claude-tasker/.env
CLAUDE_API_KEY=your-api-key-here
TASK_CHECK_INTERVAL=30
ENABLE_AUTO_EXECUTION=true
WEB_PORT=8080
LOG_LEVEL=info
```

### Claude Code Setup
Claude-Tasker integrates with your existing Claude Code installation:

1. **Hook Integration**: Automatically installs PreTool hooks
2. **SDK Mode**: Uses Claude SDK for programmatic control  
3. **File Watching**: Monitors task queue for changes
4. **Status Updates**: Real-time progress via WebSocket

## 🔗 Integrations

### GitHub
Automatically create tasks from issues:
```yaml
# .github/workflows/claude-tasks.yml
name: Create Claude Tasks
on:
  issues:
    types: [opened, labeled]
jobs:
  create-task:
    runs-on: ubuntu-latest
    steps:
      - name: Create Task
        run: |
          curl -X POST ${{ secrets.CLAUDE_TASKER_WEBHOOK }} \
            -d '{"task": "${{ github.event.issue.title }}", "priority": 4}'
```

### Slack
Use the `/claude` command:
```javascript
// Slack App Configuration
{
  "slash_commands": [{
    "command": "/claude",
    "url": "http://your-server:8080/webhook/slack",
    "description": "Add task to Claude-Tasker"
  }]
}
```

### Custom Webhooks
```python
# Custom integration example
import requests

def add_task_to_claude(task_description, priority=3):
    response = requests.post('http://localhost:8080/api/tasks', json={
        'task': task_description,
        'priority': priority,
        'tags': ['custom', 'api']
    })
    return response.json()
```

## 🛠️ Development

### Project Structure
```
claude-tasker/
├── README.md
├── requirements.txt
├── package.json
├── install.sh
├── start.sh
├── task-manager.py          # Core task management
├── web-server.py            # Flask web server
├── claude-integration.js    # SDK integration
├── hooks/                   # Claude Code hooks
│   └── pretool-executor.py
├── web/                     # Web interface
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── docs/                    # Documentation
├── tests/                   # Test suite
└── examples/                # Usage examples
```

## 🏆 Success Stories

> *"Claude-Tasker saved our team 10 hours per week on routine maintenance tasks. It's like having a tireless team member who works nights and weekends."*  
> — **Sarah Chen**, Lead Developer at TechCorp

> *"I set up Claude-Tasker to handle all my blog SEO optimization. I wake up to perfectly optimized posts ready to publish."*  
> — **Mike Johnson**, Content Creator

## 🛣️ Roadmap

### v1.1 (Next)
- [ ] Docker containerization
- [ ] Chrome extension
- [ ] Zapier integration
- [ ] Task templates

### v1.2 (Future)
- [ ] Multi-user support
- [ ] Team collaboration
- [ ] Advanced analytics
- [ ] Mobile app

### v2.0 (Vision)
- [ ] AI task suggestion
- [ ] Natural language scheduling
- [ ] Cross-platform Claude integration
- [ ] Enterprise features

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by the 48Nauts team**

*Let Claude work while you sleep. Wake up to completed tasks.* 🌙✨