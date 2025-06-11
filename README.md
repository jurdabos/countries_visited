# Countries Visited Map

An interactive web application for visualizing countries you've visited on a world map. Built with Streamlit, Folium, and HDF5.

## Features

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

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   streamlit run app.py
   ```

## Deployment Options

### Local Deployment
Running the application locally is the simplest option and recommended for development or personal use:
```
streamlit run app.py
```

This will start the Streamlit server and open the application in your default web browser.

### Streamlit Cloud Deployment
For sharing with others or accessing from anywhere, you can deploy to Streamlit Cloud:

1. Push your code to a GitHub repository
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Sign in with your GitHub account
4. Create a new app by selecting your repository
5. Configure the app:
   - Main file path: `app.py`
   - Python version: 3.9+
   - Add any required secrets (OAuth credentials) in the Streamlit Cloud dashboard

#### Important Considerations for Cloud Deployment

1. **File Storage**: The application currently uses local file storage (HDF5 files) for data persistence. In a cloud environment:
   - Files created during a session may be temporary and could be lost when the app restarts
   - Consider implementing a more persistent storage solution for production use (e.g., database integration)

2. **OAuth Configuration**: For OAuth to work in a cloud environment:
   - Create OAuth credentials with the correct redirect URI (your Streamlit Cloud app URL)
   - Add these credentials to the Streamlit Cloud secrets management
   - Update the `redirect_uri` in the `setup_oauth()` function to match your deployed app URL

## Usage

### Single-Player Mode

1. Select "Single Player" mode in the sidebar
2. Use the search box to find countries you've visited
3. Check the boxes next to countries you've visited
4. View your personalized world map and statistics

### Multi-Player Mode

1. Select "Multi Player" mode in the sidebar
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

## OAuth Integration

The application includes a placeholder for OAuth authentication. To enable it:

1. Create OAuth credentials (e.g. with Google Cloud Platform)
2. Add your credentials to Streamlit secrets:
   ```
   OAUTH_CLIENT_ID = "your-client-id"
   OAUTH_CLIENT_SECRET = "your-client-secret"
   OAUTH_REDIRECT_URI = "your-redirect-uri"
   ```

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
