import os
import pytest
import h5py
import numpy as np
from datetime import datetime, UTC
import sys
import json

# Add the parent directory to sys.path to import h5_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import h5_utils


class TestH5Utils:
    """Test suite for h5_utils.py functions."""

    def test_init_h5(self, temp_dir):
        """Test initializing an HDF5 file."""
        # Test with default parameters
        h5_path = os.path.join(temp_dir, "test_init.h5")
        h5_utils.init_h5(h5_path)
        
        # Verify file structure
        with h5py.File(h5_path, "r") as f:
            assert "/players" in f
        
        # Test with palette
        palette = ["#FF0000", "#00FF00", "#0000FF"]
        h5_path2 = os.path.join(temp_dir, "test_init_palette.h5")
        h5_utils.init_h5(h5_path2, palette)
        
        # Verify palette was saved
        with h5py.File(h5_path2, "r") as f:
            assert "/palettes/hex_codes" in f
            saved_palette = f["/palettes/hex_codes"][...]
            assert len(saved_palette) == len(palette)
            for i, color in enumerate(palette):
                assert saved_palette[i] == color

    def test_add_player(self, temp_h5_file):
        """Test adding a player to the HDF5 file."""
        player_id = "test_player"
        color = "#FF0000"
        
        # Add a player
        h5_utils.add_player(player_id, color, temp_h5_file)
        
        # Verify player was added
        with h5py.File(temp_h5_file, "r") as f:
            assert f"/players/{player_id}" in f
            assert f[f"/players/{player_id}"].attrs["colour"] == color
            assert "created" in f[f"/players/{player_id}"].attrs
            assert f[f"/players/{player_id}/visited"].shape == (0,)
        
        # Test adding the same player again (should not error)
        h5_utils.add_player(player_id, "#00FF00", temp_h5_file)
        
        # Verify player was updated
        with h5py.File(temp_h5_file, "r") as f:
            assert f[f"/players/{player_id}"].attrs["colour"] == "#00FF00"

    def test_update_visits(self, temp_h5_file):
        """Test updating visited countries for a player."""
        player_id = "test_player"
        color = "#FF0000"
        
        # Add a player first
        h5_utils.add_player(player_id, color, temp_h5_file)
        
        # Update visits
        countries = ["US", "CA", "MX"]
        h5_utils.update_visits(player_id, countries, temp_h5_file)
        
        # Verify visits were updated
        with h5py.File(temp_h5_file, "r") as f:
            visited = f[f"/players/{player_id}/visited"][...]
            assert len(visited) == len(countries)
            for i, country in enumerate(countries):
                assert visited[i] == country
        
        # Add more countries
        more_countries = ["FR", "DE"]
        h5_utils.update_visits(player_id, more_countries, temp_h5_file)
        
        # Verify all countries are there
        with h5py.File(temp_h5_file, "r") as f:
            visited = f[f"/players/{player_id}/visited"][...]
            assert len(visited) == len(countries) + len(more_countries)
            all_countries = countries + more_countries
            for i, country in enumerate(all_countries):
                assert visited[i] == country

    def test_get_players(self, temp_h5_file):
        """Test getting all players from the HDF5 file."""
        # Test with empty file
        players = h5_utils.get_players(temp_h5_file)
        assert players == {}
        
        # Add some players
        h5_utils.add_player("player1", "#FF0000", temp_h5_file)
        h5_utils.add_player("player2", "#00FF00", temp_h5_file)
        
        # Add visits for player1
        h5_utils.update_visits("player1", ["US", "CA"], temp_h5_file)
        
        # Get players
        players = h5_utils.get_players(temp_h5_file)
        
        # Verify players data
        assert len(players) == 2
        assert "player1" in players
        assert "player2" in players
        assert players["player1"]["colour"] == "#FF0000"
        assert players["player2"]["colour"] == "#00FF00"
        assert "US" in players["player1"]["visited"]
        assert "CA" in players["player1"]["visited"]
        assert len(players["player2"]["visited"]) == 0
        
        # Test with non-existent file
        non_existent = os.path.join(os.path.dirname(temp_h5_file), "non_existent.h5")
        players = h5_utils.get_players(non_existent)
        assert players == {}

    def test_get_palettes(self, mock_palettes_json):
        """Test loading color palettes from JSON."""
        palettes = h5_utils.get_palettes(mock_palettes_json)
        
        # Verify palettes data
        assert "Test Palette" in palettes
        assert len(palettes["Test Palette"]) == 3
        assert "#FF0000" in palettes["Test Palette"]
        assert "#00FF00" in palettes["Test Palette"]
        assert "#0000FF" in palettes["Test Palette"]

    def test_clear_player_visits(self, temp_h5_file):
        """Test clearing all visited countries for a player."""
        player_id = "test_player"
        
        # Add a player and some visits
        h5_utils.add_player(player_id, "#FF0000", temp_h5_file)
        h5_utils.update_visits(player_id, ["US", "CA", "MX"], temp_h5_file)
        
        # Verify visits were added
        with h5py.File(temp_h5_file, "r") as f:
            assert len(f[f"/players/{player_id}/visited"][...]) == 3
        
        # Clear visits
        h5_utils.clear_player_visits(player_id, temp_h5_file)
        
        # Verify visits were cleared
        with h5py.File(temp_h5_file, "r") as f:
            assert len(f[f"/players/{player_id}/visited"][...]) == 0
        
        # Test with non-existent player (should not error)
        h5_utils.clear_player_visits("non_existent", temp_h5_file)

    def test_delete_player(self, temp_h5_file):
        """Test deleting a player from the HDF5 file."""
        # Add some players
        h5_utils.add_player("player1", "#FF0000", temp_h5_file)
        h5_utils.add_player("player2", "#00FF00", temp_h5_file)
        
        # Delete player1
        h5_utils.delete_player("player1", temp_h5_file)
        
        # Verify player1 was deleted
        with h5py.File(temp_h5_file, "r") as f:
            assert "/players/player1" not in f
            assert "/players/player2" in f
        
        # Test with non-existent player (should not error)
        h5_utils.delete_player("non_existent", temp_h5_file)