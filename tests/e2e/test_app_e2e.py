import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import app
import h5_utils


class TestAppE2E:
    """End-to-end tests for the Countries Visited application."""
    
    @patch('streamlit.session_state')
    @patch('streamlit.sidebar')
    @patch('streamlit.title')
    @patch('streamlit.subheader')
    @patch('streamlit.divider')
    @patch('streamlit.columns')
    @patch('streamlit.button')
    @patch('streamlit.file_uploader')
    @patch('streamlit.download_button')
    @patch('streamlit.success')
    @patch('streamlit.error')
    @patch('streamlit.info')
    @patch('streamlit.radio')
    @patch('streamlit_folium.folium_static')
    def test_single_player_workflow(self, mock_folium_static, mock_radio, mock_info, 
                                   mock_error, mock_success, mock_download_button, 
                                   mock_file_uploader, mock_button, mock_columns, 
                                   mock_divider, mock_subheader, mock_title, 
                                   mock_sidebar, mock_session_state, temp_dir):
        """Test the single player workflow from start to finish."""
        # Setup mock session state
        mock_session_state.logged_in = True
        mock_session_state.user_id = "test_user"
        mock_session_state.current_mode = "single"
        mock_session_state.visited_countries = set()
        
        # Setup mock radio button to return "Single Player"
        mock_radio.return_value = "Single Player"
        
        # Setup mock button to simulate creating a new map
        mock_button.return_value = True
        
        # Setup mock columns
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2]
        
        # Create test environment
        test_h5_file = os.path.join(temp_dir, "countries_visited.h5")
        
        # Create JSON directory with required files
        json_dir = os.path.join(temp_dir, "JSON")
        os.makedirs(json_dir, exist_ok=True)
        
        # Create mock countries.geojson
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
                }
            ]
        }
        
        with open(geojson_path, "w") as f:
            import json
            json.dump(geojson_data, f)
        
        # Create mock palettes.json
        palettes_path = os.path.join(json_dir, "palettes.json")
        palettes_data = {
            "palettes": [
                {
                    "paletteName": "Test Palette",
                    "colors": [
                        {"hex": "FF0000"},
                        {"hex": "00FF00"},
                        {"hex": "0000FF"}
                    ]
                }
            ]
        }
        
        with open(palettes_path, "w") as f:
            json.dump(palettes_data, f)
        
        # Change to temp directory to make relative paths work
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Initialize the app by calling main()
            with patch('app.DEFAULT_H5_FILE', test_h5_file):
                # Simulate adding countries in single player mode
                mock_session_state.visited_countries = {"US", "CA"}
                
                # Run the main function
                app.main()
                
                # Verify the map was created
                mock_folium_static.assert_called()
                
                # Verify the H5 file was created and contains the expected data
                assert os.path.exists(test_h5_file)
                
                # Get players from the H5 file
                players = h5_utils.get_players(test_h5_file)
                
                # Verify the player data
                assert "demo_user" in players
                assert len(players["demo_user"]["visited"]) == 2
                assert "US" in players["demo_user"]["visited"]
                assert "CA" in players["demo_user"]["visited"]
        finally:
            # Restore original directory
            os.chdir(original_dir)
    
    @patch('streamlit.session_state')
    @patch('streamlit.sidebar')
    @patch('streamlit.title')
    @patch('streamlit.subheader')
    @patch('streamlit.divider')
    @patch('streamlit.columns')
    @patch('streamlit.button')
    @patch('streamlit.text_input')
    @patch('streamlit.color_picker')
    @patch('streamlit.selectbox')
    @patch('streamlit.expander')
    @patch('streamlit.checkbox')
    @patch('streamlit.radio')
    @patch('streamlit_folium.folium_static')
    def test_multi_player_workflow(self, mock_folium_static, mock_radio, mock_checkbox,
                                  mock_expander, mock_selectbox, mock_color_picker,
                                  mock_text_input, mock_button, mock_columns,
                                  mock_divider, mock_subheader, mock_title,
                                  mock_sidebar, mock_session_state, temp_dir):
        """Test the multi-player workflow from start to finish."""
        # Setup mock session state
        mock_session_state.logged_in = True
        mock_session_state.user_id = "test_user"
        mock_session_state.current_mode = "multi"
        mock_session_state.visited_countries = set()
        mock_session_state.current_player = "player1"
        
        # Setup mock radio button to return "Multi Player"
        mock_radio.return_value = "Multi Player"
        
        # Setup mock expander
        mock_exp = MagicMock()
        mock_expander.return_value.__enter__.return_value = mock_exp
        
        # Setup mock text input and color picker for adding players
        mock_text_input.return_value = "player2"
        mock_color_picker.return_value = "#00FF00"
        
        # Setup mock selectbox for selecting player
        mock_selectbox.return_value = "player1"
        
        # Setup mock checkbox for selecting countries
        mock_checkbox.return_value = True
        
        # Setup mock columns
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2]
        
        # Create test environment
        test_h5_file = os.path.join(temp_dir, "countries_visited.h5")
        
        # Create JSON directory with required files
        json_dir = os.path.join(temp_dir, "JSON")
        os.makedirs(json_dir, exist_ok=True)
        
        # Create mock countries.geojson
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
                }
            ]
        }
        
        with open(geojson_path, "w") as f:
            import json
            json.dump(geojson_data, f)
        
        # Create mock palettes.json
        palettes_path = os.path.join(json_dir, "palettes.json")
        palettes_data = {
            "palettes": [
                {
                    "paletteName": "Test Palette",
                    "colors": [
                        {"hex": "FF0000"},
                        {"hex": "00FF00"},
                        {"hex": "0000FF"}
                    ]
                }
            ]
        }
        
        with open(palettes_path, "w") as f:
            json.dump(palettes_data, f)
        
        # Initialize the H5 file and add players
        h5_utils.init_h5(test_h5_file)
        h5_utils.add_player("player1", "#FF0000", test_h5_file)
        h5_utils.add_player("player2", "#00FF00", test_h5_file)
        
        # Change to temp directory to make relative paths work
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Run the main function with multi-player mode
            with patch('app.DEFAULT_H5_FILE', test_h5_file):
                # Simulate adding countries for player1
                h5_utils.update_visits("player1", ["US"], test_h5_file)
                
                # Run the main function
                app.main()
                
                # Verify the map was created
                mock_folium_static.assert_called()
                
                # Verify the H5 file contains the expected data
                players = h5_utils.get_players(test_h5_file)
                
                # Verify player data
                assert "player1" in players
                assert "player2" in players
                assert "US" in players["player1"]["visited"]
                assert players["player1"]["colour"] == "#FF0000"
                assert players["player2"]["colour"] == "#00FF00"
        finally:
            # Restore original directory
            os.chdir(original_dir)