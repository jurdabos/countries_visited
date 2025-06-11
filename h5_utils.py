import h5py
import datetime
from datetime import UTC
import numpy as np
import json
import os


def init_h5(filename="countries_visited.h5", palette_hexes=None):
    """
    Initialize a new HDF5 file with the basic structure.
    Args:
        filename (str): Path to the HDF5 file to create
        palette_hexes (list): Optional list of hex color codes to save as a palette
    """
    with h5py.File(filename, "w") as f:
        # Creating players group
        f.create_group("/players")
        # Saving palette (optional)
        if palette_hexes is not None:
            dt = h5py.string_dtype(encoding='utf-8')
            f.create_dataset("/palettes/hex_codes",
                             data=np.array(palette_hexes, dtype=dt),
                             compression="gzip")


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


def get_palettes(json_path="JSON/palettes.json"):
    """
    Load color palettes from the JSON file.
    Args:
        json_path (str): Path to the palettes JSON file
    Returns:
        dict: Dictionary of palettes
    """
    with open(json_path, encoding="utf-8") as f:
        palettes_data = json.load(f)
    # Extracting hex codes from each palette
    palettes = {}
    for palette in palettes_data["palettes"]:
        name = palette["paletteName"]
        colors = [color["hex"] for color in palette["colors"]]
        palettes[name] = ["#" + color if not color.startswith("#") else color for color in colors]
    return palettes


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
