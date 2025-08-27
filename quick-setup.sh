#!/bin/bash
# Quick setup script to get Claude-Tasker working with SDK integration

set -e

echo "🎯 Claude-Tasker Quick Setup"
echo "============================="

# Install anthropic package
echo "📦 Installing Claude SDK..."
python3 -m pip install --user anthropic python-dotenv

# Create .env file template
echo ""
echo "🔑 Setting up API key..."
mkdir -p "$HOME/.claude-tasker"

if [ ! -f "$HOME/.claude-tasker/.env" ]; then
    cat > "$HOME/.claude-tasker/.env" << 'EOF'
# Claude SDK Configuration
# Get your API key from: https://console.anthropic.com/
# CLAUDE_API_KEY=sk-ant-api03-your-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4000
CLAUDE_TEMPERATURE=0.7
EOF
    
    echo "✅ Created .env template at ~/.claude-tasker/.env"
    echo ""
    echo "🔐 IMPORTANT: Add your Claude API key to ~/.claude-tasker/.env"
    echo "   1. Go to: https://console.anthropic.com/"
    echo "   2. Generate an API key"
    echo "   3. Edit ~/.claude-tasker/.env and uncomment the CLAUDE_API_KEY line"
    echo "   4. Replace 'your-key-here' with your actual API key"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Make scripts executable
chmod +x task-manager.py claude-sdk-executor.py

echo "✅ Quick setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Add your Claude API key to ~/.claude-tasker/.env"
echo "2. Run: python3 task-manager.py autonomous"
echo "3. The system will now use Claude SDK for true autonomous execution"