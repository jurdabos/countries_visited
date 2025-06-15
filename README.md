# Countries Visited Map

An interactive web application for visualizing countries you've visited on a world map. Built with Streamlit, Folium, and HDF5.

## Features

- **User Authentication**: Register and login with username/password stored in Redis
- **Welcome Screen**: Dedicated welcome page with login and registration forms
- **Single-player mode**: Track countries you've visited with a simple interface
- **Multi-player mode**: Create multiple players with different colors to compare travel histories
- **Interactive map**: Visualize visited countries on a world map
- **Country selection**: Search and select countries from a comprehensive list
- **Statistics**: View statistics about your visited countries
- **Data persistence**: Save and load your maps as HDF5 files
- **Color coding**: Countries are colored based on who visited them, with mixed colors for overlaps

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/countries-visited.git
   cd countries-visited
   ```

2. Set up a virtual environment (recommended):
   ```
   # On Windows
   python -m venv .venv
   .venv\Scripts\activate

   # On macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install the required dependencies:

   **Option A**: Use the installation script (recommended):
   ```
   python install_dependencies.py
   ```
   This script will automatically handle the installation of all dependencies, with special handling for h5py and pandas on Windows.

   **Option B**: Install via setup.py:
   ```
   pip install -e .
   ```
   This will use the setup.py file which handles platform-specific installations automatically.

   **Note for Windows users**: 

   If you encounter issues with h5py or pandas installation, try one of these solutions:

   - **Option 1**: Use conda (recommended for Windows):
     ```
     conda create -n countries_env python=3.10
     conda activate countries_env
     conda install h5py pandas streamlit folium
     pip install -e .
     ```

   - **Option 2**: Install Microsoft Visual C++ Build Tools:
     1. Download and install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
     2. During installation, select "Desktop development with C++"
     3. Then run: `pip install -e .`

   - **Option 3**: Install binary packages manually in PowerShell:
     ```
     pip install "h5py>=3.10.0" --only-binary=h5py
     pip install "pandas>=2.1.0,<2.2.0" --only-binary=pandas
     ```
     Note: In PowerShell, you must use quotes around version specifications with operators.

   - **Option 4**: Install the HDF5 library separately:
     1. Download the pre-built HDF5 binaries from the [HDF Group website](https://www.hdfgroup.org/downloads/hdf5/)
     2. Add the HDF5 bin directory to your PATH environment variable
     3. Then install h5py: `pip install "h5py>=3.10.0"`

   - **Option 5 (for Python 3.12+ users)**: Use a different Python version:
     Python 3.12 is relatively new and some packages may not have binary wheels available yet.
     Consider using Python 3.9 or 3.10 which have better compatibility with h5py.
     ```
     python -m venv .venv --python=3.10
     .venv\Scripts\activate
     python install_dependencies.py
     ```

4. Verify your installation:
   ```
   python verify_installation.py
   ```
   This script will check if all required packages are installed correctly and test the functionality of critical dependencies.

5. Run the application:
   ```
   streamlit run app.py
   ```

   If you encounter any issues, please refer to the [Troubleshooting Guide](TROUBLESHOOTING.md).

   **Alternative Dependency Management**: If you're experiencing persistent dependency issues, consider using modern tools like Poetry or uv. See the [Troubleshooting Guide](TROUBLESHOOTING.md#alternative-dependency-management-tools) for instructions.

## Configuration

### Streamlit Configuration
The application includes a `.streamlit/config.toml` file with default configuration settings. You can modify these settings to customize the appearance and behavior of the application:

- **Theme**: Colors, fonts, and visual appearance
- **Server**: Port, headless mode, CORS settings
- **Logger**: Logging level for debugging
- **Client**: Caching and display settings

For more information on Streamlit configuration options, see the [Streamlit documentation](https://docs.streamlit.io/library/advanced-features/configuration).

## Deployment Options

### Local Deployment
Running the application locally is the simplest option and recommended for development or personal use:
```
streamlit run app.py
```

This will start the Streamlit server and open the application in your default web browser.

### Streamlit Cloud Deployment
For sharing with others or accessing from anywhere, we are deploying to Streamlit Cloud with:

1. Push code to a GitHub repository
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Sign in with GitHub account
4. Create a new app by selecting repository
5. Configure the app:
   - Main file path: `app.py`
   - Python version: 3.9+
   - Add any required secrets (OAuth credentials) in the Streamlit Cloud dashboard

#### Important Considerations for Cloud Deployment

1. **File Storage**: The application currently uses local file storage (HDF5 files) for data persistence. In a cloud environment:
   - Files created during a session may be temporary and could be lost when the app restarts
   - Consider implementing a more persistent storage solution for production use (e.g. database integration)

2. **Redis Configuration**: For Redis authentication to work in a cloud environment:
   - Set up a Redis instance accessible from your Streamlit Cloud app
   - Add Redis connection details to Streamlit Cloud secrets management
   - Ensure proper security measures are in place (password protection, SSL, etc.)
   - Consider using a managed Redis service (Redis Cloud, AWS ElastiCache, etc.) for production use

3. **User Data Persistence**: Be aware that:
   - User credentials are stored in Redis and will persist as long as your Redis instance is maintained
   - If you reset or change your Redis instance, users will need to register again
   - Consider implementing a backup solution for user data in production environments

## Usage

### Authentication

1. When you first open the application, you'll see the welcome screen with login and registration forms
2. **To register a new account**:
   - Fill in the registration form on the right side
   - Choose a username and password
   - Click "Register"
   - After successful registration, you can log in with your new credentials
3. **To log in**:
   - Enter your username and password in the login form on the left side
   - Click "Login"
   - Alternatively, you can use the "Login as Demo User" button for quick access

### Single-Player Mode

1. After logging in, select "Single Player" mode in the sidebar
2. Use the search box to find countries you've visited
3. Check the boxes next to countries you've visited
4. View your personalized world map and statistics

### Multi-Player Mode

1. After logging in, select "Multi Player" mode in the sidebar
2. Add players by expanding the "Add New Player" section
3. Enter a name and select a color for each player
4. Select a player to edit from the dropdown
5. Check the countries that player has visited
6. View the combined map with all players' visited countries
7. Explore the overlap statistics to see which countries were visited by multiple players

### Map Management

- Create a new map using the "New Map" button in the sidebar
- Download your current map using the "Download Map" button
- Upload a previously saved map using the "Load Map" uploader

## Data Structure

The application uses HDF5 for data storage with the following structure:

```
/                           (file root)
/palettes                   (group)
    ↳ hex_codes             (1-D UTF-8 string dataset)        # flattened list
/players                    (group)
    ↳ <player-id>/          (one subgroup per player)
           ↳ visited        (1-D UTF-8 string dataset)        # ISO-3166-1 alpha-2
           ↳ colour         (attribute)                       # "#7ebce6"
           ↳ created        (attribute)                       # ISO-8601 timestamp
```

## Redis Authentication

The application uses Redis for user authentication. To set up Redis:

### Local Development with Docker

1. Start a Redis container:
   ```
   docker run --name redis -p 6379:6379 -d redis:latest
   ```

2. Verify Redis is running:
   ```
   docker exec -it redis redis-cli ping
   ```
   You should see `PONG` as the response.

### Configuration

Redis connection parameters can be configured using environment variables:

- `REDIS_HOST`: Redis server hostname (default: "localhost")
- `REDIS_PORT`: Redis server port (default: 6379)
- `REDIS_PASSWORD`: Redis server password (default: "")
- `REDIS_SSL`: Use SSL for Redis connection (default: False)

For example:
```
# Windows PowerShell
$env:REDIS_HOST = "your-redis-host"
$env:REDIS_PORT = "6379"
$env:REDIS_PASSWORD = "your-redis-password"
$env:REDIS_SSL = "True"
streamlit run app.py

# Linux/macOS
export REDIS_HOST="your-redis-host"
export REDIS_PORT="6379"
export REDIS_PASSWORD="your-redis-password"
export REDIS_SSL="True"
streamlit run app.py
```

### Cloud Deployment

For cloud deployment, you'll need to:

1. Set up a Redis instance (e.g., Redis Cloud, AWS ElastiCache, Azure Cache for Redis)
2. Configure the application with your Redis connection details using environment variables or Streamlit secrets
3. Ensure your Redis instance is accessible from your Streamlit Cloud app

#### Using Streamlit Secrets for Redis Configuration

Add your Redis configuration to Streamlit secrets:
```
[redis]
host = "your-redis-host"
port = 6379
password = "your-redis-password"
ssl = true
```

Then update `redis_utils.py` to use these secrets instead of environment variables.

## Testing

The application includes a comprehensive test suite organized by test type:

- **Unit tests**: Test individual functions in isolation
- **Integration tests**: Test interactions between components
- **End-to-end tests**: Test the full application flow

### Running Tests

1. Install development dependencies:
   ```
   pip install -r requirements-dev.txt
   ```

2. Run all tests:
   ```
   pytest
   ```

3. Run specific test types:
   ```
   pytest tests/unit/          # Run unit tests only
   pytest tests/integration/   # Run integration tests only
   pytest tests/e2e/           # Run end-to-end tests only
   ```

4. Generate coverage report:
   ```
   pytest --cov=. --cov-report=html
   ```
   This will create an HTML coverage report in the `htmlcov` directory.

## License

[MIT License](LICENSE)

## Acknowledgments

- Country data from Natural Earth
- Built with Streamlit, Folium, and HDF5
