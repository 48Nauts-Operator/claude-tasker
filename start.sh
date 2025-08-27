#!/bin/bash
# Start Claude-Tasker services

echo "🎯 Starting Claude-Tasker..."

# Check if Claude SDK is set up
if [ ! -f "$HOME/.claude-tasker/.env" ]; then
    echo "⚠️  Claude SDK not configured. Run ./quick-setup.sh first"
    exit 1
fi

# Start web server in background
echo "🌐 Starting web interface..."
python3 web-server.py &
WEB_PID=$!

echo "🌐 Web interface: http://localhost:8080"
echo "📊 Starting task manager in autonomous mode..."
echo "💡 Press Ctrl+C to stop both services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping Claude-Tasker..."
    kill $WEB_PID 2>/dev/null
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start autonomous task execution (this will block)
python3 task-manager.py autonomous

# This line will only be reached if autonomous mode exits
cleanup