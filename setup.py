"""Setup script for countries_visited package."""

import sys
import subprocess
import platform
from setuptools import setup, find_packages

# Read requirements
with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()

# Special handling for Windows
if sys.platform == 'win32':
    # We'll keep h5py and pandas in requirements but add a post-install step
    # to ensure they're installed correctly with binary packages

    # Define a function to install packages with binary preference
    def install_with_binary(package_spec):
        try:
            print(f"Installing {package_spec} with --only-binary flag for Windows...")
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                package_spec, '--only-binary=:all:'
            ])
            return True
        except subprocess.CalledProcessError:
            try:
                print(f"Retrying installation of {package_spec} without --only-binary flag...")
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package_spec
                ])
                return True
            except subprocess.CalledProcessError:
                print(f"Warning: Failed to install {package_spec}.")
                return False

    # Install critical packages before setup runs
    h5py_installed = install_with_binary('h5py>=3.10.0')
    pandas_installed = install_with_binary('pandas>=2.1.0,<2.2.0')

    if not h5py_installed:
        print("You may need to install HDF5 manually or use conda to install h5py.")
        print("See README.md for instructions.")

    if not pandas_installed:
        print("You may need to install Microsoft Visual C++ Build Tools or use conda.")
        print("See README.md for instructions.")

setup(
    name="countries_visited",
    version="0.0.1",
    packages=find_packages(exclude=["examples"]),
    license='MIT',
    description='Code base related to a map app with HDF5 serialization',
    author='Torda Balázs',
    install_requires=requirements,
    url='https://github.com/jurdabos/countries_visited'
)
