# Manual Testing Scripts for Countries Visited Map

This directory contains scripts for manually testing the Countries Visited Map application. These scripts help verify that the application is running correctly, with authentication and maps displaying properly.

## Available Test Scripts

### 1. Directory Structure Check (`ensure_directories.py`)

A utility script that:
- Checks if the required JSON directory exists
- Creates the directory if it doesn't exist
- Verifies if required JSON files are present
- Reports any missing files

**Usage:**
```
python tests\manual\ensure_directories.py
```

Run this script first to ensure the application has the correct directory structure.

### 2. Basic Test (`test_app_manual.py`)

A simple test script that:
- Starts the Streamlit app
- Opens it in your default web browser
- Provides instructions for manual verification

**Usage:**
```
python tests\manual\test_app_manual.py
```

### 2. Comprehensive Test (`test_app_comprehensive.py`)

A more thorough test script that:
- Checks if all required dependencies are installed
- Verifies all required files are accessible
- Displays system information
- Starts the Streamlit app
- Captures and displays any errors from the app
- Opens it in your default web browser
- Provides instructions for manual verification

**Usage:**
```
python tests\manual\test_app_comprehensive.py
```

### 3. Run All Tests (`run_all_tests.py`)

A master script that runs all tests in sequence:
- First runs the directory structure check
- Then runs the comprehensive app test
- Provides a summary of all test results

**Usage:**
```
python tests\manual\run_all_tests.py
```

This is the recommended script to run for a complete verification of the application.

## Manual Verification Steps

When running either test script, you'll need to manually verify the following:

1. **App Loading**: The app should load correctly in your browser
2. **Authentication**: 
   - Click 'Login with Google' or 'Login as Demo User'
   - Verify you can log in successfully
3. **Map Display**:
   - After logging in, check if the world map is visible
   - Try selecting some countries and verify they appear on the map
4. **App Modes**:
   - Test both Single Player and Multi Player modes

## Troubleshooting

If you encounter issues during testing:

1. **Missing Dependencies**:
   - Install missing packages with `pip install -e .` or install them individually
   - For Windows users, refer to the installation instructions in the main README.md

2. **File Access Issues**:
   - Ensure all required files are in the correct locations
   - Check that the JSON directory contains countries.geojson and palettes.json

3. **Map Display Issues**:
   - If the map doesn't display, check the browser console for errors
   - Verify that folium and streamlit-folium are installed correctly

4. **Authentication Issues**:
   - For the demo login, simply click "Login as Demo User"
   - For Google OAuth, you would need to set up proper credentials (not required for basic testing)

## Interpreting Test Results

- If all verification steps pass, the app is running correctly
- If there are issues, the comprehensive test will provide detailed error messages
- Check the STDOUT and STDERR output for any errors from the Streamlit app

## Stopping the Test

Press `Ctrl+C` in the terminal when you're done testing to stop the app and end the test.
