import streamlit as st
import folium
from folium.plugins import Fullscreen
from streamlit_folium import folium_static
import json
import os
import h5_utils
import redis_utils
import random
import pandas as pd
from streamlit_oauth import OAuth2Component
import sys

# Global variables
players = {}

# Check if the script is being run directly (not through streamlit)
if __name__ == "__main__" and "streamlit" not in sys.modules:
    print("This app must be run with `streamlit run app.py`")
    print("Please use the following command:")
    print(f"    streamlit run {os.path.abspath(__file__)}")
    sys.exit(1)

# Set page configuration
try:
    st.set_page_config(
        page_title="Countries Visited Map",
        page_icon="🌎",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    print("Page configuration set successfully")
except Exception as page_config_error:
    print(f"Error setting page configuration: {str(page_config_error)}")
    # Try with minimal configuration
    try:
        st.set_page_config(page_title="Countries Visited Map")
        print("Minimal page configuration set successfully")
    except Exception as e:
        print(f"Error setting minimal page configuration: {str(e)}")
        # Continue without page configuration

# Constants
DEFAULT_H5_FILE = "countries_visited.h5"
# Use os.path.join for cross-platform compatibility
GEOJSON_PATH = os.path.join("JSON", "countries.geojson")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'current_mode' not in st.session_state:
    st.session_state.current_mode = "single"  # Default to single-player mode


# Load country data
@st.cache_data
def load_country_data():
    try:
        # Check if file exists
        if not os.path.exists(GEOJSON_PATH):
            st.error(f"GeoJSON file not found: {GEOJSON_PATH}")
            st.info(f"Current working directory: {os.getcwd()}")
            st.info("Please check that the JSON directory exists and contains the countries.geojson file.")
            return None, []

        with open(GEOJSON_PATH, encoding="utf-8") as f:
            geo_data = json.load(f)

        # Create a list of countries with their ISO codes
        countries = []
        for feature in geo_data['features']:
            props = feature['properties']
            if 'ISO3166-1-Alpha-2' in props and props['ISO3166-1-Alpha-2'] != '-99':
                countries.append({
                    'name': props['name'],
                    'code': props['ISO3166-1-Alpha-2']
                })

        # Sort by name
        countries.sort(key=lambda x: x['name'])

        # Verify we have data
        if not countries:
            st.warning("No countries were loaded from the GeoJSON file.")
            st.info("The file may be missing country data or using an unexpected format.")
        else:
            st.success(f"Successfully loaded {len(countries)} countries.")

        return geo_data, countries
    except FileNotFoundError:
        st.error(f"GeoJSON file not found: {GEOJSON_PATH}")
        st.info(f"Current working directory: {os.getcwd()}")
        st.info("Please check that the JSON directory exists and contains the countries.geojson file.")
        return None, []
    except json.JSONDecodeError:
        st.error(f"Error parsing GeoJSON file: {GEOJSON_PATH}")
        st.info("The file may be corrupted or not in valid JSON format.")
        return None, []
    except Exception as load_error:
        st.error(f"Error loading country data: {str(load_error)}")
        st.info(f"Current working directory: {os.getcwd()}")
        st.info(f"Full path to GeoJSON: {os.path.abspath(GEOJSON_PATH)}")
        return None, []


# Load palettes
@st.cache_data
def load_palettes():
    try:
        return h5_utils.get_palettes()
    except FileNotFoundError:
        st.error("Palettes JSON file not found")
        st.info("Please check that the JSON/palettes.json file exists.")
        return {}
    except json.JSONDecodeError:
        st.error("Error parsing palettes JSON file")
        st.info("The file may be corrupted or not in valid JSON format.")
        return {}
    except Exception as palette_error:
        st.error(f"Error loading palettes: {str(palette_error)}")
        return {}


# Build map function
def build_map(player_data, geo_data):
    """
    Build a folium map with visited countries colored according to player colors.

    Args:
        player_data (dict): Dictionary of players with their visited countries and colors
        geo_data (dict): GeoJSON data for countries

    Returns:
        folium.Map: The created map
    """
    try:
        # Check if geo_data is None or empty
        if geo_data is None:
            st.error("Cannot build map: GeoJSON data is missing")
            # Return a simple default map
            return folium.Map(location=[20, 0], zoom_start=2)

        def style_fn(feature):
            try:
                iso = feature["properties"].get("ISO3166-1-Alpha-2", "")
                if iso == '-99':  # Skip non-country territories
                    return {"fillColor": "#ffffff", "fillOpacity": 0.1, "color": "#999", "weight": 0.5}

                owners = [player_id for player_id, player_info in player_data.items() if iso in player_info["visited"]]

                if not owners:  # Nobody visited
                    return {"fillColor": "#ffffff", "color": "#999", "weight": 0.5}

                if len(owners) == 1:  # Single owner → their colour
                    return {"fillColor": player_data[owners[0]]["colour"],
                            "fillOpacity": 0.7,
                            "color": "#444", "weight": 0.5}

                # Multiple owners → improved color mixing
                # Convert hex colors to RGB
                hex_colors = [player_data[o]["colour"] for o in owners]
                rgb_colors = []

                for hex_color in hex_colors:
                    # Ensure hex color has # prefix and is 7 characters long (#RRGGBB)
                    if not hex_color.startswith('#'):
                        hex_color = f"#{hex_color}"
                    if len(hex_color) != 7:
                        # Default to a gray color if invalid
                        hex_color = "#777777"

                    # Convert hex to RGB
                    r = int(hex_color[1:3], 16)
                    g = int(hex_color[3:5], 16)
                    b = int(hex_color[5:7], 16)
                    rgb_colors.append((r, g, b))

                # Calculate the mixed color using a more visually accurate method
                # This uses a square root method which better represents color mixing
                r_sum = sum(color[0] ** 2 for color in rgb_colors)
                g_sum = sum(color[1] ** 2 for color in rgb_colors)
                b_sum = sum(color[2] ** 2 for color in rgb_colors)

                r_mixed = int((r_sum / len(rgb_colors)) ** 0.5)
                g_mixed = int((g_sum / len(rgb_colors)) ** 0.5)
                b_mixed = int((b_sum / len(rgb_colors)) ** 0.5)

                # Ensure values are within valid RGB range (0-255)
                r_mixed = max(0, min(255, r_mixed))
                g_mixed = max(0, min(255, g_mixed))
                b_mixed = max(0, min(255, b_mixed))

                mixed_color = "#{:02x}{:02x}{:02x}".format(r_mixed, g_mixed, b_mixed)

                return {"fillColor": mixed_color,
                        "fillOpacity": 0.7,
                        "color": "#222", "weight": 0.5}
            except Exception as style_error:
                # If there's an error in styling, use a default style
                st.warning(f"Error styling map feature: {str(style_error)}")
                return {"fillColor": "#ffffff", "color": "#999", "weight": 0.5}

        # Create map
        m = folium.Map(location=[20, 0], zoom_start=2, control_scale=True)

        # Add fullscreen button
        Fullscreen().add_to(m)

        # Add GeoJSON layer
        tooltip = folium.GeoJsonTooltip(fields=['name', 'ISO3166-1-Alpha-2'], aliases=['Country:', 'Code:'])
        folium.GeoJson(
            geo_data,
            style_function=style_fn,
            tooltip=tooltip
        ).add_to(m)

        # Add legend
        if player_data:
            legend_html = """
            <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; 
                        padding: 10px; border-radius: 5px; border: 1px solid grey; max-width: 300px;">
            <h4 style="margin-top: 0;">Players</h4>
            """

            for i, (p, info) in enumerate(player_data.items(), 1):
                legend_html += f"""
                <div style="margin-bottom: 5px;">
                    <span style="background:{info["colour"]}; width:15px; height:15px; 
                          display:inline-block; margin-right:5px;"></span>{p} 
                    <span style="color: gray; font-size: 0.8em;">({len(info["visited"])} countries)</span>
                </div>
                """

            legend_html += "</div>"
            m.get_root().add_child(folium.Element(legend_html))

        return m
    except Exception as map_error:
        st.error(f"Error building map: {str(map_error)}")
        # Return a simple default map
        return folium.Map(location=[20, 0], zoom_start=2)


# OAuth configuration
def setup_oauth():
    # Replace with your actual OAuth credentials
    client_id = st.secrets.get("OAUTH_CLIENT_ID", "your-client-id")
    client_secret = st.secrets.get("OAUTH_CLIENT_SECRET", "your-client-secret")
    redirect_uri = st.secrets.get("OAUTH_REDIRECT_URI", "http://localhost:8501")

    # Initialize OAuth component
    oauth2 = OAuth2Component(
        client_id,
        client_secret,
        "https://accounts.google.com/o/oauth2/auth",
        "https://oauth2.googleapis.com/token",
        "https://oauth2.googleapis.com/revoke",
        redirect_uri
    )

    return oauth2


def welcome_screen():
    """
    Display the welcome screen with login and registration forms.

    Note:
        When login is successful, this function calls st.rerun() which stops execution
        and restarts the Streamlit app. This means the function doesn't actually return
        a value for successful logins.

    Returns:
        bool: False if the user did not successfully log in
              (For successful logins, st.rerun() is called and the function doesn't return)
    """
    # Handle button clicks and state changes BEFORE rendering UI

    # Check if login button was clicked
    if 'login_button' in st.session_state and st.session_state.login_button:
        # Reset button state
        st.session_state.login_button = False

        if not st.session_state.login_username or not st.session_state.login_password:
            st.session_state.login_error = "Please enter both username and password"
        else:
            # Authenticate user
            if redis_utils.authenticate_user(st.session_state.login_username, st.session_state.login_password):
                st.session_state.login_success = f"Welcome back, {st.session_state.login_username}!"
                # Set session state
                st.session_state.logged_in = True
                st.session_state.user_id = st.session_state.login_username
                st.rerun()
            else:
                st.session_state.login_error = "Invalid username or password"

    # Check if demo login button was clicked
    if 'demo_login_button' in st.session_state and st.session_state.demo_login_button:
        # Reset button state
        st.session_state.demo_login_button = False

        st.session_state.logged_in = True
        st.session_state.user_id = "demo_user"
        st.rerun()

    # Check if register button was clicked
    if 'register_button' in st.session_state and st.session_state.register_button:
        # Reset button state
        st.session_state.register_button = False

        if (not st.session_state.reg_username or
                not st.session_state.reg_password or
                not st.session_state.reg_confirm_password):
            st.session_state.register_error = "Please fill in all fields"
        elif st.session_state.reg_password != st.session_state.reg_confirm_password:
            st.session_state.register_error = "Passwords do not match"
        elif redis_utils.user_exists(st.session_state.reg_username):
            st.session_state.register_error = "Username already exists. Please choose another one."
        else:
            # Register new user
            if redis_utils.add_user(st.session_state.reg_username, st.session_state.reg_password):
                st.session_state.register_success = "Registration successful! You can now log in."
                st.session_state.registration_successful = True
                # Clear form fields after successful registration
                st.session_state.reg_username = ""
                st.session_state.reg_password = ""
                st.session_state.reg_confirm_password = ""
                st.rerun()
            else:
                st.session_state.register_error = "Registration failed. Please try again later."

    # Check if we just completed a successful registration
    if 'registration_successful' in st.session_state and st.session_state.registration_successful:
        # Clear the flag
        st.session_state.registration_successful = False

    # Now render the UI
    st.title("Welcome to Countries Visited Map")

    # Welcome message with app description
    st.markdown("""
    This application allows you to track and visualize the countries you've visited on an interactive world map.
    """)

    # Create columns for login and registration
    col1, col2 = st.columns(2)

    # Login form
    with col1:
        st.subheader("Login")
        st.text_input("Username", key="login_username")
        st.text_input("Password", type="password", key="login_password")

        # Button with no callback - handled at the beginning of function
        st.button("Login", type="primary", use_container_width=True, key="login_button")

        # Display error or success message if they exist
        if 'login_error' in st.session_state and st.session_state.login_error:
            st.error(st.session_state.login_error)
            st.session_state.login_error = None
        if 'login_success' in st.session_state and st.session_state.login_success:
            st.success(st.session_state.login_success)
            st.session_state.login_success = None

        # Demo login option
        st.divider()
        st.write("Or use demo login:")

        # Button with no callback - handled at the beginning of function
        st.button("Login as Demo User", use_container_width=True, key="demo_login_button")

    # Registration form
    with col2:
        st.subheader("Register")
        st.text_input("Choose a Username", key="reg_username")
        st.text_input("Choose a Password", type="password", key="reg_password")
        st.text_input("Confirm Password", type="password", key="reg_confirm_password")

        # Button with no callback - handled at the beginning of function
        st.button("Register", type="primary", use_container_width=True, key="register_button")

        # Display error or success message if they exist
        if 'register_error' in st.session_state and st.session_state.register_error:
            st.error(st.session_state.register_error)
            st.session_state.register_error = None
        if 'register_success' in st.session_state and st.session_state.register_success:
            st.success(st.session_state.register_success)
            st.session_state.register_success = None

    # Return False to indicate login was not successful
    # Note: For successful logins, st.rerun() is called which restarts the app,
    # so this return statement is only reached if login was not successful
    return False


def login_screen():
    """
    Display the login screen and handle authentication.

    Returns:
        bool: True if login is successful, False otherwise
    """
    # Initialize session state variables for login if they don't exist
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'password' not in st.session_state:
        st.session_state.password = ""
    if 'login_error' not in st.session_state:
        st.session_state.login_error = None
    if 'register_error' not in st.session_state:
        st.session_state.register_error = None
    if 'register_success' not in st.session_state:
        st.session_state.register_success = None

    # Handle form submissions first - before rendering the UI
    login_submitted = False
    register_submitted = False

    # Create columns for the login and register buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("Login"):
            login_submitted = True

    with col2:
        if st.button("Register"):
            register_submitted = True

    with col3:
        if st.button("Login as Demo User"):
            st.session_state.username = "demo"
            st.session_state.password = "demo"
            login_submitted = True

    # Now render the UI
    st.title("Countries Visited")
    st.subheader("Login")

    # Display username and password fields
    username = st.text_input("Username", value=st.session_state.username, key="username_input")
    password = st.text_input("Password", type="password", value=st.session_state.password, key="password_input")

    # Update session state with current values
    st.session_state.username = username
    st.session_state.password = password

    # Process login if submitted
    if login_submitted:
        if not username or not password:
            st.session_state.login_error = "Please enter both username and password."
        else:
            # Demo user check (no actual authentication)
            if username == "demo" and password == "demo":
                st.session_state.authenticated = True
                st.session_state.user = "demo"
                st.rerun()  # Refresh the app to show the authenticated view
            else:
                # Check Redis for user authentication
                try:
                    success = redis_utils.authenticate_user(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user = username
                        st.rerun()  # Refresh the app to show the authenticated view
                    else:
                        st.session_state.login_error = "Invalid username or password."
                except Exception as auth_error:
                    print(f"Authentication error: {str(auth_error)}")
                    st.session_state.login_error = "Authentication service unavailable. Please try the demo login."

    # Process registration if submitted
    if register_submitted:
        if not username or not password:
            st.session_state.register_error = "Please enter both username and password."
        else:
            try:
                success, message = redis_utils.register_user(username, password)
                if success:
                    st.session_state.register_success = f"User {username} registered successfully. You can now log in."
                    st.session_state.username = username
                    st.session_state.password = ""
                else:
                    st.session_state.register_error = message
            except Exception as reg_error:
                print(f"Registration error: {str(reg_error)}")
                st.session_state.register_error = "Registration service unavailable. Please try the demo login."

    # Display error messages if present
    if 'login_error' in st.session_state and st.session_state.login_error:
        st.error(st.session_state.login_error)
        st.session_state.login_error = None
    if 'register_error' in st.session_state and st.session_state.register_error:
        st.error(st.session_state.register_error)
        st.session_state.register_error = None
    if 'register_success' in st.session_state and st.session_state.register_success:
        st.success(st.session_state.register_success)
        st.session_state.register_success = None

    # Return False to indicate login was not successful
    # Note: For successful logins, st.rerun() is called which restarts the app,
    # so this return statement is only reached if login was not successful
    return False


# Main app function
def main():
    try:
        # Initialize session state for country selection if not already done
        if 'selected_countries' not in st.session_state:
            st.session_state.selected_countries = set()
        if 'country_search' not in st.session_state:
            st.session_state.country_search = ""

        # Check if HDF5 file exists and create it if it doesn't
        if not os.path.exists(DEFAULT_H5_FILE):
            try:
                success = h5_utils.init_h5(DEFAULT_H5_FILE)
                if not success:
                    # Try to create a simple placeholder file to avoid errors
                    with open(DEFAULT_H5_FILE, 'wb') as file_handle:
                        file_handle.write(b'placeholder')
            except Exception as exc:
                print(f"Error creating HDF5 file: {str(exc)}")
                # Try to create a simple placeholder file to avoid errors
                try:
                    with open(DEFAULT_H5_FILE, 'wb') as file_handle:
                        file_handle.write(b'placeholder')
                except (IOError, PermissionError) as file_error:
                    print(f"Error creating placeholder file: {str(file_error)}")
        else:
            # Verify that the file is a valid HDF5 file
            try:
                import h5py
                with h5py.File(DEFAULT_H5_FILE, 'r'):
                    pass
            except Exception as exc:
                print(f"Error opening existing HDF5 file: {str(exc)}")
                # Rename the corrupted file and create a new one
                try:
                    import shutil
                    backup_file = f"{DEFAULT_H5_FILE}.bak"
                    shutil.move(DEFAULT_H5_FILE, backup_file)
                    h5_utils.init_h5(DEFAULT_H5_FILE)
                except (IOError, OSError, PermissionError) as backup_error:
                    print(f"Error backing up corrupted file and creating new one: {str(backup_error)}")

        # Check if JSON directory and files exist
        if not os.path.exists("JSON"):
            # Display a basic UI with error message
            st.title("Countries Visited Map")
            st.error("JSON directory not found. Please make sure the JSON directory exists in the project root.")
            st.info("This application requires the JSON directory with countries.geojson and palettes.json files.")
            return

        if not os.path.exists(GEOJSON_PATH):
            # Display a basic UI with error message
            st.title("Countries Visited Map")
            st.error(f"countries.geojson not found at {GEOJSON_PATH}. Please make sure the file exists.")
            st.info("This application requires the countries.geojson file in the JSON directory.")
            return

        if not os.path.exists(os.path.join("JSON", "palettes.json")):
            # Display a basic UI with error message
            st.title("Countries Visited Map")
            st.error(f"palettes.json not found at {os.path.join('JSON', 'palettes.json')}. Please make sure the file "
                     f"exists.")
            st.info("This application requires the palettes.json file in the JSON directory.")
            return

        # Load data
        geo_data, countries = load_country_data()

        # Check if country data was loaded successfully
        if not geo_data or not countries:
            # Display a basic UI with error message
            st.title("Countries Visited Map")
            st.error("Failed to load country data. Please check the terminal for more details.")
            st.info("This application requires valid country data from the countries.geojson file.")
            return

        palettes = load_palettes()

        # Check if palettes were loaded successfully
        if not palettes:
            # Display a basic UI with error message
            st.title("Countries Visited Map")
            st.error("Failed to load color palettes. Please check the terminal for more details.")
            st.info("This application requires valid color palettes from the palettes.json file.")
            # Continue without palettes - we can use default colors
            palettes = {"default": ["#7ebce6", "#f7941d", "#a2ad00", "#522398"]}

        # Sidebar
        with st.sidebar:
            st.title("Countries Visited Map")

            # User info and logout
            if st.session_state.logged_in:
                st.success(f"Logged in as {st.session_state.user_id}")

                # Callback function for logout button
                def logout_callback():
                    st.session_state.logged_in = False
                    st.session_state.user_id = None
                    st.session_state.need_rerun = True

                st.button("Logout", on_click=logout_callback, key="logout_button")

                # Check if we need to rerun after callback
                if 'need_rerun' in st.session_state and st.session_state.need_rerun:
                    st.session_state.need_rerun = False
                    st.rerun()

                st.divider()

                # Mode selection (only shown when logged in)
                st.subheader("Mode")
                mode = st.radio("Select Mode", ["Single Player", "Multi Player"],
                                index=0 if st.session_state.current_mode == "single" else 1,
                                key="mode_selection")
                st.session_state.current_mode = "single" if mode == "Single Player" else "multi"

                # File management
                st.divider()
                st.subheader("Map File")

                # Create new map or load existing
                col1, col2 = st.columns(2)
                with col1:
                    # Callback function for new map button
                    def new_map_callback():
                        try:
                            if os.path.exists(DEFAULT_H5_FILE):
                                os.remove(DEFAULT_H5_FILE)
                            init_success = h5_utils.init_h5(DEFAULT_H5_FILE)
                            if init_success:
                                st.session_state.new_map_success = "Created new map!"
                                st.session_state.need_rerun = True
                            else:
                                st.session_state.new_map_error = ("Failed to create new map. Check the terminal for "
                                                                  "details.")
                                st.session_state.new_map_info = [
                                    f"Current working directory: {os.getcwd()}",
                                    f"Attempted to create file at: {os.path.abspath(DEFAULT_H5_FILE)}"
                                ]
                        except Exception as map_error:
                            st.session_state.new_map_error = f"Error creating new map: {str(map_error)}"
                            st.session_state.new_map_info = [
                                f"Current working directory: {os.getcwd()}",
                                f"Attempted to create file at: {os.path.abspath(DEFAULT_H5_FILE)}"
                            ]

                    st.button("New Map", on_click=new_map_callback, key="new_map_button")

                    # Check if we need to rerun after callback
                    if 'need_rerun' in st.session_state and st.session_state.need_rerun:
                        st.session_state.need_rerun = False
                        st.rerun()

                    # Display error, success, or info messages if they exist
                    if 'new_map_success' in st.session_state and st.session_state.new_map_success:
                        st.success(st.session_state.new_map_success)
                        st.session_state.new_map_success = None
                    if 'new_map_error' in st.session_state and st.session_state.new_map_error:
                        st.error(st.session_state.new_map_error)
                        st.session_state.new_map_error = None
                    if 'new_map_info' in st.session_state and st.session_state.new_map_info:
                        for info in st.session_state.new_map_info:
                            st.info(info)
                        st.session_state.new_map_info = None

                with col2:
                    uploaded_file = st.file_uploader("Load Map", type=["h5"], key="map_file_uploader")
                    if uploaded_file:
                        try:
                            with open(DEFAULT_H5_FILE, "wb") as f:
                                f.write(uploaded_file.getvalue())
                            st.success("Map loaded!")
                            st.session_state.need_rerun = True
                        except Exception as exc:
                            st.error(f"Error loading map: {str(exc)}")

                    # Check if we need to rerun after callback
                    if 'need_rerun' in st.session_state and st.session_state.need_rerun:
                        st.session_state.need_rerun = False
                        st.rerun()

                # Download current map
                if os.path.exists(DEFAULT_H5_FILE):
                    try:
                        with open(DEFAULT_H5_FILE, "rb") as f:
                            st.download_button(
                                label="Download Map",
                                data=f,
                                file_name="countries_visited.h5",
                                mime="application/x-hdf5",
                                key="download_map_button"
                            )
                    except Exception as exc:
                        st.error(f"Error preparing map for download: {str(exc)}")

        # Main content
        try:
            # Force Streamlit to render something
            placeholder = st.empty()
            placeholder.text("Loading application content...")

            if st.session_state.logged_in:
                try:
                    if st.session_state.current_mode == "single":
                        # Clear the placeholder
                        placeholder.empty()
                        single_player_mode(geo_data, countries)
                    else:
                        # Clear the placeholder
                        placeholder.empty()
                        multi_player_mode(geo_data, countries, palettes)
                except Exception as exc:
                    import traceback
                    traceback.print_exc()
                    st.error(f"Error displaying {st.session_state.current_mode} mode: {str(exc)}")
                    st.info("Please check the error message above and try again. If the problem persists, "
                            "try creating a new map or reloading the page.")
                    # Display a basic UI even if there's an error
                    st.title(f"{st.session_state.current_mode.title()} Player Mode")
                    st.warning("There was an error loading the map. Please see the error message above.")
            else:
                # Clear the placeholder
                placeholder.empty()
                # Show welcome screen with login/registration forms
                welcome_screen()
        except Exception as exc:
            import traceback
            traceback.print_exc()
            st.error(f"Error rendering application content: {str(exc)}")
            st.info("Please check the terminal for more details and try refreshing the page.")
            # Display minimal UI
            st.title("Countries Visited Map")
            st.warning("There was an error loading the application. Please see the error message above.")
            # Provide troubleshooting information
            st.subheader("Troubleshooting Steps")
            st.markdown("""
            1. Check the terminal for error messages
            2. Make sure all dependencies are installed correctly:
               ```
               pip install --force-reinstall -r requirements.txt
               ```
            3. Clear the Streamlit cache:
               ```
               streamlit cache clear
               ```
            4. Try running with debug logging:
               ```
               streamlit run app.py --logger.level=debug
               ```
            See TROUBLESHOOTING.md for more information.
            """)
    except Exception as exc:
        st.error(f"An unexpected error occurred: {str(exc)}")
        st.info("Please try refreshing the page. If the problem persists, check the application logs for more details.")
        # Always show at least the basic UI
        st.title("Countries Visited Map")
        st.warning("There was an error loading the application. Please see the error message above.")


def single_player_mode(geo_data, countries):
    st.title("Single Player Mode")
    # Initialize if needed
    if not os.path.exists(DEFAULT_H5_FILE):
        h5_utils.init_h5(DEFAULT_H5_FILE)
        h5_utils.add_player("default", "#444444", DEFAULT_H5_FILE)
    # Get player data
    players = h5_utils.get_players(DEFAULT_H5_FILE)
    if "default" not in players:
        h5_utils.add_player("default", "#444444", DEFAULT_H5_FILE)
        players = h5_utils.get_players(DEFAULT_H5_FILE)
    visited = players.get("default", {}).get("visited", set())

    # Initialize session state for country selection
    if 'single_player_selected_countries' not in st.session_state:
        st.session_state.single_player_selected_countries = visited.copy()

    # Initialize session state for showing map
    if 'single_player_show_map' not in st.session_state:
        st.session_state.single_player_show_map = False

    # Country selection
    with st.container():
        st.subheader("Select Countries You've Visited")

        # Search box for countries
        search_term = st.text_input("Search for a country", key="single_player_search")

        # Filter countries based on search
        filtered_countries = countries
        if search_term:
            filtered_countries = [c for c in countries if search_term.lower() in c['name'].lower()]

        # Create a DataFrame for easier display
        df = pd.DataFrame(filtered_countries)

        # Set 'Visited' based on session state selected countries
        df['Visited'] = df['code'].apply(lambda x: x in st.session_state.single_player_selected_countries)

        # Display as a table with checkboxes
        edited_df = st.data_editor(
            df,
            column_config={
                "name": "Country",
                "code": "Code",
                "Visited": st.column_config.CheckboxColumn(
                    "Visited",
                    help="Check if you've visited this country",
                    default=False,
                )
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            key="single_player_data_editor"
        )

        # Update selected countries in session state based on edited data
        for _, row in edited_df.iterrows():
            if row['Visited'] and row['code'] not in st.session_state.single_player_selected_countries:
                st.session_state.single_player_selected_countries.add(row['code'])
            elif not row['Visited'] and row['code'] in st.session_state.single_player_selected_countries:
                st.session_state.single_player_selected_countries.remove(row['code'])
        col1, col2 = st.columns([1, 1])
        with col1:
            # Callback function for save selected countries button
            def save_countries_callback():
                global players
                # Clear existing visits
                h5_utils.clear_player_visits("default", DEFAULT_H5_FILE)
                # Add new visits
                if st.session_state.single_player_selected_countries:
                    h5_utils.update_visits("default", list(st.session_state.single_player_selected_countries),
                                           DEFAULT_H5_FILE)
                visit_count = len(st.session_state.single_player_selected_countries)
                st.session_state.save_countries_success = (f"Updated visited countries: {visit_count} countries marked "
                                                           f"as visited")
                # Refresh player data
                players = h5_utils.get_players(DEFAULT_H5_FILE)

            st.button("Save Selected Countries", key="single_player_save", on_click=save_countries_callback)

            # Display success message if it exists
            if 'save_countries_success' in st.session_state and st.session_state.save_countries_success:
                st.success(st.session_state.save_countries_success)
                st.session_state.save_countries_success = None

        with col2:
            # Callback function for toggle map button
            def toggle_map_callback():
                st.session_state.single_player_show_map = not st.session_state.single_player_show_map

            # Toggle map display
            st.button("Show Map" if not st.session_state.single_player_show_map else "Hide Map",
                      key="single_player_toggle_map", on_click=toggle_map_callback)

    # Display stats
    st.subheader("Statistics")
    total_countries = len(countries)
    visited_count = len(st.session_state.single_player_selected_countries)
    visited_percent = (visited_count / total_countries) * 100 if total_countries > 0 else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Countries", total_countries)
    col2.metric("Countries Visited", visited_count)
    col3.metric("Percentage Visited", f"{visited_percent:.1f}%")

    # Display map only if requested
    if st.session_state.single_player_show_map:
        st.subheader("Your World Map")

        # Create a temporary players dict with current selections for the map
        temp_players = {
            "default": {
                "colour": players.get("default", {}).get("colour", "#444444"),
                "visited": st.session_state.single_player_selected_countries
            }
        }

        # Add a placeholder to ensure something is displayed - defining outside try block
        map_placeholder = st.empty()
        map_placeholder.info("Rendering map... Please wait.")

        # Initialize m with a default value
        m = None

        try:
            m = build_map(temp_players, geo_data)
            try:
                # Only try to render if m was successfully created
                if m is not None:
                    # Try to render the map with folium_static
                    folium_static(m, width=1200, height=600)
                    # Clear the placeholder if successful
                    map_placeholder.empty()
                else:
                    st.error("Failed to build map")
                    map_placeholder.empty()
            except Exception as folium_error:
                import traceback
                # Try alternative rendering method
                try:
                    # Convert map to HTML and display with st.markdown
                    map_html = m.get_root().render()
                    map_placeholder.empty()  # Clear the placeholder
                    st.markdown(map_html, unsafe_allow_html=True)
                    st.success("Map rendered using alternative method.")
                except (ValueError, RuntimeError, AttributeError) as render_error:
                    map_placeholder.empty()  # Clear the placeholder
                    st.error(f"Error displaying map: {str(folium_error)}")
                    st.info(f"Alternative rendering failed: {str(render_error)}")
                    st.info("This could be due to an issue with the map data or the Folium library.")
                    # Display a message with a placeholder for the map
                    st.warning("Map could not be displayed. Please try refreshing the page or creating a new map.")
        except (ValueError, KeyError, ImportError, IOError, AttributeError) as build_error:
            st.error(f"Error creating map: {str(build_error)}")
            st.info("This could be due to an issue with the map data or the Folium library.")
            # Display a message with a placeholder for the map
            st.warning("Map could not be created. Please try refreshing the page or creating a new map.")
            try:
                # Try to render the map with folium_static
                folium_static(m, width=1200, height=600)
                # Clear the placeholder if successful
                map_placeholder.empty()
            except Exception as folium_error:
                import traceback
                # Try alternative rendering method
                try:
                    # Only attempt alternative rendering if m exists
                    if m is not None:
                        # Convert map to HTML and display with st.markdown
                        map_html = m.get_root().render()
                        map_placeholder.empty()  # Clear the placeholder
                        st.markdown(map_html, unsafe_allow_html=True)
                        st.success("Map rendered using alternative method.")
                    else:
                        map_placeholder.empty()
                        st.error("Failed to build map")
                except (ValueError, RuntimeError, AttributeError) as render_error:
                    map_placeholder.empty()  # Clear the placeholder
                    st.error(f"Error displaying map: {str(folium_error)}")
                    st.info(f"Alternative rendering failed: {str(render_error)}")
                    st.info("This could be due to an issue with the map data or the Folium library.")
                    # Display a message with a placeholder for the map
                    st.warning("Map could not be displayed. Please try refreshing the page or creating a new map.")
        except (ValueError, KeyError, ImportError, IOError, AttributeError) as build_error:
            st.error(f"Error creating map: {str(build_error)}")
            st.info("This could be due to an issue with the map data or the Folium library.")
            # Display a message with a placeholder for the map
            st.warning("Map could not be created. Please try refreshing the page or creating a new map.")


def multi_player_mode(geo_data, countries, palettes):
    global players

    # Handle all button clicks and state changes BEFORE rendering UI

    # Handle add player button click
    if 'add_player_button' in st.session_state and st.session_state.add_player_button:
        # Reset button state
        st.session_state.add_player_button = False

        # Get the selected color from session state
        selected_color_index = (st.session_state.player_color_selectbox
                                if 'player_color_selectbox' in st.session_state
                                else 0)
        color_options = (st.session_state.color_options
                         if 'color_options' in st.session_state
                         else ["#7ebce6"])
        new_player_color = (color_options[selected_color_index]
                            if selected_color_index < len(color_options)
                            else "#7ebce6")

        if not st.session_state.new_player_name:
            st.session_state.add_player_error = "Please enter a player name"
        elif st.session_state.new_player_name in players:
            st.session_state.add_player_error = f"Player '{st.session_state.new_player_name}' already exists!"
        else:
            h5_utils.add_player(st.session_state.new_player_name, new_player_color, DEFAULT_H5_FILE)
            st.session_state.add_player_success = f"Added player: {st.session_state.new_player_name}"
            players = h5_utils.get_players(DEFAULT_H5_FILE)
            # Initialize session state for the new player
            if 'multi_player_selections' in st.session_state:
                st.session_state.multi_player_selections[st.session_state.new_player_name] = set()
            st.session_state.new_player_name = ""  # Clear the input field
            st.rerun()

    # Handle delete player button click
    if 'delete_player_button' in st.session_state and st.session_state.delete_player_button:
        # Reset button state
        st.session_state.delete_player_button = False

        # Get selected player
        player_select_key = "selected_player_to_edit"
        if player_select_key in st.session_state and st.session_state[player_select_key]:
            selected_player = st.session_state[player_select_key]

            h5_utils.delete_player(selected_player, DEFAULT_H5_FILE)
            # Also remove from session state
            if ('multi_player_selections' in st.session_state and
                    selected_player in st.session_state.multi_player_selections):
                del st.session_state.multi_player_selections[selected_player]
            st.session_state.delete_player_success = f"Deleted player: {selected_player}"

            # Refresh player data
            players = h5_utils.get_players(DEFAULT_H5_FILE)

            # If no players left or the deleted player was selected, update selection
            if not players:
                if 'selected_player_to_edit' in st.session_state:
                    st.session_state.pop(player_select_key, None)
                st.rerun()
            elif selected_player == st.session_state[player_select_key] and players:
                st.session_state[player_select_key] = list(players.keys())[0]
                st.rerun()

    # Handle clear countries button click
    if 'clear_countries_button' in st.session_state and st.session_state.clear_countries_button:
        # Reset button state
        st.session_state.clear_countries_button = False

        # Get selected player
        player_select_key = "selected_player_to_edit"
        if player_select_key in st.session_state and st.session_state[player_select_key]:
            selected_player = st.session_state[player_select_key]

            # Clear in database
            h5_utils.clear_player_visits(selected_player, DEFAULT_H5_FILE)
            # Clear in session state
            if ('multi_player_selections' in st.session_state and
                    selected_player in st.session_state.multi_player_selections):
                st.session_state.multi_player_selections[selected_player] = set()
            st.session_state.clear_countries_success = f"Cleared visited countries for: {selected_player}"

            # Refresh player data
            players = h5_utils.get_players(DEFAULT_H5_FILE)

    # Handle save all players button click
    if 'save_all_players_button' in st.session_state and st.session_state.save_all_players_button:
        # Reset button state
        st.session_state.save_all_players_button = False

        if 'multi_player_selections' in st.session_state:
            # Save all players' selections to the database
            for playerid, selectedcountries in st.session_state.multi_player_selections.items():
                if playerid in players:  # Only save for existing players
                    # Clear existing visits
                    h5_utils.clear_player_visits(playerid, DEFAULT_H5_FILE)
                    # Add new visits
                    if selectedcountries:
                        h5_utils.update_visits(playerid, list(selectedcountries), DEFAULT_H5_FILE)
            st.session_state.save_all_players_success = "Saved all players' country selections"
            # Refresh player data
            players = h5_utils.get_players(DEFAULT_H5_FILE)

    # Handle individual player save button clicks
    for player_id in players.keys() if players else []:
        save_key = f"save_{player_id}"
        if save_key in st.session_state and st.session_state[save_key]:
            # Reset button state
            st.session_state[save_key] = False

            # Clear existing visits
            h5_utils.clear_player_visits(player_id, DEFAULT_H5_FILE)
            # Add new visits
            if ('multi_player_selections' in st.session_state and
                    player_id in st.session_state.multi_player_selections and
                    st.session_state.multi_player_selections[player_id]):
                # Update player's visited countries in the database
                selections = list(st.session_state.multi_player_selections[player_id])
                h5_utils.update_visits(player_id, selections, DEFAULT_H5_FILE)
            # Get count of visited countries for this player
            visited_count = len(st.session_state.multi_player_selections.get(player_id, set()))
            # Create success message
            successkey = f"save_{player_id}_success"
            success_msg = f"Updated visited countries for {player_id}: {visited_count} countries marked as visited"
            st.session_state[successkey] = success_msg
            # Refresh player data
            players = h5_utils.get_players(DEFAULT_H5_FILE)

    # Handle toggle map button click
    if 'multi_player_toggle_map' in st.session_state and st.session_state.multi_player_toggle_map:
        # Reset button state
        st.session_state.multi_player_toggle_map = False

        # Toggle map display state
        if 'multi_player_show_map' in st.session_state:
            st.session_state.multi_player_show_map = not st.session_state.multi_player_show_map
        else:
            st.session_state.multi_player_show_map = True

    # Process data editor changes for each player
    if 'multi_player_selections' in st.session_state and players:
        for player_id in players:
            editor_key = f"multi_player_{player_id}_data_editor"
            if editor_key in st.session_state and st.session_state[editor_key] is not None:
                edited_df = st.session_state[editor_key]
                if isinstance(edited_df, pd.DataFrame):
                    # Ensure this player has an entry in the session state
                    if player_id not in st.session_state.multi_player_selections:
                        st.session_state.multi_player_selections[player_id] = players[player_id]["visited"].copy()

                    # Update selected countries in session state based on edited data
                    for _, row in edited_df.iterrows():
                        if 'Visited' in row and 'code' in row:
                            if row['Visited'] and row['code'] not in st.session_state.multi_player_selections[
                                    player_id]:
                                st.session_state.multi_player_selections[player_id].add(row['code'])
                            elif not row['Visited'] and row['code'] in st.session_state.multi_player_selections[
                                    player_id]:
                                st.session_state.multi_player_selections[player_id].remove(row['code'])

    # Now begin rendering UI
    st.title("Multi-Player Mode")
    # Initialize if needed
    if not os.path.exists(DEFAULT_H5_FILE):
        h5_utils.init_h5(DEFAULT_H5_FILE)
    # Get player data
    players = h5_utils.get_players(DEFAULT_H5_FILE)

    # Initialize session state for showing map
    if 'multi_player_show_map' not in st.session_state:
        st.session_state.multi_player_show_map = False

    # Initialize session state for player selections
    if 'multi_player_selections' not in st.session_state:
        st.session_state.multi_player_selections = {}
        # Initialize with data from the database
        for player_id, player_data in players.items():
            st.session_state.multi_player_selections[player_id] = player_data["visited"].copy()

    # Player management
    st.subheader("Players")
    # Add new player
    with st.expander("Add New Player"):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Player Name", key="new_player_name")
        with col2:
            # Create a flattened list of all colors from all palettes with their names
            # Use session state to store color options to ensure consistency between renders
            if 'all_palette_colors' not in st.session_state:
                all_palette_colors = []

                # Get color information from the palettes dictionary
                color_info = palettes.get("_color_info", {})

                # Process all colors from all palettes with deduplication
                unique_colors = set()
                for palette_name, colors in palettes.items():
                    # Skip the _color_info key
                    if palette_name == "_color_info":
                        continue

                    for color in colors:
                        # Only add if we haven't seen this color before
                        if color not in unique_colors:
                            unique_colors.add(color)
                            # Get color name from the Colors class if available
                            color_class_name = h5_utils.Colors.get_color_name(color)

                            # If not found in Colors class, use name from color_info or hex code as fallback
                            if color_class_name == color:  # Not found in Colors class
                                color_name = color_info.get(color, color)
                                display_name = color_name
                            else:
                                # Use the name from Colors class
                                display_name = color_class_name

                            all_palette_colors.append({"name": f"{display_name} ({color})", "hex": color})

                # Sort colors by name for better organization
                all_palette_colors.sort(key=lambda x: x["name"])

                # Store in session state
                st.session_state.all_palette_colors = all_palette_colors
                st.session_state.color_options = [color["hex"] for color in all_palette_colors]
                st.session_state.color_labels = [color["name"] for color in all_palette_colors]
                # Default to a random color only the first time
                # Generate random index if color options exist, otherwise default to 0
                max_index = len(st.session_state.color_options) - 1
                # Set default color index based on available options
                st.session_state.default_color_index = 0
                if st.session_state.color_options:
                    st.session_state.default_color_index = random.randint(0, max_index)

            # Use the stored values from session state
            color_options = st.session_state.color_options
            color_labels = st.session_state.color_labels

            # Use selectbox with stored options
            # Initialize the key in session state if it doesn't exist
            if "player_color_selectbox" not in st.session_state:
                st.session_state.player_color_selectbox = st.session_state.default_color_index

            selected_color_index = st.selectbox(
                "Player Color",
                options=range(len(color_options)),
                format_func=lambda r_i: color_labels[r_i] if r_i < len(color_labels) else "",
                key="player_color_selectbox"
            )

            # Get the selected color
            new_player_color = color_options[selected_color_index] if color_options else "#7ebce6"
            # Display the selected color
            color_display_html = (
                f'<div style="background-color:{new_player_color};'
                f'width:100%;height:30px;border-radius:5px;"></div>'
            )
            st.markdown(color_display_html, unsafe_allow_html=True)

        # Button with no callback - handled at beginning of function
        st.button("Add Player", key="add_player_button")

        # Display error or success message if they exist
        if 'add_player_error' in st.session_state and st.session_state.add_player_error:
            st.error(st.session_state.add_player_error)
            st.session_state.add_player_error = None
        if 'add_player_success' in st.session_state and st.session_state.add_player_success:
            st.success(st.session_state.add_player_success)
            st.session_state.add_player_success = None

    # Select player to edit
    if players:
        # Use a consistent key for the player selection
        player_select_key = "selected_player_to_edit"

        # Initialize the key in session state if it doesn't exist
        if player_select_key not in st.session_state and players:
            st.session_state[player_select_key] = list(players.keys())[0]

        selected_player = st.selectbox("Select Player to Edit", list(players.keys()), key=player_select_key)

        # Player actions
        col1, col2, col3 = st.columns(3)
        with col1:
            # Button with no callback - handled at beginning of function
            st.button("Delete Player", key="delete_player_button")

            # Display success message if it exists
            if 'delete_player_success' in st.session_state and st.session_state.delete_player_success:
                st.success(st.session_state.delete_player_success)
                st.session_state.delete_player_success = None

        with col2:
            # Button with no callback - handled at beginning of function
            st.button("Clear Visited Countries", key="clear_countries_button")

            # Display success message if it exists
            if 'clear_countries_success' in st.session_state and st.session_state.clear_countries_success:
                st.success(st.session_state.clear_countries_success)
                st.session_state.clear_countries_success = None

        with col3:
            # Button with no callback - handled at beginning of function
            st.button("Save All Players", key="save_all_players_button")

            # Display success message if it exists
            if 'save_all_players_success' in st.session_state and st.session_state.save_all_players_success:
                st.success(st.session_state.save_all_players_success)
                st.session_state.save_all_players_success = None

        # Country selection for the selected player
        if selected_player in players:
            st.subheader(f"Countries Visited by {selected_player}")

            # Ensure this player has an entry in the session state
            if selected_player not in st.session_state.multi_player_selections:
                st.session_state.multi_player_selections[selected_player] = players[selected_player]["visited"].copy()

            # Search box for countries
            search_term = st.text_input(f"Search for a country to add to {selected_player}'s visits",
                                        key=f"search_{selected_player}")

            # Filter countries based on search
            filtered_countries = countries
            if search_term:
                filtered_countries = [c for c in countries if search_term.lower() in c['name'].lower()]

            # Create a DataFrame for easier display
            df = pd.DataFrame(filtered_countries)

            # Set 'Visited' based on session state selected countries
            df['Visited'] = df['code'].apply(lambda x: x in st.session_state.multi_player_selections[selected_player])

            # Display as a table with checkboxes
            st.data_editor(
                df,
                column_config={
                    "name": "Country",
                    "code": "Code",
                    "Visited": st.column_config.CheckboxColumn(
                        "Visited",
                        help="Check if this player has visited this country",
                        default=False,
                    )
                },
                hide_index=True,
                use_container_width=True,
                num_rows="fixed",
                key=f"multi_player_{selected_player}_data_editor"
            )

            # Button with no callback - handled at beginning of function
            st.button(f"Save {selected_player}'s Countries", key=f"save_{selected_player}")

            # Display success message if it exists
            success_key = f"save_{selected_player}_success"
            if success_key in st.session_state and st.session_state[success_key]:
                st.success(st.session_state[success_key])
                st.session_state[success_key] = None
    else:
        st.info("No players yet. Add a player to get started!")

    # Button with no callback - handled at beginning of function
    st.button("Show Map" if not st.session_state.multi_player_show_map else "Hide Map",
              key="multi_player_toggle_map")

    # Display map only if requested
    if st.session_state.multi_player_show_map:
        st.subheader("Multi-Player World Map")

        # Create a temporary players dict with current selections for the map
        temp_players = {}
        for player_id, player_data in players.items():
            temp_players[player_id] = {
                "colour": player_data["colour"],
                "visited": st.session_state.multi_player_selections.get(player_id, set())
            }

        # Add a placeholder to ensure something is displayed - defining outside try block
        map_placeholder = st.empty()
        map_placeholder.info("Rendering map... Please wait.")

        try:
            m = build_map(temp_players, geo_data)
            if m is not None:
                try:
                    # Try to render the map with folium_static
                    folium_static(m, width=1200, height=600)
                    # Clear the placeholder if successful
                    map_placeholder.empty()
                except (RuntimeError, ValueError, TypeError) as folium_error:
                    # Try alternative rendering method with specific error handling
                    try:
                        # Convert map to HTML and display with st.markdown
                        map_html = m.get_root().render()
                        map_placeholder.empty()  # Clear the placeholder
                        st.markdown(map_html, unsafe_allow_html=True)
                        st.success("Map rendered using alternative method.")
                    except (ValueError, RuntimeError, AttributeError) as render_error:
                        map_placeholder.empty()  # Clear the placeholder
                        st.error(f"Error displaying map: {str(folium_error)}")
                        st.info(f"Alternative rendering failed: {str(render_error)}")
                        st.warning("Map could not be displayed. Please try refreshing the page or creating a new map.")
            else:
                map_placeholder.empty()
                st.error("Failed to build map")
        except Exception as map_error:
            st.error(f"Error creating map: {str(map_error)}")
            st.warning("Map could not be created. Please try refreshing the page or creating a new map.")


# Check essential requirements
if not os.path.exists("JSON"):
    print("ERROR: JSON directory not found!")
elif not os.path.exists(GEOJSON_PATH):
    print(f"ERROR: countries.geojson not found: {os.path.abspath(GEOJSON_PATH)}")
elif not os.path.exists(os.path.join("JSON", "palettes.json")):
    print(f"ERROR: palettes.json not found: {os.path.abspath(os.path.join('JSON', 'palettes.json'))}")

try:
    # Force Streamlit to show something
    st.empty()
    st.write("Initializing application...")
    # Run the main function
    main()
except Exception as e:
    import traceback

    traceback.print_exc()
    # Still try to display something
    st.title("Countries Visited Map")
    st.error(f"An error occurred: {str(e)}")
    st.info("Please check the terminal for more details.")
    # Display troubleshooting information
    st.subheader("Troubleshooting Information")
    st.info("""
    If you're seeing a blank screen or only "Running..." is displayed:
    1. Check the terminal for error messages
    2. Make sure all dependencies are installed correctly
    3. Try running: `streamlit run app.py --server.runOnSave=true`
    4. Or try: `streamlit run app.py --logger.level=debug`
    See TROUBLESHOOTING.md for more information.
    """)
