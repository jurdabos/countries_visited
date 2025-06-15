# Troubleshooting Guide for Countries Visited App

This guide will help you resolve common issues when running the Countries Visited application.

## Installation Issues

### Dependency Conflicts

If you're experiencing blank screens or dependency errors when running the app, try the following:

1. **Clean installation**:
   ```
   pip uninstall -y streamlit pandas numpy h5py folium streamlit-folium streamlit-oauth
   pip install -e .
   ```

2. **Force reinstall dependencies**:
   ```
   pip install --force-reinstall -r requirements.txt
   ```

3. **Clear Streamlit cache**:
   ```
   streamlit cache clear
   ```

### H5py Installation Issues on Windows

If you're having trouble with h5py on Windows:

1. Use the `--only-binary` flag:
   ```
   pip install h5py>=3.10.0 --only-binary=h5py
   ```

2. Or install via conda:
   ```
   conda install h5py
   ```

3. For Python 3.12+ users specifically:
   Python 3.12 is relatively new and h5py may not have binary wheels available for it yet.
   You have several options:

   a. Downgrade to Python 3.10:
   ```
   # Create a new venv with Python 3.10
   python -m venv .venv --python=3.10
   .venv\Scripts\activate
   python install_dependencies.py
   ```

   b. Install HDF5 library manually:
   - Download HDF5 binaries from https://www.hdfgroup.org/downloads/hdf5/
   - Add the HDF5 bin directory to your PATH environment variable
   - Then try installing h5py again

   c. Try specific h5py versions that might have wheels:
   ```
   pip install h5py==3.10.0 --only-binary=h5py
   # or
   pip install h5py==3.9.0 --only-binary=h5py
   ```

### Alternative Dependency Management Tools

If you're experiencing persistent dependency issues, consider using one of these modern dependency management tools:

1. **Poetry**:
   Poetry provides more robust dependency resolution and environment management:
   ```
   # Install Poetry
   pip install poetry

   # Initialize Poetry in your project (if not already done)
   poetry init

   # Add dependencies
   poetry add streamlit folium streamlit-folium h5py pandas numpy streamlit-oauth

   # Install dependencies
   poetry install

   # Run the app
   poetry run streamlit run app.py
   ```

2. **uv**:
   uv is a new, fast Python package installer and resolver:
   ```
   # Install uv
   pip install uv

   # Create and activate a virtual environment
   uv venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate

   # Install dependencies
   uv pip install -r requirements.txt

   # Run the app
   streamlit run app.py
   ```

### Numpy and Pandas Version Constraints

When deploying to Streamlit Cloud, only specific versions of numpy are available:
- numpy<=2.0.2
- numpy>=2.1.0,<=2.1.3
- numpy>=2.2.0,<=2.2.6
- numpy>=2.3.0

Additionally, pandas has specific numpy version requirements. For example:
- pandas>=2.0.0,<2.1.0 works with numpy>=1.26.0,<=2.0.2
- pandas>=2.1.0,<2.2.0 works with numpy>=1.26.0,<1.27.0 and h5py>=3.10.0

If you encounter dependency conflicts:
1. Do not downgrade numpy below 1.26.0 as it will cause compatibility issues
2. Ensure pandas and numpy versions are compatible
3. Use the following command to check compatibility:
   ```
   pip install -e . --no-deps && pip install -r requirements.txt
   ```

### Pandas and H5py Compatibility

For pandas to work with HDF5 files (used by the app for data storage), you need the 'tables' package:

1. If you see an error like "Missing optional dependency 'pytables'", install it with:
   ```
   pip install tables>=3.8.0
   ```

2. Or use the install_dependencies.py script which now includes this dependency:
   ```
   python install_dependencies.py
   ```

3. For conda users:
   ```
   conda install pytables
   ```

This package enables pandas to read and write HDF5 files using the HDFStore functionality.

## Running the App

### Correct Way to Run

Always run the app using the Streamlit CLI:

```
streamlit run app.py
```

Do NOT run with:
```
python app.py  # This won't work!
```

### Restarting the App

If you see a blank screen or the app seems stuck:

1. Stop any running Streamlit processes:
   - Press Ctrl+C in the terminal where Streamlit is running
   - Or close the terminal and open a new one

2. Restart with the `--server.runOnSave=true` flag:
   ```
   streamlit run app.py --server.runOnSave=true
   ```

3. Force a full restart:
   ```
   streamlit run app.py --server.port=8502
   ```
   This uses a different port to ensure a fresh instance.

## Common Issues

### Blank Screen with Only "RUNNING..." Visible

This usually indicates that:
1. The app is still loading (wait a few moments)
2. There's a dependency conflict (see Installation Issues above)
3. There's an error in the app code that's preventing it from rendering
4. The GeoJSON file is not being found or loaded correctly

Try these steps:
1. Check your terminal for error messages
2. Restart the app using the instructions above
3. Make sure you've installed all dependencies correctly
4. Try accessing the app at http://localhost:8501 directly in your browser
5. Verify that the JSON directory exists and contains the countries.geojson file
6. For Windows users specifically:
   - Make sure you've installed h5py and pandas correctly (see README.md)
   - Try using conda instead of pip (see README.md Option 1)
   - Check if you have Microsoft Visual C++ Build Tools installed
   - Try running the app with debug logging: `streamlit run app.py --logger.level=debug`

### Authentication Issues

If you can't log in:
1. The demo login should always work (no real authentication is required)
2. Click the "Login as Demo User" button in the sidebar
3. If that doesn't work, try restarting the app

## Getting Help

If you're still experiencing issues:
1. Check the logs in the terminal where you're running the app
2. Look for any error messages or warnings
3. Try running with verbose logging:
   ```
   streamlit run app.py --logger.level=debug
   ```

## Contact

If you need further assistance, please open an issue on the GitHub repository.
