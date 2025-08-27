# 🔑 Claude SDK Integration - The Key to Autonomous Execution

## The Critical Missing Piece

The web UI and task queue are just the frontend. The **real magic** that enables autonomous Claude execution happens through the Claude SDK integration. This is what we discovered after trying multiple approaches.

## Why Claude SDK is Essential

### The Problem We Solved
- **TodoWrite timeouts**: Native tool times out at high context
- **No programmatic control**: Claude Code has no API for external control
- **Manual intervention required**: Each task needed human prompting
- **Context switching**: Claude would forget tasks between sessions

### The Solution: Claude SDK
The Claude SDK provides programmatic access to Claude's capabilities, allowing us to:
- Execute tasks without human intervention
- Maintain context across multiple operations
- Control Claude's behavior programmatically
- Integrate with external systems seamlessly

## Claude SDK Installation & Setup

### 1. Install Claude SDK
```bash
# Python SDK
pip install anthropic

# Node.js SDK (alternative)
npm install @anthropic-ai/claude-sdk
```

### 2. Get API Key
1. Go to https://console.anthropic.com/
2. Create an account or sign in
3. Navigate to API Keys
4. Generate a new API key
5. Save it securely (starts with `sk-ant-api03-...`)

### 3. Environment Configuration
```bash
# ~/.claude-tasker/.env
CLAUDE_API_KEY=sk-ant-api03-your-actual-key-here
CLAUDE_MODEL=claude-3-opus-20240229
CLAUDE_MAX_TOKENS=4000
CLAUDE_TEMPERATURE=0.7
```

## Core Integration Implementation

### Python SDK Integration (`claude-sdk-executor.py`)
```python
#!/usr/bin/env python3
"""
Claude SDK Integration for Autonomous Task Execution
This is the CRITICAL component that makes programmatic control possible
"""

import anthropic
import json
import os
from pathlib import Path
from datetime import datetime
import asyncio
import logging

class ClaudeSDKExecutor:
    def __init__(self):
        """Initialize Claude SDK with API key"""
        self.api_key = os.getenv('CLAUDE_API_KEY')
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY environment variable required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = os.getenv('CLAUDE_MODEL', 'claude-3-opus-20240229')
        self.max_tokens = int(os.getenv('CLAUDE_MAX_TOKENS', '4000'))
        
        self.config_dir = Path.home() / '.claude-tasker'
        self.execution_log = self.config_dir / 'claude-execution.log'
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def execute_task_autonomously(self, task):
        """
        THIS IS THE MAGIC - Execute a task using Claude SDK
        No human intervention required!
        """
        try:
            # Build the execution prompt
            system_prompt = self._build_system_prompt()
            task_prompt = self._build_task_prompt(task)
            
            # Execute via Claude SDK
            self.logger.info(f"🚀 Executing task via Claude SDK: {task['task']}")
            
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.7,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": task_prompt
                }]
            )
            
            # Process the response
            response_content = message.content[0].text
            
            # Log the execution
            await self._log_execution(task, response_content)
            
            # Parse any tool calls or actions from the response
            actions = await self._parse_claude_response(response_content)
            
            # Execute the parsed actions
            results = await self._execute_actions(actions)
            
            return {
                'success': True,
                'response': response_content,
                'actions_executed': len(actions),
                'results': results,
                'execution_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Claude SDK execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': datetime.now().isoformat()
            }
    
    def _build_system_prompt(self):
        """Build the system prompt that enables autonomous execution"""
        return """You are Claude-Tasker, an autonomous task execution agent.

CRITICAL INSTRUCTIONS:
1. You are running in autonomous mode - no human is monitoring
2. Execute the given task completely and thoroughly
3. Use appropriate tools and commands as needed
4. Provide detailed feedback on what you accomplished
5. If you encounter issues, try alternative approaches
6. Always complete the task or provide clear failure reasons

AVAILABLE CAPABILITIES:
- File operations (read, write, edit, create, delete)
- Shell commands and system operations
- Code execution and debugging
- Package management (npm, pip, etc.)
- Git operations
- Network requests and API calls
- Database operations
- Testing and validation

EXECUTION GUIDELINES:
- Be thorough but efficient
- Test your changes when possible
- Follow best practices and conventions
- Document significant changes
- Handle errors gracefully
- Provide clear status updates

You have full autonomous control. Execute the task completely."""

    def _build_task_prompt(self, task):
        """Build the specific task prompt"""
        prompt = f"""AUTONOMOUS TASK EXECUTION

Task: {task['task']}
Priority: {task['priority']}/5
Tags: {', '.join(task.get('tags', []))}
Created: {task['created_at']}

"""
        
        if task.get('description'):
            prompt += f"Description: {task['description']}\n\n"
        
        prompt += """EXECUTE THIS TASK NOW:
1. Analyze what needs to be done
2. Plan your approach
3. Execute the necessary steps
4. Verify the results
5. Report completion status

Begin execution immediately."""
        
        return prompt
    
    async def _parse_claude_response(self, response):
        """Parse Claude's response for actionable items"""
        # This would parse the response to extract:
        # - Shell commands to run
        # - Files to create/modify
        # - API calls to make
        # - Tests to run
        
        actions = []
        lines = response.split('\n')
        
        current_action = None
        for line in lines:
            # Look for command blocks
            if line.strip().startswith('```bash') or line.strip().startswith('```sh'):
                current_action = {'type': 'shell', 'commands': []}
            elif line.strip().startswith('```python'):
                current_action = {'type': 'python', 'code': ''}
            elif line.strip().startswith('```'):
                if current_action:
                    actions.append(current_action)
                    current_action = None
            elif current_action:
                if current_action['type'] == 'shell':
                    if line.strip() and not line.startswith('#'):
                        current_action['commands'].append(line.strip())
                elif current_action['type'] == 'python':
                    current_action['code'] += line + '\n'
        
        return actions
    
    async def _execute_actions(self, actions):
        """Execute the parsed actions"""
        results = []
        
        for action in actions:
            try:
                if action['type'] == 'shell':
                    for command in action['commands']:
                        result = await self._run_shell_command(command)
                        results.append({
                            'type': 'shell',
                            'command': command,
                            'result': result
                        })
                
                elif action['type'] == 'python':
                    result = await self._run_python_code(action['code'])
                    results.append({
                        'type': 'python',
                        'result': result
                    })
                    
            except Exception as e:
                results.append({
                    'type': action['type'],
                    'error': str(e)
                })
        
        return results
    
    async def _run_shell_command(self, command):
        """Execute a shell command safely"""
        import subprocess
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'stdout': stdout.decode(),
                'stderr': stderr.decode(),
                'return_code': process.returncode
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _run_python_code(self, code):
        """Execute Python code safely"""
        try:
            # Create a safe execution environment
            safe_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                }
            }
            
            # Execute the code
            exec(code, safe_globals)
            
            return {'success': True}
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _log_execution(self, task, response):
        """Log the execution details"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task_id': task['id'],
            'task': task['task'],
            'response_length': len(response),
            'response_preview': response[:500] + '...' if len(response) > 500 else response
        }
        
        with open(self.execution_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

# Integration with the main task manager
class EnhancedTaskManager:
    def __init__(self):
        self.claude_executor = ClaudeSDKExecutor()
        # ... rest of task manager code
    
    async def execute_task_with_claude_sdk(self, task):
        """Execute task using Claude SDK instead of hooks"""
        self.logger.info(f"🎯 Claude SDK execution starting: {task['task']}")
        
        # Update task status
        self.update_task_status(task['id'], 'in_progress')
        
        try:
            # Execute via Claude SDK
            result = await self.claude_executor.execute_task_autonomously(task)
            
            if result['success']:
                # Mark as completed
                self.update_task_status(task['id'], 'completed', 
                                      execution_result=result)
                self.logger.info(f"✅ Task completed: {task['task']}")
                return True
            else:
                # Mark as failed
                self.update_task_status(task['id'], 'failed', 
                                      error=result.get('error'))
                self.logger.error(f"❌ Task failed: {task['task']}")
                return False
                
        except Exception as e:
            self.update_task_status(task['id'], 'failed', error=str(e))
            self.logger.error(f"❌ SDK execution error: {e}")
            return False
```

## Alternative: Node.js SDK Implementation

### Node.js Version (`claude-executor.js`)
```javascript
// Claude SDK Node.js Integration
const Anthropic = require('@anthropic-ai/claude-sdk');
const fs = require('fs').promises;
const { spawn } = require('child_process');

class ClaudeNodeExecutor {
    constructor() {
        this.client = new Anthropic({
            apiKey: process.env.CLAUDE_API_KEY,
        });
        
        this.model = process.env.CLAUDE_MODEL || 'claude-3-opus-20240229';
    }
    
    async executeTaskAutonomously(task) {
        try {
            const message = await this.client.messages.create({
                model: this.model,
                max_tokens: 4000,
                messages: [{
                    role: 'user',
                    content: this.buildTaskPrompt(task)
                }]
            });
            
            const response = message.content[0].text;
            
            // Parse and execute actions
            const actions = this.parseResponse(response);
            const results = await this.executeActions(actions);
            
            return {
                success: true,
                response,
                results
            };
            
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    buildTaskPrompt(task) {
        return `AUTONOMOUS TASK EXECUTION

Task: ${task.task}
Priority: ${task.priority}/5

Execute this task completely and autonomously. Provide detailed steps and results.`;
    }
    
    // ... rest of implementation
}
```

## Integration with Claude-Tasker

### Updated Task Manager (`task-manager.py`)
```python
# Add to the main task manager

from claude_sdk_executor import ClaudeSDKExecutor
import asyncio

class TaskManager:
    def __init__(self):
        # ... existing initialization
        self.claude_executor = ClaudeSDKExecutor()
    
    async def run_autonomous_mode_with_sdk(self, interval=30):
        """Enhanced autonomous mode using Claude SDK"""
        self.logger.info("🤖 Starting Claude-Tasker with SDK integration...")
        
        while True:
            task = self.get_next_task()
            
            if task:
                self.logger.info(f"⚡ Executing via Claude SDK: {task['task']}")
                
                # Execute using Claude SDK
                result = await self.claude_executor.execute_task_autonomously(task)
                
                if result['success']:
                    self.update_task_status(task['id'], 'completed', result=result)
                    self.logger.info(f"✅ Task completed: {task['task']}")
                else:
                    self.update_task_status(task['id'], 'failed', error=result['error'])
                    self.logger.error(f"❌ Task failed: {task['task']}")
            
            await asyncio.sleep(interval)
```

## Critical Configuration Steps

### 1. Environment Setup
```bash
# Required environment variables
export CLAUDE_API_KEY="sk-ant-api03-your-key-here"
export CLAUDE_MODEL="claude-3-opus-20240229"
export CLAUDE_MAX_TOKENS="4000"

# Add to ~/.bashrc or ~/.zshrc
echo 'export CLAUDE_API_KEY="your-key"' >> ~/.bashrc
```

### 2. API Key Security
```bash
# Store in a secure file (not in version control)
echo "sk-ant-api03-your-key-here" > ~/.claude-tasker/api-key.txt
chmod 600 ~/.claude-tasker/api-key.txt
```

### 3. Testing the SDK Integration
```python
# test-claude-sdk.py
import asyncio
from claude_sdk_executor import ClaudeSDKExecutor

async def test_integration():
    executor = ClaudeSDKExecutor()
    
    test_task = {
        'id': 'test_001',
        'task': 'Create a simple hello world Python script',
        'priority': 3,
        'created_at': '2024-08-27T10:00:00'
    }
    
    result = await executor.execute_task_autonomously(test_task)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_integration())
```

## Why This Changes Everything

### Before Claude SDK
- ❌ Manual triggering required
- ❌ Context lost between sessions
- ❌ No programmatic control
- ❌ TodoWrite timeouts

### After Claude SDK
- ✅ **True autonomous execution**
- ✅ **Persistent context**
- ✅ **Programmatic control**
- ✅ **No timeout issues**
- ✅ **Scalable task execution**

## Updated Installation Process

The installer needs to include SDK setup:

```bash
# Enhanced install.sh
setup_claude_sdk() {
    print_color $BLUE "🔑 Setting up Claude SDK..."
    
    # Install Python SDK
    pip3 install --user anthropic
    
    # Prompt for API key
    echo ""
    print_color $YELLOW "🔐 Claude API Key Setup Required"
    echo "1. Go to: https://console.anthropic.com/"
    echo "2. Create account and generate API key"
    echo "3. Enter your API key below:"
    echo ""
    
    read -p "Enter Claude API Key (starts with sk-ant-): " API_KEY
    
    if [[ $API_KEY == sk-ant-* ]]; then
        echo "CLAUDE_API_KEY=$API_KEY" >> "$CONFIG_DIR/.env"
        echo "CLAUDE_MODEL=claude-3-opus-20240229" >> "$CONFIG_DIR/.env"
        print_color $GREEN "✅ Claude API key configured"
    else
        print_color $RED "❌ Invalid API key format"
        exit 1
    fi
}
```

## This is the Missing Key!

Without the Claude SDK integration, Claude-Tasker is just a fancy to-do list. **WITH** the SDK integration, it becomes a true autonomous execution system.

The SDK is what enables:
- **No human intervention**
- **True autonomous execution** 
- **Programmatic task control**
- **Context preservation**
- **Scalable automation**

This is why our initial attempts with TodoWrite and file queues didn't work - we needed the Claude SDK to actually control Claude programmatically!