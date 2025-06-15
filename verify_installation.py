"""
Verification script for countries_visited dependencies.
This script checks if all required packages are installed correctly
and reports any issues.
"""

import sys
import importlib
import importlib.metadata
import os
import re
import warnings
from packaging import version

def check_package(package_name, min_version=None, max_version=None):
    """
    Check if a package is installed and meets version requirements.

    Args:
        package_name (str): Name of the package to check
        min_version (str): Minimum required version (optional)
        max_version (str): Maximum allowed version (optional)

    Returns:
        tuple: (is_installed, version, message)
    """
    try:
        # Handle package names with hyphens
        import_name = package_name.replace('-', '_')

        # Suppress warnings when importing streamlit
        if package_name == 'streamlit' or package_name.startswith('streamlit-'):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                module = importlib.import_module(import_name)
        else:
            # Try to import the package normally
            module = importlib.import_module(import_name)

        # Get the installed version
        try:
            pkg_version = importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            # Try with hyphen instead of underscore
            try:
                hyphen_name = import_name.replace('_', '-')
                pkg_version = importlib.metadata.version(hyphen_name)
            except importlib.metadata.PackageNotFoundError:
                # Fallback to module's __version__ attribute
                pkg_version = getattr(module, "__version__", "unknown")

        # Check version constraints
        if min_version and max_version:
            if version.parse(pkg_version) < version.parse(min_version) or \
               version.parse(pkg_version) >= version.parse(max_version):
                return (True, pkg_version, f"WARNING: Version {pkg_version} is outside the required range {min_version} to {max_version}")
        elif min_version:
            if version.parse(pkg_version) < version.parse(min_version):
                return (True, pkg_version, f"WARNING: Version {pkg_version} is below the minimum required {min_version}")
        elif max_version:
            if version.parse(pkg_version) >= version.parse(max_version):
                return (True, pkg_version, f"WARNING: Version {pkg_version} is above the maximum allowed {max_version}")

        return (True, pkg_version, "OK")

    except ImportError:
        return (False, None, f"ERROR: Package not installed")
    except Exception as e:
        return (False, None, f"ERROR: {str(e)}")

def read_requirements(file_path="requirements.txt"):
    """
    Read package requirements from requirements.txt file.

    Args:
        file_path (str): Path to requirements.txt file

    Returns:
        list: List of package requirements
    """
    if not os.path.exists(file_path):
        print(f"Error: Requirements file '{file_path}' not found.")
        return []

    with open(file_path, "r") as f:
        requirements = f.read().splitlines()

    # Filter out empty lines and comments
    requirements = [req for req in requirements if req and not req.startswith('#')]

    return requirements

def parse_requirement(req_string):
    """
    Parse a requirement string into package name and version constraints.

    Args:
        req_string (str): Requirement string (e.g., 'h5py>=3.7.0,<3.9.0')

    Returns:
        tuple: (package_name, min_version, max_version)
    """
    # Handle package names with extras
    if '[' in req_string:
        req_string = req_string.split('[')[0]

    # Split package name from version constraints
    parts = req_string.split('>=')
    if len(parts) > 1:
        package_name = parts[0].strip()
        version_part = '>=' + parts[1]
    else:
        parts = req_string.split('>')
        if len(parts) > 1:
            package_name = parts[0].strip()
            version_part = '>' + parts[1]
        else:
            parts = req_string.split('==')
            if len(parts) > 1:
                package_name = parts[0].strip()
                version_part = '==' + parts[1]
            else:
                parts = req_string.split('<')
                if len(parts) > 1:
                    package_name = parts[0].strip()
                    version_part = '<' + parts[1]
                else:
                    # No version constraint
                    package_name = req_string.strip()
                    version_part = ''

    min_version = None
    max_version = None

    # Process version constraints
    if '>=' in version_part:
        min_version_part = version_part.split('>=')[1].split(',')[0].strip()
        min_version = min_version_part
    elif '>' in version_part:
        min_version_part = version_part.split('>')[1].split(',')[0].strip()
        min_version = min_version_part

    if '<=' in version_part:
        max_version_part = version_part.split('<=')[1].split(',')[0].strip()
        max_version = max_version_part
    elif '<' in version_part:
        max_version_part = version_part.split('<')[1].split(',')[0].strip()
        max_version = max_version_part
    elif '==' in version_part:
        exact_version = version_part.split('==')[1].split(',')[0].strip()
        min_version = exact_version
        # For exact version, set max_version slightly higher
        try:
            # Try to parse as a semantic version (major.minor.patch)
            version_parts = exact_version.split('.')
            if len(version_parts) >= 3:
                # Increment patch version by 1
                patch = int(version_parts[2]) + 1
                max_version = f"{version_parts[0]}.{version_parts[1]}.{patch}"
            else:
                # Fallback to adding a small value
                max_version = str(float(exact_version) + 0.0001)
        except (ValueError, IndexError):
            # If parsing fails, don't set max_version
            pass

    return (package_name, min_version, max_version)

def main():
    """Main function to verify installation."""
    print("=" * 60)
    print("Verifying installation for countries_visited")
    print("=" * 60)

    # Check Python version
    python_version = sys.version.split()[0]
    print(f"Python version: {python_version}")

    # Check if running in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"Running in virtual environment: {'Yes' if in_venv else 'No'}")

    print("\nChecking required packages:")
    print("-" * 60)
    print(f"{'Package':<20} {'Version':<15} {'Status':<25}")
    print("-" * 60)

    # Read requirements from file
    requirements = read_requirements()

    all_ok = True
    critical_packages = ['h5py', 'pandas', 'streamlit', 'folium']

    # Check each requirement
    for req in requirements:
        package_name, min_version, max_version = parse_requirement(req)
        is_installed, version, message = check_package(package_name, min_version, max_version)

        status_str = message
        if not is_installed and package_name in critical_packages:
            all_ok = False
        elif "WARNING" in message and package_name in critical_packages:
            all_ok = False

        print(f"{package_name:<20} {version if version else 'Not installed':<15} {status_str:<25}")

    print("\nAdditional checks:")

    # Test h5py functionality
    print("\nTesting h5py functionality...")
    try:
        import h5py
        import numpy as np
        import tempfile
        import os

        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.h5')
        temp_file.close()

        try:
            # Try to create and write to an HDF5 file
            with h5py.File(temp_file.name, 'w') as f:
                f.create_dataset('test', data=np.array([1, 2, 3]))

            # Try to read from the HDF5 file
            with h5py.File(temp_file.name, 'r') as f:
                data = f['test'][...]
                if list(data) == [1, 2, 3]:
                    print("  h5py test: SUCCESS - Created and read HDF5 file correctly")
                else:
                    print("  h5py test: WARNING - Data read does not match data written")
                    all_ok = False
        except Exception as e:
            error_msg = str(e)
            print(f"  h5py test: ERROR - {error_msg}")
            all_ok = False

            # Provide more specific guidance for common h5py errors
            if "Unable to load dependency HDF5" in error_msg or "Could not find module 'hdf5.dll'" in error_msg:
                print("  This error indicates that the HDF5 library is missing.")
                print("  For Windows users:")
                print("  1. Install HDF5 library from https://www.hdfgroup.org/downloads/hdf5/")
                print("  2. Add the HDF5 bin directory to your PATH environment variable")
                print("  3. Or use conda: conda install h5py")
                print("  See TROUBLESHOOTING.md for detailed instructions.")
        finally:
            # Clean up
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    except ImportError:
        print("  h5py test: ERROR - h5py not installed")
        all_ok = False
    except Exception as e:
        print(f"  h5py test: ERROR - {str(e)}")
        all_ok = False

    # Test pandas functionality
    print("\nTesting pandas functionality...")
    try:
        import pandas as pd

        # Create a simple DataFrame
        df = pd.DataFrame({'A': [1, 2, 3], 'B': ['a', 'b', 'c']})

        # Perform a simple operation
        filtered = df[df['A'] > 1]

        if len(filtered) == 2 and list(filtered['A']) == [2, 3]:
            print("  pandas test: SUCCESS - Created and filtered DataFrame correctly")
        else:
            print("  pandas test: WARNING - DataFrame operations did not produce expected results")
            all_ok = False
    except ImportError:
        print("  pandas test: ERROR - pandas not installed")
        all_ok = False
    except Exception as e:
        print(f"  pandas test: ERROR - {str(e)}")
        all_ok = False

    # Test pandas and h5py compatibility
    print("\nTesting pandas and h5py compatibility...")
    try:
        import pandas as pd
        import h5py
        import numpy as np
        import tempfile
        import os

        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.h5')
        temp_file.close()

        try:
            # Create a pandas DataFrame
            df = pd.DataFrame({
                'A': np.random.rand(5),
                'B': np.random.rand(5),
                'C': np.random.rand(5)
            })

            # Save DataFrame to HDF5 file using pandas
            df.to_hdf(temp_file.name, key='df', mode='w')

            # Read DataFrame from HDF5 file using pandas
            df_read = pd.read_hdf(temp_file.name, key='df')

            # Verify data integrity
            if df.equals(df_read):
                print("  pandas-h5py test: SUCCESS - DataFrame saved and loaded correctly with HDF5")
            else:
                print("  pandas-h5py test: WARNING - Data integrity check failed")
                all_ok = False

            # Access the HDF5 file directly using h5py
            with h5py.File(temp_file.name, 'r') as f:
                if len(list(f.keys())) > 0:
                    print("  pandas-h5py test: SUCCESS - HDF5 file structure verified")
                else:
                    print("  pandas-h5py test: WARNING - HDF5 file structure is empty")
                    all_ok = False

        except Exception as e:
            print(f"  pandas-h5py test: ERROR - {str(e)}")
            print("  This may indicate compatibility issues between pandas and h5py versions.")
            print("  Try updating to pandas>=2.1.0,<2.2.0 which is known to work with h5py>=3.10.0")
            all_ok = False

        finally:
            # Clean up
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    except ImportError as e:
        print(f"  pandas-h5py test: ERROR - {str(e)}")
        print("  Make sure both pandas and h5py are installed.")
        all_ok = False
    except Exception as e:
        print(f"  pandas-h5py test: ERROR - {str(e)}")
        all_ok = False

    # Final verdict
    print("\n" + "=" * 60)
    if all_ok:
        print("All critical dependencies are installed and working correctly!")
        print("You can now run the application with: streamlit run app.py")
    else:
        print("Some dependencies have issues. Please fix them before running the application.")
        print("You can use the install_dependencies.py script to install missing packages:")
        print("  python install_dependencies.py")

        # Provide specific guidance for Python 3.12+ users with h5py issues
        if sys.version_info.major == 3 and sys.version_info.minor >= 12:
            try:
                import h5py
            except ImportError:
                print("\nNOTE: You're using Python 3.12+, which may have compatibility issues with h5py.")
                print("For Python 3.12+ users, consider these options:")
                print("1. Downgrade to Python 3.10 which has better h5py compatibility")
                print("2. Install HDF5 library manually (see TROUBLESHOOTING.md)")
                print("3. Use conda instead of pip (see README.md)")
                print("\nSee README.md and TROUBLESHOOTING.md for detailed instructions.")
    print("=" * 60)

if __name__ == "__main__":
    main()
