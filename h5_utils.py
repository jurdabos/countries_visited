import h5py
import datetime
from datetime import UTC
import numpy as np
import json
import os


class Colors:
    """
    Class containing ANSI color codes with informative names.
    These colors match the ones used in the palettes.json file.
    """
    # Basic reset and standard colors
    RESET = "\033[0m"
    WHITE = "\033[97m"
    BLACK = "\033[30m"

    # Colors from palettes.json
    CARIBBEAN_CURRENT = "\033[36m"  # Caribbean Current
    MINDARO = "\033[92m"  # Mindaro
    CHESTNUT = "\033[31m"  # Chestnut
    MAYA_BLUE = "\033[94m"  # Maya Blue
    PALE_DOGWOOD = "\033[93m"  # Pale Dogwood
    CAMBRIDGE_BLUE = "\033[32m"  # Cambridge Blue
    LION = "\033[33m"  # Lion
    ROSE_TAUPE = "\033[35m"  # Rose Taupe
    TAUPE_GRAY = "\033[90m"  # Taupe Gray
    FRENCH_GRAY = "\033[37m"  # French Gray

    # Caribbean Current shades
    DARK_CARIBBEAN_CURRENT = "\033[34m"  # Dark Caribbean Current shades
    LIGHT_CARIBBEAN_CURRENT = "\033[96m"  # Light Caribbean Current shades

    # Additional shades from palettes.json
    CARIBBEAN_CURRENT_DARKEST = "\033[30m"  # #030f11
    CARIBBEAN_CURRENT_DARKER = "\033[34m"  # #061e22
    CARIBBEAN_CURRENT_DARK = "\033[34m"  # #0d3c45
    CARIBBEAN_CURRENT_MEDIUM_DARK = "\033[36m"  # #135967
    CARIBBEAN_CURRENT_MEDIUM = "\033[36m"  # #19778a
    CARIBBEAN_CURRENT_MEDIUM_LIGHT = "\033[36m"  # #2095ac
    CARIBBEAN_CURRENT_LIGHT = "\033[96m"  # #26b3cf
    CARIBBEAN_CURRENT_LIGHTER = "\033[96m"  # #41c2dc
    CARIBBEAN_CURRENT_VERY_LIGHT = "\033[96m"  # #64cde3
    CARIBBEAN_CURRENT_EXTRA_LIGHT = "\033[96m"  # #86d8e9
    CARIBBEAN_CURRENT_ULTRA_LIGHT = "\033[97m"  # #a9e3ef
    CARIBBEAN_CURRENT_PALEST = "\033[97m"  # #cbeef6
    CARIBBEAN_CURRENT_LIGHTEST = "\033[97m"  # #eef9fc

    # Aliases for backward compatibility
    TEAL = CARIBBEAN_CURRENT
    LIME = MINDARO
    RUST = CHESTNUT
    BLUE = MAYA_BLUE
    PEACH = PALE_DOGWOOD
    SAGE = CAMBRIDGE_BLUE
    SAND = LION
    MAUVE = ROSE_TAUPE
    SLATE = TAUPE_GRAY
    SILVER = FRENCH_GRAY
    DARK_TEAL = DARK_CARIBBEAN_CURRENT
    LIGHT_TEAL = LIGHT_CARIBBEAN_CURRENT

    # Mapping of color names to hex codes for use in the app
    # This allows the app to display the proper color names from this class
    COLOR_MAP = {
        "CARIBBEAN_CURRENT": "#16697a",
        "MINDARO": "#dbf4a7",
        "CHESTNUT": "#a24936",
        "MAYA_BLUE": "#7ebce6",
        "PALE_DOGWOOD": "#e6beae",
        "CAMBRIDGE_BLUE": "#79af91",
        "LION": "#bf9f6f",
        "ROSE_TAUPE": "#996662",
        "TAUPE_GRAY": "#90838e",
        "FRENCH_GRAY": "#b2bdca",
        "CARIBBEAN_CURRENT_DARKEST": "#030f11",
        "CARIBBEAN_CURRENT_DARKER": "#061e22",
        "CARIBBEAN_CURRENT_DARK": "#0d3c45",
        "CARIBBEAN_CURRENT_MEDIUM_DARK": "#135967",
        "CARIBBEAN_CURRENT_MEDIUM": "#19778a",
        "CARIBBEAN_CURRENT_MEDIUM_LIGHT": "#2095ac",
        "CARIBBEAN_CURRENT_LIGHT": "#26b3cf",
        "CARIBBEAN_CURRENT_LIGHTER": "#41c2dc",
        "CARIBBEAN_CURRENT_VERY_LIGHT": "#64cde3",
        "CARIBBEAN_CURRENT_EXTRA_LIGHT": "#86d8e9",
        "CARIBBEAN_CURRENT_ULTRA_LIGHT": "#a9e3ef",
        "CARIBBEAN_CURRENT_PALEST": "#cbeef6",
        "CARIBBEAN_CURRENT_LIGHTEST": "#eef9fc"
    }

    # Reverse mapping for looking up color names by hex code
    @classmethod
    def get_color_name(cls, hex_code):
        """
        Get the color name for a given hex code.

        Args:
            hex_code (str): The hex code to look up (with or without # prefix)

        Returns:
            str: The color name if found, or the original hex code if not found
        """
        # Normalize hex code (ensure it has # prefix)
        if not hex_code.startswith('#'):
            hex_code = f"#{hex_code}"

        # Look up in the color map
        for name, code in cls.COLOR_MAP.items():
            if code.lower() == hex_code.lower():
                return name

        # Return the original hex code if not found
        return hex_code


def init_h5(filename="countries_visited.h5", palette_hexes=None):
    """
    Initialize a new HDF5 file with the basic structure.
    Args:
        filename (str): Path to the HDF5 file to create
        palette_hexes (list): Optional list of hex color codes to save as a palette
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with h5py.File(filename, "w") as f:
            # Creating players group
            f.create_group("/players")
            # Saving palette (optional)
            if palette_hexes is not None:
                dt = h5py.string_dtype(encoding='utf-8')
                f.create_dataset("/palettes/hex_codes",
                                data=np.array(palette_hexes, dtype=dt),
                                compression="gzip")
        return True
    except OSError as e:
        print(f"Error creating HDF5 file: {str(e)}")
        print(f"Filename: {filename}")
        print(f"Current working directory: {os.getcwd()}")
        return False
    except Exception as e:
        print(f"Unexpected error initializing HDF5 file: {str(e)}")
        print(f"Filename: {filename}")
        print(f"Current working directory: {os.getcwd()}")
        return False


def add_player(player_id, colour, filename="countries_visited.h5"):
    """
    Add a new player to the HDF5 file.
    Args:
        player_id (str): Unique identifier for the player
        colour (str): Hex color code for the player (e.g. "#7ebce6")
        filename (str): Path to the HDF5 file
    """
    with h5py.File(filename, "a") as f:
        g = f.require_group(f"/players/{player_id}")
        if "visited" not in g:  # create once
            dt = h5py.string_dtype(encoding='utf-8')
            g.create_dataset("visited", shape=(0,),
                             maxshape=(None,), dtype=dt)
        g.attrs["colour"] = colour
        g.attrs["created"] = datetime.datetime.now(UTC).isoformat()


def update_visits(player_id, iso_codes, filename="countries_visited.h5"):
    """
    Update the list of countries visited by a player.
    Args:
        player_id (str): Unique identifier for the player
        iso_codes (list): List of ISO-3166-1 alpha-2 country codes
        filename (str): Path to the HDF5 file
    """
    with h5py.File(filename, "a") as f:
        dset = f[f"/players/{player_id}/visited"]
        now = len(dset)
        dset.resize((now + len(iso_codes),))
        dset[now:] = iso_codes  # to write new slice


def get_players(filename="countries_visited.h5"):
    """
    Get a list of all players in the HDF5 file.
    Args:
        filename (str): Path to the HDF5 file
    Returns:
        dict: Dictionary with player information
    """
    if not os.path.exists(filename):
        return {}
    with h5py.File(filename, "r") as f:
        if "/players" not in f:
            return {}
        players = {
            name: {
                "colour": grp.attrs["colour"],
                "visited": set(grp["visited"][...].astype(str)),
                "created": grp.attrs["created"] if "created" in grp.attrs else ""
            }
            for name, grp in f["/players"].items()
        }
    return players


def get_palettes(json_path=None):
    """
    Load color palettes from the JSON file.
    Args:
        json_path (str): Path to the palettes JSON file. If None, uses default path.
    Returns:
        dict: Dictionary of palettes where each key is a palette name and each value is a list of hex codes.
              The dictionary also has a special key '_color_info' that contains detailed color information.
    """
    if json_path is None:
        json_path = os.path.join("JSON", "palettes.json")

    try:
        # Check if file exists
        if not os.path.exists(json_path):
            print(f"Palettes JSON file not found: {json_path}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Full path: {os.path.abspath(json_path)}")
            return {}

        with open(json_path, encoding="utf-8") as f:
            palettes_data = json.load(f)

        # Extracting color information from each palette
        palettes = {}
        color_info = {}  # Dictionary to store color information

        for palette in palettes_data.get("palettes", []):
            name = palette.get("paletteName", "Unknown")
            colors_info = []
            hex_codes = []

            for color in palette.get("colors", []):
                hex_code = color.get("hex", "")
                if not hex_code:
                    continue

                # Format hex code with # prefix if needed
                hex_code = "#" + hex_code if not hex_code.startswith("#") else hex_code

                # Get color name with a descriptive fallback if not provided
                color_name = color.get("name", "")
                if not color_name or color_name.startswith(palette.get("paletteName", "")):
                    # For shades palettes, provide more descriptive names
                    if "shades" in name:
                        position = color.get("position", 0)
                        if position <= 3:
                            color_name = f"Dark {name.split('_')[0].title()}"
                        elif position >= 7:
                            color_name = f"Light {name.split('_')[0].title()}"
                        else:
                            color_name = f"Medium {name.split('_')[0].title()}"
                    else:
                        # Default to hex code if no better name is available
                        color_name = f"Color {hex_code}"

                colors_info.append({
                    "hex": hex_code,
                    "name": color_name
                })
                hex_codes.append(hex_code)

                # Store color information in the global color_info dictionary
                if hex_code not in color_info:
                    color_info[hex_code] = color_name

            # Store hex codes for backward compatibility
            palettes[name] = hex_codes

        # Add color information to the palettes dictionary with a special key
        palettes["_color_info"] = color_info

        return palettes
    except FileNotFoundError:
        print(f"Palettes JSON file not found: {json_path}")
        print(f"Current working directory: {os.getcwd()}")
        return {}
    except json.JSONDecodeError:
        print(f"Error parsing palettes JSON file: {json_path}")
        print("The file may be corrupted or not in valid JSON format.")
        return {}
    except Exception as e:
        print(f"Error loading palettes: {str(e)}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Full path: {os.path.abspath(json_path)}")
        return {}


def clear_player_visits(player_id, filename="countries_visited.h5"):
    """
    Clear all visited countries for a player.
    Args:
        player_id (str): Unique identifier for the player
        filename (str): Path to the HDF5 file
    """
    with h5py.File(filename, "a") as f:
        if f"/players/{player_id}" in f:
            dset = f[f"/players/{player_id}/visited"]
            dset.resize((0,))


def delete_player(player_id, filename="countries_visited.h5"):
    """
    Delete a player from the HDF5 file.
    Args:
        player_id (str): Unique identifier for the player
        filename (str): Path to the HDF5 file
    """
    with h5py.File(filename, "a") as f:
        if f"/players/{player_id}" in f:
            del f[f"/players/{player_id}"]
