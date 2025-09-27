#!/usr/bin/env python3
"""
Example usage of the TimeAPI Client
Demonstrates different ways to use the client script
"""

import subprocess
import json
import os

def run_client_command(command):
    """Run a client command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🚀 TimeAPI Client Examples")
    print("=" * 50)
    
    # Example 1: Basic scheduling
    print("\n📝 Example 1: Basic Task Scheduling")
    print("-" * 40)
    success, stdout, stderr = run_client_command(
        'python3 client.py "I need to have breakfast at 8am and work on my project" --output example1.json'
    )
    if success:
        print("✅ Success!")
        print(stdout)
    else:
        print("❌ Failed:", stderr)
    
    # Example 2: Show current schedule
    print("\n📅 Example 2: Show Current Schedule")
    print("-" * 40)
    success, stdout, stderr = run_client_command('python3 client.py --show')
    if success:
        print("✅ Success!")
        print(stdout)
    else:
        print("❌ Failed:", stderr)
    
    # Example 3: Schedule with explicit times
    print("\n⏰ Example 3: Schedule with Explicit Times")
    print("-" * 40)
    success, stdout, stderr = run_client_command(
        'python3 client.py "I have a meeting at 3pm and need to call mom at 5pm" --output example3.json --verbose'
    )
    if success:
        print("✅ Success!")
        print(stdout)
    else:
        print("❌ Failed:", stderr)
    
    # Example 4: Complex daily schedule
    print("\n📋 Example 4: Complex Daily Schedule")
    print("-" * 40)
    success, stdout, stderr = run_client_command(
        'python3 client.py "Schedule my day: breakfast at 8am, work from 9am to 12pm, lunch at 12:30pm, gym at 6pm, dinner at 7pm" --output daily_schedule.json'
    )
    if success:
        print("✅ Success!")
        print(stdout)
    else:
        print("❌ Failed:", stderr)
    
    # Example 5: Show JSON file contents
    print("\n📄 Example 5: JSON File Contents")
    print("-" * 40)
    json_files = [f for f in os.listdir('.') if f.startswith('example') and f.endswith('.json')]
    if json_files:
        filename = json_files[0]
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            print(f"📁 File: {filename}")
            print(f"📊 Total tasks: {len(data.get('all_tasks', []))}")
            print(f"🆕 New tasks: {len(data.get('new_tasks', []))}")
            print(f"🔍 Extracted tasks: {len(data.get('extracted_tasks', []))}")
        except Exception as e:
            print(f"❌ Error reading JSON: {e}")
    else:
        print("No example JSON files found")
    
    print("\n🎉 Examples completed!")
    print("\n💡 Try these commands yourself:")
    print("   python3 client.py --help")
    print("   python3 client.py 'Your task description here'")
    print("   python3 client.py --show")
    print("   python3 client.py --clear")

if __name__ == "__main__":
    main()

