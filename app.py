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
except Exception as e:
    print(f"Error setting page configuration: {str(e)}")
    # Try with minimal configuration
    try:
        st.set_page_config(page_title="Countries Visited Map")
        print("Minimal page configuration set successfully")
    except Exception as config_error:
        print(f"Error setting minimal page configuration: {str(config_error)}")
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
def build_map(players, geo_data):
    """
    Build a folium map with visited countries colored according to player colors.

    Args:
        players (dict): Dictionary of players with their visited countries and colors
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

                owners = [player_id for player_id, player_info in players.items() if iso in player_info["visited"]]

                if not owners:  # Nobody visited
                    return {"fillColor": "#ffffff", "color": "#999", "weight": 0.5}

                if len(owners) == 1:  # Single owner → their colour
                    return {"fillColor": players[owners[0]]["colour"],
                            "fillOpacity": 0.7,
                            "color": "#444", "weight": 0.5}

                # Multiple owners → simple average mix
                cols = [players[o]["colour"].lstrip("#") for o in owners]
                rgb = [[int(c[idx:idx + 2], 16) for idx in (0, 2, 4)] for c in cols]
                mix = tuple(int(sum(x) / len(x)) for x in zip(*rgb))
                return {"fillColor": "#{:02x}{:02x}{:02x}".format(*mix),
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
        if players:
            legend_html = """
            <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; 
                        padding: 10px; border-radius: 5px; border: 1px solid grey; max-width: 300px;">
            <h4 style="margin-top: 0;">Players</h4>
            """

            for i, (p, info) in enumerate(players.items(), 1):
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

    Returns:
        bool: True if the user successfully logged in, False otherwise
    """
    # Check if we just completed a successful registration
    if 'registration_successful' in st.session_state and st.session_state.registration_successful:
        # Clear the flag
        st.session_state.registration_successful = False

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
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")

        login_button = st.button("Login", type="primary", use_container_width=True)

        if login_button:
            if not login_username or not login_password:
                st.error("Please enter both username and password")
            else:
                # Authenticate user
                if redis_utils.authenticate_user(login_username, login_password):
                    st.success(f"Welcome back, {login_username}!")
                    # Set session state
                    st.session_state.logged_in = True
                    st.session_state.user_id = login_username
                    # Rerun to update UI
                    st.rerun()
                    return True
                else:
                    st.error("Invalid username or password")

        # Demo login option
        st.divider()
        st.write("Or use demo login:")
        if st.button("Login as Demo User", use_container_width=True):
            st.session_state.logged_in = True
            st.session_state.user_id = "demo_user"
            st.rerun()
            return True

    # Registration form
    with col2:
        st.subheader("Register")
        reg_username = st.text_input("Choose a Username", key="reg_username")
        reg_password = st.text_input("Choose a Password", type="password", key="reg_password")
        reg_confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")

        register_button = st.button("Register", type="primary", use_container_width=True)

        if register_button:
            if not reg_username or not reg_password or not reg_confirm_password:
                st.error("Please fill in all fields")
            elif reg_password != reg_confirm_password:
                st.error("Passwords do not match")
            elif redis_utils.user_exists(reg_username):
                st.error("Username already exists. Please choose another one.")
            else:
                # Register new user
                if redis_utils.add_user(reg_username, reg_password):
                    st.success("Registration successful! You can now log in.")
                    # Set a flag to indicate successful registration
                    st.session_state.registration_successful = True
                    # Rerun to reset the form
                    st.rerun()
                else:
                    st.error("Registration failed. Please try again later.")

    return False


# Main app function
def main():
    try:
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
                except Exception:
                    pass
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
                except Exception:
                    pass

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
                if st.button("Logout"):
                    st.session_state.logged_in = False
                    st.session_state.user_id = None
                    st.rerun()

                st.divider()

                # Mode selection (only shown when logged in)
                st.subheader("Mode")
                mode = st.radio("Select Mode", ["Single Player", "Multi Player"],
                                index=0 if st.session_state.current_mode == "single" else 1)
                st.session_state.current_mode = "single" if mode == "Single Player" else "multi"

                # File management
                st.divider()
                st.subheader("Map File")

                # Create new map or load existing
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("New Map"):
                        try:
                            if os.path.exists(DEFAULT_H5_FILE):
                                os.remove(DEFAULT_H5_FILE)
                            success = h5_utils.init_h5(DEFAULT_H5_FILE)
                            if success:
                                st.success("Created new map!")
                                st.rerun()
                            else:
                                st.error("Failed to create new map. Check the terminal for details.")
                                st.info(f"Current working directory: {os.getcwd()}")
                                st.info(f"Attempted to create file at: {os.path.abspath(DEFAULT_H5_FILE)}")
                        except Exception as exc:
                            st.error(f"Error creating new map: {str(exc)}")
                            st.info(f"Current working directory: {os.getcwd()}")
                            st.info(f"Attempted to create file at: {os.path.abspath(DEFAULT_H5_FILE)}")

                with col2:
                    uploaded_file = st.file_uploader("Load Map", type=["h5"])
                    if uploaded_file:
                        try:
                            with open(DEFAULT_H5_FILE, "wb") as f:
                                f.write(uploaded_file.getvalue())
                            st.success("Map loaded!")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Error loading map: {str(exc)}")

                # Download current map
                if os.path.exists(DEFAULT_H5_FILE):
                    try:
                        with open(DEFAULT_H5_FILE, "rb") as f:
                            st.download_button(
                                label="Download Map",
                                data=f,
                                file_name="countries_visited.h5",
                                mime="application/x-hdf5"
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
    # Country selection
    st.subheader("Select Countries You've Visited")
    # Search box for countries
    search_term = st.text_input("Search for a country")
    # Filter countries based on search
    filtered_countries = countries
    if search_term:
        filtered_countries = [c for c in countries if search_term.lower() in c['name'].lower()]
    # Create a DataFrame for easier display
    df = pd.DataFrame(filtered_countries)
    df['Visited'] = df['code'].apply(lambda x: x in visited)

    # Initialize session state for edited data if not exists
    if 'single_player_edited_df' not in st.session_state:
        st.session_state.single_player_edited_df = df.copy()

    # If search term changed, update the session state dataframe but preserve visited status
    if search_term:
        # Get current visited status from session state
        current_visited = {}
        if 'single_player_edited_df' in st.session_state:
            for _, row in st.session_state.single_player_edited_df.iterrows():
                if row['Visited']:
                    current_visited[row['code']] = True

        # Update session state with new filtered countries but preserve visited status
        st.session_state.single_player_edited_df = df.copy()
        for i, row in st.session_state.single_player_edited_df.iterrows():
            if row['code'] in current_visited:
                st.session_state.single_player_edited_df.at[i, 'Visited'] = True

    # Display as a table with checkboxes
    edited_df = st.data_editor(
        st.session_state.single_player_edited_df,
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

    # Update session state with edited data
    st.session_state.single_player_edited_df = edited_df

    # Update visited countries if changed
    new_visited = set(edited_df[edited_df['Visited']]['code'].tolist())
    if new_visited != visited:
        # Clear existing visits
        h5_utils.clear_player_visits("default", DEFAULT_H5_FILE)
        # Add new visits
        if new_visited:
            h5_utils.update_visits("default", list(new_visited), DEFAULT_H5_FILE)
        st.success(f"Updated visited countries: {len(new_visited)} countries marked as visited")
        # Refresh player data
        players = h5_utils.get_players(DEFAULT_H5_FILE)
    # Display stats
    st.subheader("Statistics")
    total_countries = len(countries)
    visited_count = len(visited)
    visited_percent = (visited_count / total_countries) * 100 if total_countries > 0 else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Countries", total_countries)
    col2.metric("Countries Visited", visited_count)
    col3.metric("Percentage Visited", f"{visited_percent:.1f}%")
    # Display map
    st.subheader("Your World Map")
    try:
        m = build_map(players, geo_data)
        # Add a placeholder to ensure something is displayed
        map_placeholder = st.empty()
        map_placeholder.info("Rendering map... Please wait.")
        try:
            # Try to render the map with folium_static
            folium_static(m, width=1200, height=600)
            # Clear the placeholder if successful
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
            except Exception:
                map_placeholder.empty()  # Clear the placeholder
                st.error(f"Error displaying map: {str(folium_error)}")
                st.info("This could be due to an issue with the map data or the Folium library.")
                # Display a message with a placeholder for the map
                st.warning("Map could not be displayed. Please try refreshing the page or creating a new map.")
    except Exception as build_error:
        st.error(f"Error creating map: {str(build_error)}")
        st.info("This could be due to an issue with the map data or the Folium library.")
        # Display a message with a placeholder for the map
        st.warning("Map could not be created. Please try refreshing the page or creating a new map.")


def multi_player_mode(geo_data, countries, palettes):
    st.title("Multi-Player Mode")
    # Initialize if needed
    if not os.path.exists(DEFAULT_H5_FILE):
        h5_utils.init_h5(DEFAULT_H5_FILE)
    # Get player data
    players = h5_utils.get_players(DEFAULT_H5_FILE)
    # Player management
    st.subheader("Players")
    # Add new player
    with st.expander("Add New Player"):
        col1, col2 = st.columns(2)
        with col1:
            new_player_name = st.text_input("Player Name")
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
                st.session_state.default_color_index = random.randint(0, len(st.session_state.color_options)-1) if st.session_state.color_options else 0

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
        if st.button("Add Player") and new_player_name:
            if new_player_name in players:
                st.error(f"Player '{new_player_name}' already exists!")
            else:
                h5_utils.add_player(new_player_name, new_player_color, DEFAULT_H5_FILE)
                st.success(f"Added player: {new_player_name}")
                players = h5_utils.get_players(DEFAULT_H5_FILE)
    # Select player to edit
    if players:
        # Use a consistent key for the player selection
        player_select_key = "selected_player_to_edit"

        # Initialize the key in session state if it doesn't exist
        if player_select_key not in st.session_state and players:
            st.session_state[player_select_key] = list(players.keys())[0]

        selected_player = st.selectbox("Select Player to Edit", list(players.keys()), key=player_select_key)
        # Player actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Delete Player"):
                h5_utils.delete_player(selected_player, DEFAULT_H5_FILE)
                st.success(f"Deleted player: {selected_player}")
                players = h5_utils.get_players(DEFAULT_H5_FILE)
                st.rerun()
        with col2:
            if st.button("Clear Visited Countries"):
                h5_utils.clear_player_visits(selected_player, DEFAULT_H5_FILE)
                st.success(f"Cleared visited countries for: {selected_player}")
                players = h5_utils.get_players(DEFAULT_H5_FILE)
        # Country selection for the selected player
        if selected_player in players:
            st.subheader(f"Countries Visited by {selected_player}")
            # Search box for countries
            search_term = st.text_input(f"Search for a country to add to {selected_player}'s visits")
            # Filter countries based on search
            filtered_countries = countries
            if search_term:
                filtered_countries = [c for c in countries if search_term.lower() in c['name'].lower()]
            # Get visited countries for this player
            visited = players[selected_player]["visited"]
            # Create a DataFrame for easier display
            df = pd.DataFrame(filtered_countries)
            df['Visited'] = df['code'].apply(lambda x: x in visited)

            # Initialize session state for edited data if not exists
            session_key = f"multi_player_{selected_player}_edited_df"
            if session_key not in st.session_state:
                st.session_state[session_key] = df.copy()

            # If search term changed, update the session state dataframe but preserve visited status
            if search_term:
                # Get current visited status from session state
                current_visited = {}
                if session_key in st.session_state:
                    for _, row in st.session_state[session_key].iterrows():
                        if row['Visited']:
                            current_visited[row['code']] = True

                # Update session state with new filtered countries but preserve visited status
                st.session_state[session_key] = df.copy()
                for i, row in st.session_state[session_key].iterrows():
                    if row['code'] in current_visited:
                        st.session_state[session_key].at[i, 'Visited'] = True

            # Display as a table with checkboxes
            edited_df = st.data_editor(
                st.session_state[session_key],
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

            # Update session state with edited data
            st.session_state[session_key] = edited_df

            # Update visited countries if changed
            new_visited = set(edited_df[edited_df['Visited']]['code'].tolist())
            if new_visited != visited:
                # Clear existing visits
                h5_utils.clear_player_visits(selected_player, DEFAULT_H5_FILE)
                # Add new visits
                if new_visited:
                    h5_utils.update_visits(selected_player, list(new_visited), DEFAULT_H5_FILE)
                st.success(
                    f"Updated visited countries for {selected_player}: {len(new_visited)} countries marked as visited")
                # Refresh player data
                players = h5_utils.get_players(DEFAULT_H5_FILE)
    else:
        st.info("No players yet. Add a player to get started!")
    # Display map
    st.subheader("Multi-Player World Map")
    try:
        m = build_map(players, geo_data)
        # Add a placeholder to ensure something is displayed
        map_placeholder = st.empty()
        map_placeholder.info("Rendering map... Please wait.")
        try:
            # Try to render the map with folium_static
            folium_static(m, width=1200, height=600)
            # Clear the placeholder if successful
            map_placeholder.empty()
        except Exception as folium_exception:
            import traceback
            # Try alternative rendering method
            try:
                # Convert map to HTML and display with st.markdown
                map_html = m.get_root().render()
                map_placeholder.empty()  # Clear the placeholder
                st.markdown(map_html, unsafe_allow_html=True)
                st.success("Map rendered using alternative method.")
            except Exception:
                map_placeholder.empty()  # Clear the placeholder
                st.error(f"Error displaying map: {str(folium_exception)}")
                st.info("This could be due to an issue with the map data or the Folium library.")
                # Display a message with a placeholder for the map
                st.warning("Map could not be displayed. Please try refreshing the page or creating a new map.")
    except Exception as map_build_error:
        st.error(f"Error creating map: {str(map_build_error)}")
        st.info("This could be due to an issue with the map data or the Folium library.")
        # Display a message with a placeholder for the map
        st.warning("Map could not be created. Please try refreshing the page or creating a new map.")
    # Display overlap statistics
    if len(players) > 1:
        st.subheader("Country Overlap Statistics")
        # Calculate overlaps
        all_countries = set()
        for player_info in players.values():
            all_countries.update(player_info["visited"])
        overlap_data = []
        for country_code in all_countries:
            country_name = next((c['name'] for c in countries if c['code'] == country_code), country_code)
            visiting_players = [p for p, info in players.items() if country_code in info["visited"]]
            if len(visiting_players) > 1:  # Only show countries with overlaps
                overlap_data.append({
                    "Country": country_name,
                    "Code": country_code,
                    "Visitors": ", ".join(visiting_players),
                    "Count": len(visiting_players)
                })
        if overlap_data:
            overlap_df = pd.DataFrame(overlap_data)
            overlap_df = overlap_df.sort_values("Count", ascending=False)
            st.dataframe(overlap_df, use_container_width=True)
        else:
            st.info("No country overlaps found between players.")


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
