import streamlit as st
import folium
from folium.plugins import Fullscreen
from streamlit_folium import folium_static
import json
import os
import h5_utils
import random
import pandas as pd
from streamlit_oauth import OAuth2Component
import sys

# Check if the script is being run directly
if __name__ == "__main__" and not sys.argv[0].endswith("streamlit") and not os.environ.get("STREAMLIT_SCRIPT_PATH"):
    print("This app must be run with `streamlit run app.py`")
    print("Please use the following command:")
    print(f"    streamlit run {os.path.abspath(__file__)}")
    sys.exit(1)

# Set page configuration
st.set_page_config(
    page_title="Countries Visited Map",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
DEFAULT_H5_FILE = "countries_visited.h5"
GEOJSON_PATH = "JSON/countries.geojson"

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
    return geo_data, countries


# Load palettes
@st.cache_data
def load_palettes():
    return h5_utils.get_palettes()


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

    def style_fn(feature):
        iso = feature["properties"].get("ISO3166-1-Alpha-2", "")
        if iso == '-99':  # Skip non-country territories
            return {"fillColor": "#ffffff", "fillOpacity": 0.1, "color": "#999", "weight": 0.5}

        owners = [player_id for player_id, player_info in players.items() if iso in player_info["visited"]]

        if not owners:  # Nobody visited
            return {"fillColor": "#ffffff", "color": "#999", "weight": 0.5}

        if len(owners) == 1:  # Single owner → their colour
            return {"fillColor": players[owners[0]]["colour"],
                    "color": "#444", "weight": 0.5}

        # Multiple owners → simple average mix
        cols = [players[o]["colour"].lstrip("#") for o in owners]
        rgb = [[int(c[idx:idx + 2], 16) for idx in (0, 2, 4)] for c in cols]
        mix = tuple(int(sum(x) / len(x)) for x in zip(*rgb))
        return {"fillColor": "#{:02x}{:02x}{:02x}".format(*mix),
                "color": "#222", "weight": 0.5}

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
        "https://oauth2.googleapis.com/token",
        "https://oauth2.googleapis.com/revoke",
        redirect_uri
    )

    return oauth2


# Main app function
def main():
    # Load data
    geo_data, countries = load_country_data()
    palettes = load_palettes()

    # Sidebar
    with st.sidebar:
        st.title("Countries Visited Map")

        # OAuth login (placeholder for now)
        if not st.session_state.logged_in:
            st.subheader("Login")
            if st.button("Login with Google"):
                # This would be replaced with actual OAuth flow
                st.session_state.logged_in = True
                st.session_state.user_id = "demo_user"
                st.rerun()
        else:
            st.success(f"Logged in as {st.session_state.user_id}")
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.rerun()

        st.divider()

        # Mode selection
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
                if os.path.exists(DEFAULT_H5_FILE):
                    os.remove(DEFAULT_H5_FILE)
                h5_utils.init_h5(DEFAULT_H5_FILE)
                st.success("Created new map!")
                st.rerun()

        with col2:
            uploaded_file = st.file_uploader("Load Map", type=["h5"])
            if uploaded_file:
                with open(DEFAULT_H5_FILE, "wb") as f:
                    f.write(uploaded_file.getvalue())
                st.success("Map loaded!")
                st.rerun()

        # Download current map
        if os.path.exists(DEFAULT_H5_FILE):
            with open(DEFAULT_H5_FILE, "rb") as f:
                st.download_button(
                    label="Download Map",
                    data=f,
                    file_name="countries_visited.h5",
                    mime="application/x-hdf5"
                )

    # Main content
    if st.session_state.current_mode == "single":
        single_player_mode(geo_data, countries)
    else:
        multi_player_mode(geo_data, countries, palettes)


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
    )

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
    m = build_map(players, geo_data)
    folium_static(m, width=1200, height=600)


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
            all_palette_colors = []

            # Read the JSON file once
            with open("JSON/palettes.json", encoding="utf-8") as f:
                palettes_data = json.load(f)

            # Create a mapping of hex codes to color names
            color_name_map = {}
            for palette in palettes_data["palettes"]:
                for color_data in palette["colors"]:
                    hex_code = "#" + color_data["hex"] if not color_data["hex"].startswith("#") else color_data["hex"]
                    color_name_map[hex_code] = color_data.get("name", hex_code)

            # Process all colors from all palettes
            for palette_name, colors in palettes.items():
                for color in colors:
                    # Get color name from the map or use hex code as fallback
                    color_name = color_name_map.get(color, color)
                    all_palette_colors.append({"name": f"{color_name} ({color})", "hex": color})

            # Sort colors by name for better organization
            all_palette_colors.sort(key=lambda x: x["name"])

            # Create options for selectbox
            color_options = [color["hex"] for color in all_palette_colors]
            color_labels = [color["name"] for color in all_palette_colors]

            # Default to a random color
            default_index = random.randint(0, len(color_options)-1) if color_options else 0

            # Use selectbox instead of color_picker
            selected_color_index = st.selectbox(
                "Player Color",
                options=range(len(color_options)),
                format_func=lambda i: color_labels[i] if i < len(color_labels) else "",
                index=default_index
            )

            new_player_color = color_options[selected_color_index] if color_options else "#7ebce6"

            # Display the selected color
            st.markdown(f'<div style="background-color:{new_player_color};width:100%;height:30px;border-radius:5px;"></div>', unsafe_allow_html=True)

        if st.button("Add Player") and new_player_name:
            if new_player_name in players:
                st.error(f"Player '{new_player_name}' already exists!")
            else:
                h5_utils.add_player(new_player_name, new_player_color, DEFAULT_H5_FILE)
                st.success(f"Added player: {new_player_name}")
                players = h5_utils.get_players(DEFAULT_H5_FILE)

    # Select player to edit
    if players:
        selected_player = st.selectbox("Select Player to Edit", list(players.keys()))

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

            # Display as a table with checkboxes
            edited_df = st.data_editor(
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
            )

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
    m = build_map(players, geo_data)
    folium_static(m, width=1200, height=600)

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


if __name__ == "__main__":
    main()
