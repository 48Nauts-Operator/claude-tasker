#!/usr/bin/env python3
"""
Claude SDK Integration for Autonomous Task Execution
This is the CRITICAL component that makes programmatic control possible
"""

import anthropic
import json
import os
import asyncio
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = Path.home() / '.claude-tasker' / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    # dotenv not available, use system environment variables only
    pass

class ClaudeSDKExecutor:
    def __init__(self):
        """Initialize Claude SDK with API key"""
        self.api_key = os.getenv('CLAUDE_API_KEY')
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY environment variable required. Get one at https://console.anthropic.com/")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
        self.max_tokens = int(os.getenv('CLAUDE_MAX_TOKENS', '4000'))
        
        self.config_dir = Path.home() / '.claude-tasker'
        self.execution_log = self.config_dir / 'claude-execution.log'
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def execute_task_autonomously(self, task: Dict[str, Any]) -> Dict[str, Any]:
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
            
            message = self.client.messages.create(
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
    
    def _build_system_prompt(self) -> str:
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

OUTPUT FORMAT:
Always structure your response with clear action blocks:
```bash
command to execute
```

```python
python code to run
```

```file:/path/to/file
content to write to file
```

You have full autonomous control. Execute the task completely."""

    def _build_task_prompt(self, task: Dict[str, Any]) -> str:
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
    
    async def _parse_claude_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse Claude's response for actionable items"""
        actions = []
        lines = response.split('\n')
        
        current_action = None
        for line in lines:
            # Look for command blocks
            if line.strip().startswith('```bash') or line.strip().startswith('```sh'):
                current_action = {'type': 'shell', 'commands': []}
            elif line.strip().startswith('```python'):
                current_action = {'type': 'python', 'code': ''}
            elif line.strip().startswith('```file:'):
                file_path = line.strip()[8:]  # Remove ```file:
                current_action = {'type': 'file', 'path': file_path, 'content': ''}
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
                elif current_action['type'] == 'file':
                    current_action['content'] += line + '\n'
        
        return actions
    
    async def _execute_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                
                elif action['type'] == 'file':
                    result = await self._write_file(action['path'], action['content'])
                    results.append({
                        'type': 'file',
                        'path': action['path'],
                        'result': result
                    })
                    
            except Exception as e:
                results.append({
                    'type': action['type'],
                    'error': str(e)
                })
        
        return results
    
    async def _run_shell_command(self, command: str) -> Dict[str, Any]:
        """Execute a shell command safely"""
        try:
            # Security check - block dangerous commands
            dangerous_commands = ['rm -rf /', 'sudo', 'su', 'chmod 777', 'mkfs', 'dd if=']
            if any(dangerous in command for dangerous in dangerous_commands):
                return {'error': f'Blocked dangerous command: {command}'}
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'stdout': stdout.decode().strip(),
                'stderr': stderr.decode().strip(),
                'return_code': process.returncode,
                'success': process.returncode == 0
            }
            
        except Exception as e:
            return {'error': str(e), 'success': False}
    
    async def _run_python_code(self, code: str) -> Dict[str, Any]:
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
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'open': open,
                    'json': json,
                    'os': os,
                    'datetime': datetime,
                    'Path': Path,
                }
            }
            
            # Execute the code
            exec(code, safe_globals)
            
            return {'success': True, 'message': 'Code executed successfully'}
            
        except Exception as e:
            return {'error': str(e), 'success': False}
    
    async def _write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to a file safely"""
        try:
            # Security check - ensure we're not writing outside allowed directories
            path = Path(file_path).resolve()
            allowed_dirs = [
                Path.cwd(),
                Path.home() / '.claude-tasker',
                Path('/tmp')
            ]
            
            if not any(str(path).startswith(str(allowed_dir)) for allowed_dir in allowed_dirs):
                return {'error': f'File path not allowed: {file_path}', 'success': False}
            
            # Create directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            path.write_text(content.strip())
            
            return {
                'success': True,
                'message': f'File written: {file_path}',
                'size': len(content)
            }
            
        except Exception as e:
            return {'error': str(e), 'success': False}
    
    async def _log_execution(self, task: Dict[str, Any], response: str) -> None:
        """Log the execution details"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task_id': task['id'],
            'task': task['task'],
            'response_length': len(response),
            'response_preview': response[:500] + '...' if len(response) > 500 else response
        }
        
        # Ensure log directory exists
        self.execution_log.parent.mkdir(exist_ok=True)
        
        with open(self.execution_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

# Test function
async def test_claude_sdk():
    """Test the Claude SDK integration"""
    executor = ClaudeSDKExecutor()
    
    test_task = {
        'id': 'test_001',
        'task': 'Create a simple hello world Python script called hello.py',
        'priority': 3,
        'tags': ['test', 'python'],
        'created_at': datetime.now().isoformat(),
        'description': 'Test task to verify Claude SDK integration works'
    }
    
    print("🧪 Testing Claude SDK integration...")
    result = await executor.execute_task_autonomously(test_task)
    
    if result['success']:
        print("✅ Claude SDK test successful!")
        print(f"Actions executed: {result['actions_executed']}")
        print(f"Response preview: {result['response'][:200]}...")
    else:
        print("❌ Claude SDK test failed!")
        print(f"Error: {result['error']}")
    
    return result

if __name__ == "__main__":
    # Test the integration
    asyncio.run(test_claude_sdk())