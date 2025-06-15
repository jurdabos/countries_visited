import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def test_app_running():
    """
    Test if the Streamlit app is running correctly.
    This script will:
    1. Start the Streamlit app in a subprocess
    2. Wait for it to initialize
    3. Open the app in a web browser
    4. Provide instructions for manual verification
    """
    # Get the root directory of the project
    root_dir = Path(__file__).parent.parent.parent.absolute()
    app_path = root_dir / "app.py"
    
    print("\n=== Countries Visited Map - Manual Test ===")
    print(f"Starting Streamlit app from: {app_path}")
    
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
    print("If there were any issues, please check the error messages and troubleshoot accordingly.")

if __name__ == "__main__":
    test_app_running()