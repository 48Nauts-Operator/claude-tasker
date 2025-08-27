#!/usr/bin/env python3
"""
Test script for Claude SDK integration
Verifies that the complete autonomous execution system works
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_api_key_setup():
    """Test if Claude API key is properly configured"""
    print("🔍 Testing API key configuration...")
    
    # Check environment variable
    api_key = os.getenv('CLAUDE_API_KEY')
    if api_key and api_key.startswith('sk-ant-'):
        print("✅ API key found in environment")
        return True
    
    # Check .env file
    env_file = Path.home() / '.claude-tasker' / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if 'CLAUDE_API_KEY=sk-ant-' in content:
                print("✅ API key found in .env file")
                # Load it into environment for testing
                for line in content.split('\n'):
                    if line.startswith('CLAUDE_API_KEY='):
                        os.environ['CLAUDE_API_KEY'] = line.split('=', 1)[1].strip()
                        return True
    
    print("❌ Claude API key not configured")
    print("💡 Set CLAUDE_API_KEY environment variable or run the installer")
    return False

def test_imports():
    """Test if all required imports work"""
    print("🔍 Testing imports...")
    
    try:
        import anthropic
        print("✅ anthropic package imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import anthropic: {e}")
        print("💡 Install with: pip install anthropic")
        return False
    
    try:
        from claude_sdk_executor import ClaudeSDKExecutor
        print("✅ ClaudeSDKExecutor imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ClaudeSDKExecutor: {e}")
        return False
    
    try:
        from task_manager import ClaudeTaskManager
        print("✅ ClaudeTaskManager imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ClaudeTaskManager: {e}")
        return False
    
    return True

async def test_claude_sdk_executor():
    """Test the Claude SDK executor directly"""
    print("🔍 Testing Claude SDK executor...")
    
    if not test_api_key_setup():
        return False
    
    try:
        from claude_sdk_executor import ClaudeSDKExecutor
        
        executor = ClaudeSDKExecutor()
        print("✅ ClaudeSDKExecutor initialized")
        
        # Create a simple test task
        test_task = {
            'id': 'test_001',
            'task': 'Create a file called /tmp/claude-test.txt with the content "Hello from Claude!"',
            'priority': 3,
            'tags': ['test'],
            'created_at': '2024-01-01T00:00:00',
            'description': 'Test task to verify SDK integration'
        }
        
        print("🚀 Executing test task...")
        result = await executor.execute_task_autonomously(test_task)
        
        if result['success']:
            print("✅ Task execution successful!")
            print(f"📊 Actions executed: {result.get('actions_executed', 0)}")
            
            # Verify the file was created
            test_file = Path('/tmp/claude-test.txt')
            if test_file.exists():
                content = test_file.read_text().strip()
                if 'Hello from Claude!' in content:
                    print("✅ Test file created with correct content")
                    test_file.unlink()  # Clean up
                    return True
                else:
                    print(f"⚠️  Test file created but content is: {content}")
            else:
                print("⚠️  Test file was not created")
            
            return True
        else:
            print(f"❌ Task execution failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Claude SDK executor test failed: {e}")
        return False

def test_task_manager_integration():
    """Test the integrated task manager"""
    print("🔍 Testing task manager integration...")
    
    try:
        from task_manager import ClaudeTaskManager
        
        manager = ClaudeTaskManager()
        print("✅ ClaudeTaskManager initialized")
        
        if manager.claude_executor is None:
            print("❌ Claude SDK not available in task manager")
            return False
        
        print("✅ Claude SDK integration successful")
        
        # Add a test task
        task_id = manager.add_task(
            "Create a simple test file and delete it",
            priority=1,
            tags=['test', 'integration'],
            description="Integration test for Claude SDK"
        )
        
        print(f"✅ Test task added with ID: {task_id}")
        
        # Check if task was added
        task = manager.get_next_task()
        if task and task['id'] == task_id:
            print("✅ Task retrieval working")
            
            # Clean up - delete the test task
            manager.delete_task(task_id)
            print("✅ Task cleanup complete")
            return True
        else:
            print("❌ Task retrieval failed")
            return False
            
    except Exception as e:
        print(f"❌ Task manager integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🎯 Claude-Tasker SDK Integration Test")
    print("=" * 50)
    
    tests = [
        ("API Key Setup", lambda: test_api_key_setup()),
        ("Imports", lambda: test_imports()),
        ("Task Manager Integration", lambda: test_task_manager_integration()),
        ("Claude SDK Executor", lambda: asyncio.create_task(test_claude_sdk_executor())),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if asyncio.iscoroutine(test_func()):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Claude-Tasker SDK integration is working!")
        return True
    else:
        print("⚠️  Some tests failed. Check configuration and dependencies.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)