import os
import sys
import subprocess
import time
import webbrowser
import importlib
import platform
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        "streamlit", "folium", "streamlit-folium", "h5py", 
        "pandas", "numpy", "streamlit-oauth"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace("-", "_"))
            print(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} is NOT installed")
    
    return missing_packages

def check_file_access():
    """Check if all required files are accessible."""
    root_dir = Path(__file__).parent.parent.parent.absolute()
    
    required_files = [
        root_dir / "app.py",
        root_dir / "h5_utils.py",
        root_dir / "JSON" / "countries.geojson",
        root_dir / "JSON" / "palettes.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if file_path.exists():
            print(f"✓ {file_path} exists")
        else:
            missing_files.append(file_path)
            print(f"✗ {file_path} does NOT exist")
    
    return missing_files

def test_app_comprehensive():
    """
    Comprehensive test for the Streamlit app.
    This script will:
    1. Check if all required dependencies are installed
    2. Check if all required files are accessible
    3. Start the Streamlit app in a subprocess
    4. Wait for it to initialize
    5. Open the app in a web browser
    6. Provide instructions for manual verification
    7. Capture and display any errors from the app
    """
    print("\n=== Countries Visited Map - Comprehensive Test ===")
    
    # Check system information
    print("\n--- System Information ---")
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Python Version: {platform.python_version()}")
    print(f"Current Directory: {os.getcwd()}")
    
    # Check dependencies
    print("\n--- Checking Dependencies ---")
    missing_packages = check_dependencies()
    
    # Check file access
    print("\n--- Checking File Access ---")
    missing_files = check_file_access()
    
    # Report any issues
    if missing_packages or missing_files:
        print("\n--- Issues Detected ---")
        if missing_packages:
            print("Missing packages:")
            for package in missing_packages:
                print(f"  - {package}")
            print("\nTo install missing packages, run:")
            print("pip install -e .")
            print("or")
            print(f"pip install {' '.join(missing_packages)}")
        
        if missing_files:
            print("Missing files:")
            for file_path in missing_files:
                print(f"  - {file_path}")
            print("\nPlease ensure all required files are in the correct locations.")
        
        proceed = input("\nIssues were detected. Do you want to proceed with the test anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Test aborted.")
            return
    
    # Get the root directory of the project
    root_dir = Path(__file__).parent.parent.parent.absolute()
    app_path = root_dir / "app.py"
    
    print(f"\nStarting Streamlit app from: {app_path}")
    
    # Start the Streamlit app in a subprocess
    try:
        process = subprocess.Popen(
            ["streamlit", "run", str(app_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Wait for the app to start
        print("Waiting for Streamlit app to start...")
        time.sleep(5)  # Give it some time to initialize
        
        # Start a thread to read and display output from the process
        import threading
        
        def read_output(stream, prefix):
            for line in stream:
                print(f"{prefix}: {line.strip()}")
        
        stdout_thread = threading.Thread(
            target=read_output, 
            args=(process.stdout, "STDOUT"),
            daemon=True
        )
        stderr_thread = threading.Thread(
            target=read_output, 
            args=(process.stderr, "STDERR"),
            daemon=True
        )
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Open the app in the default web browser
        url = "http://localhost:8501"
        print(f"Opening app in web browser: {url}")
        webbrowser.open(url)
        
        # Provide instructions for manual verification
        print("\n=== Manual Verification Steps ===")
        print("Please verify the following:")
        print("1. The app loads correctly in your browser")
        print("2. The login functionality works:")
        print("   - Click 'Login with Google' or 'Login as Demo User'")
        print("   - Verify you can log in successfully")
        print("3. The map displays correctly:")
        print("   - After logging in, check if the world map is visible")
        print("   - Try selecting some countries and verify they appear on the map")
        print("4. Test both Single Player and Multi Player modes")
        print("\nPress Ctrl+C when you're done testing to stop the app.")
        
        # Wait for user to manually test and press Ctrl+C
        process.wait()
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nError during test: {str(e)}")
    finally:
        # Make sure to terminate the process
        if 'process' in locals():
            process.terminate()
            print("Streamlit app stopped.")
    
    print("\n=== Test Complete ===")
    print("If all verification steps passed, the app is running correctly.")
    print("If there were any issues, please check the error messages above and troubleshoot accordingly.")

if __name__ == "__main__":
    test_app_comprehensive()