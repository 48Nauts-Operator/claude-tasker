#!/bin/bash
# 🎯 Claude-Tasker One-Line Installer
# Usage: curl -sSL https://raw.githubusercontent.com/48Nauts-Operator/claude-tasker/main/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_color() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

print_banner() {
    print_color $PURPLE "
╔══════════════════════════════════════════════════════════════════╗
║                     🎯 Claude-Tasker Installer                  ║
║              Autonomous Task Execution for Claude Code          ║
╚══════════════════════════════════════════════════════════════════╝
"
}

check_prerequisites() {
    print_color $BLUE "📋 Checking prerequisites..."
    
    # Check Python
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
        print_color $GREEN "✓ Python $PYTHON_VERSION found"
    else
        print_color $RED "✗ Python 3 not found. Please install Python 3.8+ first."
        exit 1
    fi
    
    # Check pip
    if command -v pip3 >/dev/null 2>&1; then
        print_color $GREEN "✓ pip3 found"
    else
        print_color $RED "✗ pip3 not found. Please install pip first."
        exit 1
    fi
    
    # Check git (optional)
    if command -v git >/dev/null 2>&1; then
        print_color $GREEN "✓ git found"
        HAS_GIT=true
    else
        print_color $YELLOW "⚠ git not found - will download zip instead"
        HAS_GIT=false
    fi
}

install_claude_tasker() {
    print_color $BLUE "📦 Installing Claude-Tasker..."
    
    # Create installation directory
    INSTALL_DIR="$HOME/claude-tasker"
    
    if [ -d "$INSTALL_DIR" ]; then
        print_color $YELLOW "⚠ Directory $INSTALL_DIR already exists. Backing up..."
        mv "$INSTALL_DIR" "$INSTALL_DIR.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    if [ "$HAS_GIT" = true ]; then
        # Clone the repository
        print_color $BLUE "🔄 Cloning from GitHub..."
        git clone https://github.com/48Nauts-Operator/claude-tasker.git .
    else
        # Download zip file
        print_color $BLUE "📥 Downloading from GitHub..."
        if command -v curl >/dev/null 2>&1; then
            curl -L https://github.com/48Nauts-Operator/claude-tasker/archive/main.zip -o claude-tasker.zip
        elif command -v wget >/dev/null 2>&1; then
            wget https://github.com/48Nauts-Operator/claude-tasker/archive/main.zip -O claude-tasker.zip
        else
            print_color $RED "✗ Neither curl nor wget found. Cannot download Claude-Tasker."
            exit 1
        fi
        
        # Extract zip
        if command -v unzip >/dev/null 2>&1; then
            unzip claude-tasker.zip
            mv claude-tasker-main/* .
            rm -rf claude-tasker-main claude-tasker.zip
        else
            print_color $RED "✗ unzip not found. Cannot extract Claude-Tasker."
            exit 1
        fi
    fi
    
    print_color $GREEN "✓ Claude-Tasker downloaded"
}

install_dependencies() {
    print_color $BLUE "🔧 Installing Python dependencies..."
    
    # Install Python packages
    pip3 install --user -r requirements.txt
    
    print_color $GREEN "✓ Dependencies installed"
}

setup_claude_sdk() {
    print_color $BLUE "🔑 Setting up Claude SDK..."
    
    # Install Python SDK
    print_color $BLUE "📦 Installing anthropic Python package..."
    pip3 install --user anthropic
    
    # Prompt for API key
    echo ""
    print_color $YELLOW "🔐 Claude API Key Setup Required"
    echo "1. Go to: https://console.anthropic.com/"
    echo "2. Create account and generate API key"  
    echo "3. Enter your API key below:"
    echo ""
    
    # Check if API key already exists
    if [ -f "$HOME/.claude-tasker/.env" ] && grep -q "CLAUDE_API_KEY" "$HOME/.claude-tasker/.env"; then
        print_color $GREEN "✓ Claude API key already configured"
        return
    fi
    
    read -p "Enter Claude API Key (starts with sk-ant-): " API_KEY
    
    if [[ $API_KEY == sk-ant-* ]]; then
        # Create .env file
        mkdir -p "$HOME/.claude-tasker"
        cat >> "$HOME/.claude-tasker/.env" << EOF
# Claude SDK Configuration
CLAUDE_API_KEY=$API_KEY
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4000
CLAUDE_TEMPERATURE=0.7
EOF
        
        # Set secure permissions
        chmod 600 "$HOME/.claude-tasker/.env"
        
        print_color $GREEN "✓ Claude API key configured"
        print_color $BLUE "💡 API key stored in ~/.claude-tasker/.env"
    else
        print_color $RED "❌ Invalid API key format"
        print_color $YELLOW "API keys should start with 'sk-ant-'"
        print_color $YELLOW "You can configure it later by editing ~/.claude-tasker/.env"
    fi
}

setup_configuration() {
    print_color $BLUE "⚙️ Setting up configuration..."
    
    # Create config directory
    CONFIG_DIR="$HOME/.claude-tasker"
    mkdir -p "$CONFIG_DIR"
    
    # Create default config if it doesn't exist
    if [ ! -f "$CONFIG_DIR/config.json" ]; then
        cat > "$CONFIG_DIR/config.json" << EOF
{
  "task_check_interval": 30,
  "max_retry_attempts": 3,
  "enable_auto_execution": true,
  "log_level": "info",
  "web_port": 8080
}
EOF
        print_color $GREEN "✓ Default configuration created"
    else
        print_color $YELLOW "⚠ Configuration already exists, skipping"
    fi
    
    # Make scripts executable
    chmod +x task-manager.py
    chmod +x start.sh 2>/dev/null || true
    
    print_color $GREEN "✓ Configuration complete"
}

setup_claude_integration() {
    print_color $BLUE "🔗 Setting up Claude Code integration..."
    
    # Create Claude hooks directory
    CLAUDE_DIR="$HOME/.claude"
    HOOKS_DIR="$CLAUDE_DIR/hooks"
    mkdir -p "$HOOKS_DIR"
    
    # Copy hook files
    if [ -f "hooks/pretool-executor.py" ]; then
        cp hooks/pretool-executor.py "$HOOKS_DIR/"
        chmod +x "$HOOKS_DIR/pretool-executor.py"
        print_color $GREEN "✓ PreTool hook installed"
    fi
    
    # Create or update Claude settings
    SETTINGS_FILE="$CLAUDE_DIR/settings.json"
    if [ -f "$SETTINGS_FILE" ]; then
        print_color $YELLOW "⚠ Claude settings already exist - manual hook configuration needed"
        print_color $YELLOW "  Add this to your hooks configuration:"
        print_color $YELLOW "  \"preTool\": [\"$HOOKS_DIR/pretool-executor.py\"]"
    else
        cat > "$SETTINGS_FILE" << EOF
{
  "hooks": {
    "preTool": ["$HOOKS_DIR/pretool-executor.py"]
  }
}
EOF
        print_color $GREEN "✓ Claude settings configured"
    fi
}

create_shortcuts() {
    print_color $BLUE "🔗 Creating shortcuts..."
    
    # Create a start script
    cat > start.sh << 'EOF'
#!/bin/bash
# Start Claude-Tasker services

echo "🎯 Starting Claude-Tasker..."

# Start web server in background
python3 web-server.py &
WEB_PID=$!

echo "🌐 Web interface: http://localhost:8080"
echo "📊 Starting task manager in autonomous mode..."

# Start autonomous task execution
python3 task-manager.py autonomous

# Cleanup on exit
trap "kill $WEB_PID 2>/dev/null" EXIT
EOF
    
    chmod +x start.sh
    
    # Add to PATH (optional)
    if [ -f "$HOME/.bashrc" ]; then
        if ! grep -q "claude-tasker" "$HOME/.bashrc"; then
            echo "" >> "$HOME/.bashrc"
            echo "# Claude-Tasker alias" >> "$HOME/.bashrc"
            echo "alias claude-tasker='$INSTALL_DIR/task-manager.py'" >> "$HOME/.bashrc"
            print_color $GREEN "✓ Added 'claude-tasker' command to your shell"
        fi
    fi
    
    print_color $GREEN "✓ Shortcuts created"
}

print_success() {
    print_color $GREEN "
╔══════════════════════════════════════════════════════════════════╗
║                    🎉 Installation Complete!                    ║
╚══════════════════════════════════════════════════════════════════╝
"
    
    print_color $BLUE "🚀 Getting Started:"
    echo ""
    echo "1. Start Claude-Tasker:"
    print_color $YELLOW "   cd $INSTALL_DIR && ./start.sh"
    echo ""
    echo "2. Open the web interface:"
    print_color $YELLOW "   http://localhost:8080"
    echo ""
    echo "3. Add your first task:"
    print_color $YELLOW "   python3 task-manager.py add 'Update my project documentation'"
    echo ""
    print_color $BLUE "📚 Documentation:"
    echo "   • README.md - Getting started guide"
    echo "   • docs/ - Complete documentation"
    echo "   • examples/ - Usage examples"
    echo ""
    print_color $GREEN "🎯 Claude-Tasker is ready! Let Claude work while you sleep. 🌙✨"
}

main() {
    print_banner
    check_prerequisites
    install_claude_tasker
    install_dependencies
    setup_claude_sdk
    setup_configuration
    setup_claude_integration
    create_shortcuts
    print_success
}

# Run the installer
main