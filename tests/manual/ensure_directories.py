import os
import sys
from pathlib import Path


def ensure_directories():
    """
    Ensure that all required directories exist for the Countries Visited Map application.
    This script will:
    1. Check if the JSON directory exists
    2. Create it if it doesn't exist
    3. Check if required JSON files exist
    4. Report any missing files
    """
    # Get the root directory of the project
    root_dir = Path(__file__).parent.parent.parent.absolute()
    
    print("\n=== Countries Visited Map - Directory Structure Check ===")
    
    # Check if JSON directory exists
    json_dir = root_dir / "JSON"
    if not json_dir.exists():
        print(f"Creating JSON directory at: {json_dir}")
        json_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"✓ JSON directory exists at: {json_dir}")
    
    # Check for required JSON files
    required_files = [
        json_dir / "countries.geojson",
        json_dir / "palettes.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if file_path.exists():
            print(f"✓ {file_path.name} exists")
        else:
            missing_files.append(file_path)
            print(f"✗ {file_path.name} does NOT exist")
    
    # Report any missing files
    if missing_files:
        print("\n--- Missing Files ---")
        print("The following required files are missing:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        
        print("\nPlease ensure these files are in the correct locations:")
        print("1. countries.geojson - Contains country boundary data")
        print("2. palettes.json - Contains color palette definitions")
        
        print("\nYou can download these files from the project repository or create them manually.")
    else:
        print("\n✓ All required directories and files exist!")
    
    # Check for HDF5 file
    hdf5_file = root_dir / "countries_visited.h5"
    if hdf5_file.exists():
        print(f"✓ HDF5 data file exists at: {hdf5_file}")
    else:
        print(f"Note: HDF5 data file does not exist at: {hdf5_file}")
        print("This file will be created automatically when you run the app.")


if __name__ == "__main__":
    ensure_directories()