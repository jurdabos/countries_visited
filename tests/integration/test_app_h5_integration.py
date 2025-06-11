import os
import pytest
import sys
import json
import h5py
import tempfile
import shutil

# Add the parent directory to sys.path to import app and h5_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import app
import h5_utils


class TestAppH5Integration:
    """Integration tests for app.py and h5_utils.py interactions."""
    
    def test_player_data_flow(self, temp_dir):
        """Test the flow of player data between app and h5_utils."""
        # Create a test H5 file
        h5_path = os.path.join(temp_dir, "test_integration.h5")
        h5_utils.init_h5(h5_path)
        
        # Add players using h5_utils
        h5_utils.add_player("player1", "#FF0000", h5_path)
        h5_utils.add_player("player2", "#00FF00", h5_path)
        
        # Add visits
        h5_utils.update_visits("player1", ["US", "CA"], h5_path)
        h5_utils.update_visits("player2", ["MX", "FR"], h5_path)
        
        # Get players using h5_utils
        players = h5_utils.get_players(h5_path)
        
        # Verify players data
        assert len(players) == 2
        assert "player1" in players
        assert "player2" in players
        assert players["player1"]["colour"] == "#FF0000"
        assert players["player2"]["colour"] == "#00FF00"
        assert "US" in players["player1"]["visited"]
        assert "CA" in players["player1"]["visited"]
        assert "MX" in players["player2"]["visited"]
        assert "FR" in players["player2"]["visited"]
        
        # Create a mock GeoJSON for the map
        json_dir = os.path.join(temp_dir, "JSON")
        os.makedirs(json_dir, exist_ok=True)
        
        geojson_path = os.path.join(json_dir, "countries.geojson")
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "ISO_A2": "US",
                        "NAME": "United States"
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                    }
                },
                {
                    "type": "Feature",
                    "properties": {
                        "ISO_A2": "CA",
                        "NAME": "Canada"
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[2, 0], [3, 0], [3, 1], [2, 1], [2, 0]]]
                    }
                },
                {
                    "type": "Feature",
                    "properties": {
                        "ISO_A2": "MX",
                        "NAME": "Mexico"
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[4, 0], [5, 0], [5, 1], [4, 1], [4, 0]]]
                    }
                },
                {
                    "type": "Feature",
                    "properties": {
                        "ISO_A2": "FR",
                        "NAME": "France"
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[6, 0], [7, 0], [7, 1], [6, 1], [6, 0]]]
                    }
                }
            ]
        }
        
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f)
        
        # Use app.build_map with the players data from h5_utils
        # We need to temporarily change the working directory to make the relative paths work
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Load country data using app function
            geo_data, countries = app.load_country_data()
            
            # Verify country data
            assert len(countries) == 4
            assert countries["US"] == "United States"
            assert countries["CA"] == "Canada"
            assert countries["MX"] == "Mexico"
            assert countries["FR"] == "France"
            
            # Build map using app function with h5_utils data
            m = app.build_map(players, geo_data)
            
            # Verify map was created
            assert m is not None
            
            # Clear player visits using h5_utils
            h5_utils.clear_player_visits("player1", h5_path)
            
            # Get updated players
            updated_players = h5_utils.get_players(h5_path)
            
            # Verify player1's visits were cleared
            assert len(updated_players["player1"]["visited"]) == 0
            assert len(updated_players["player2"]["visited"]) == 2
        finally:
            # Restore original directory
            os.chdir(original_dir)
    
    def test_palette_integration(self, temp_dir):
        """Test the integration of palette handling between app and h5_utils."""
        # Create JSON directory
        json_dir = os.path.join(temp_dir, "JSON")
        os.makedirs(json_dir, exist_ok=True)
        
        # Create a mock palettes.json
        json_path = os.path.join(json_dir, "palettes.json")
        palette_data = {
            "palettes": [
                {
                    "paletteName": "Test Palette 1",
                    "colors": [
                        {"hex": "FF0000"},
                        {"hex": "00FF00"},
                        {"hex": "0000FF"}
                    ]
                },
                {
                    "paletteName": "Test Palette 2",
                    "colors": [
                        {"hex": "FFFF00"},
                        {"hex": "00FFFF"},
                        {"hex": "FF00FF"}
                    ]
                }
            ]
        }
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(palette_data, f)
        
        # Create H5 file
        h5_path = os.path.join(temp_dir, "test_palette.h5")
        
        # Change to temp directory to make relative paths work
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Get palettes using h5_utils
            palettes = h5_utils.get_palettes(json_path)
            
            # Verify palettes
            assert len(palettes) == 2
            assert "Test Palette 1" in palettes
            assert "Test Palette 2" in palettes
            assert len(palettes["Test Palette 1"]) == 3
            assert len(palettes["Test Palette 2"]) == 3
            
            # Initialize H5 with palette from h5_utils
            h5_utils.init_h5(h5_path, palettes["Test Palette 1"])
            
            # Verify palette was saved in H5
            with h5py.File(h5_path, "r") as f:
                assert "/palettes/hex_codes" in f
                saved_palette = f["/palettes/hex_codes"][...]
                assert len(saved_palette) == 3
                
            # Load palettes using app function
            app_palettes = app.load_palettes()
            
            # Verify app palettes match h5_utils palettes
            assert len(app_palettes) == len(palettes)
            for name in palettes:
                assert name in app_palettes
                assert app_palettes[name] == palettes[name]
        finally:
            # Restore original directory
            os.chdir(original_dir)