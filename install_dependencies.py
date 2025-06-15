"""
Installation script for countries_visited dependencies.
This script ensures that all required packages are installed correctly,
with special handling for h5py and pandas on Windows.
"""

import sys
import subprocess
import os


def install_package(package_spec, binary_first=False):
    """
    Install a package using pip, with optional binary-first approach.
    Args:
        package_spec (str): Package specification (e.g., 'h5py>=3.10.0')
        binary_first (bool): Whether to try binary installation first
    Returns:
        bool: True if installation was successful, False otherwise
    """
    print(f"Installing {package_spec}...")
    commands = []

    # Special handling for h5py and pandas on Windows with Python 3.12
    is_h5py = package_spec.startswith('h5py')
    is_pandas = package_spec.startswith('pandas')
    is_py312 = sys.version_info.major == 3 and sys.version_info.minor >= 12

    if binary_first and sys.platform == 'win32':
        # Try binary installation first on Windows
        commands.append([sys.executable, '-m', 'pip', 'install', package_spec, '--only-binary=:all:'])

        # For h5py on Python 3.12+, try specific versions known to have wheels
        if is_h5py and is_py312:
            print("Detected Python 3.12+ on Windows, trying specific h5py versions with binary wheels...")
            commands.append([sys.executable, '-m', 'pip', 'install', 'h5py==3.10.0', '--only-binary=:all:'])
            commands.append([sys.executable, '-m', 'pip', 'install', 'h5py==3.9.0', '--only-binary=:all:'])

        # For pandas on Python 3.12+, try specific versions known to work with h5py 3.10.0
        if is_pandas and is_py312:
            print("Detected Python 3.12+ on Windows, trying specific pandas versions compatible with h5py 3.10.0...")
            commands.append([sys.executable, '-m', 'pip', 'install', 'pandas==2.1.4', '--only-binary=:all:'])
            commands.append([sys.executable, '-m', 'pip', 'install', 'pandas==2.1.3', '--only-binary=:all:'])

        # Then try regular installation
        commands.append([sys.executable, '-m', 'pip', 'install', package_spec])
    else:
        # Just do regular installation
        commands.append([sys.executable, '-m', 'pip', 'install', package_spec])

    for cmd in commands:
        try:
            subprocess.check_call(cmd)
            print(f"Successfully installed {package_spec}")
            return True
        except subprocess.CalledProcessError:
            if cmd == commands[-1]:
                print(f"Failed to install {package_spec}")
                if is_h5py:
                    print("\nFor h5py installation on Windows, you have several options:")
                    print("1. Install HDF5 library separately from https://www.hdfgroup.org/downloads/hdf5/")
                    print("2. Use conda: conda install h5py")
                    print("3. Try a different Python version (3.9 or 3.10 recommended)")
                    print("See TROUBLESHOOTING.md for more details.")
                elif is_pandas:
                    print("\nFor pandas installation on Windows, you have several options:")
                    print("1. Use conda: conda install pandas")
                    print("2. Try a specific version: pip install pandas==2.1.4 --only-binary=pandas")
                    print("3. Make sure you have Microsoft Visual C++ Build Tools installed")
                    print("See TROUBLESHOOTING.md for more details.")
                return False
            # If not the last command, try the next one
            print(f"Retrying with different installation method...")
    return False


def install_from_requirements(requirements_file="requirements.txt"):
    """
    Install packages from requirements.txt file.
    Args:
        requirements_file (str): Path to requirements.txt file
    Returns:
        bool: True if all installations were successful, False otherwise
    """
    if not os.path.exists(requirements_file):
        print(f"Error: Requirements file '{requirements_file}' not found.")
        return False
    with open(requirements_file, "r") as f:
        requirements = f.read().splitlines()
    all_successful = True
    # Install h5py and pandas first with special handling on Windows
    critical_packages = [
        req for req in requirements
        if req.startswith('h5py') or req.startswith('pandas')
    ]
    # Remove critical packages from the main list
    other_packages = [
        req for req in requirements
        if not req.startswith('h5py') and not req.startswith('pandas')
    ]
    # Install critical packages with binary-first approach
    for package in critical_packages:
        if not install_package(package, binary_first=True):
            all_successful = False
            print(f"Warning: Failed to install {package}.")
            if package.startswith('h5py'):
                print("You may need to install HDF5 manually or use conda to install h5py.")
            elif package.startswith('pandas'):
                print("You may need to install Microsoft Visual C++ Build Tools or use conda.")
    # Install other packages
    for package in other_packages:
        if package and not package.startswith('#'):  # Skip empty lines and comments
            if not install_package(package):
                all_successful = False
    return all_successful


def main():
    """Main function to install dependencies."""
    print("=" * 60)
    print("Installing dependencies for countries_visited")
    print("=" * 60)
    # Check if running in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if not in_venv:
        print("Warning: You are not running in a virtual environment.")
        print("It's recommended to create and activate a virtual environment before installing dependencies.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Installation aborted.")
            return
    success = install_from_requirements()
    if success:
        print("\nAll dependencies installed successfully!")
        print("You can now run the application with: streamlit run app.py")
    else:
        print("\nSome dependencies could not be installed.")
        print("Please check the error messages above and try to resolve the issues.")
        print("You may need to install some packages manually or using conda.")


if __name__ == "__main__":
    main()
