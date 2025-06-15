import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and return its exit code."""
    print(f"\n=== {description} ===")
    print(f"Running: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, check=True)
        print(f"✓ {description} completed successfully")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}")
        return e.returncode
    except Exception as e:
        print(f"✗ {description} failed with error: {str(e)}")
        return 1

def main():
    """Run all test scripts in sequence."""
    print("\n=== Countries Visited Map - Complete Test Suite ===")
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    
    # Define the test scripts to run
    tests = [
        {
            "command": [sys.executable, str(script_dir / "ensure_directories.py")],
            "description": "Directory Structure Check"
        },
        {
            "command": [sys.executable, str(script_dir / "test_app_comprehensive.py")],
            "description": "Comprehensive App Test"
        }
    ]
    
    # Run each test
    results = []
    for test in tests:
        exit_code = run_command(test["command"], test["description"])
        results.append({
            "description": test["description"],
            "exit_code": exit_code
        })
        
        # If the directory structure check fails, ask if we should continue
        if test["description"] == "Directory Structure Check" and exit_code != 0:
            proceed = input("\nDirectory structure check failed. Continue with app testing? (y/n): ")
            if proceed.lower() != 'y':
                print("Testing aborted.")
                return
    
    # Print summary
    print("\n=== Test Summary ===")
    all_passed = True
    for result in results:
        status = "✓ Passed" if result["exit_code"] == 0 else "✗ Failed"
        print(f"{status}: {result['description']}")
        if result["exit_code"] != 0:
            all_passed = False
    
    if all_passed:
        print("\n✓ All tests passed!")
        print("The app is running correctly with authentication and maps displaying properly.")
    else:
        print("\n✗ Some tests failed.")
        print("Please review the output above for details on the failures.")
        print("Refer to the README.md file for troubleshooting guidance.")

if __name__ == "__main__":
    main()