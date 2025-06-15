import os
import pytest
import json
import sys
import folium
import streamlit as st
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import app


class TestAppUtils:
    """Test suite for app.py utility functions."""

    @patch('json.load')
    @patch('builtins.open')
    def test_load_country_data(self, mock_open, mock_json_load, mock_countries_geojson):
        """Test loading country data from GeoJSON."""
        # Mock the JSON data
        mock_json_data = {
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
        mock_json_load.return_value = mock_json_data

        # Call the function
        geo_data, countries = app.load_country_data()

        # Verify results
        assert geo_data == mock_json_data
        assert len(countries) == 2
        assert "US" in countries
        assert "CA" in countries
        assert countries["US"] == "United States"
        assert countries["CA"] == "Canada"

        # Verify open was called with the correct path
        mock_open.assert_called_once()
        args, _ = mock_open.call_args
        assert "JSON/countries.geojson" in args[0]

    @patch('h5_utils.get_palettes')
    def test_load_palettes(self, mock_get_palettes):
        """Test loading color palettes."""
        # Mock the palettes data
        mock_palettes = {
            "Test Palette": ["#FF0000", "#00FF00", "#0000FF"],
            "_color_info": {
                "#FF0000": "Red",
                "#00FF00": "Green",
                "#0000FF": "Blue"
            }
        }
        mock_get_palettes.return_value = mock_palettes

        # Call the function
        palettes = app.load_palettes()

        # Verify results
        assert palettes == mock_palettes
        assert "_color_info" in palettes
        assert palettes["_color_info"]["#FF0000"] == "Red"
        mock_get_palettes.assert_called_once()

    def test_build_map(self, mock_countries_geojson):
        """Test building a Folium map with player data."""
        # Load mock GeoJSON data
        with open(mock_countries_geojson, 'r') as f:
            geo_data = json.load(f)

        # Create mock player data
        players = {
            "player1": {
                "colour": "#FF0000",
                "visited": {"US"}
            },
            "player2": {
                "colour": "#00FF00",
                "visited": {"CA"}
            },
            "player3": {
                "colour": "#0000FF",
                "visited": {"US", "CA"}
            }
        }

        # Call the function
        m = app.build_map(players, geo_data)

        # Verify the map was created
        assert isinstance(m, folium.Map)

        # Check that the GeoJSON layer was added
        assert len(m._children) > 0

        # Find the GeoJSON layer
        geojson_layer = None
        for _, child in m._children.items():
            if isinstance(child, folium.features.GeoJson):
                geojson_layer = child
                break

        assert geojson_layer is not None

    @patch('streamlit.secrets.get')
    def test_setup_oauth(self, mock_secrets_get):
        """Test setting up OAuth configuration."""
        # Mock the secrets
        mock_secrets_get.side_effect = lambda key, default: {
            "OAUTH_CLIENT_ID": "test-client-id",
            "OAUTH_CLIENT_SECRET": "test-client-secret",
            "OAUTH_REDIRECT_URI": "http://test-redirect-uri"
        }.get(key, default)

        # Mock the OAuth2Component class
        with patch('app.OAuth2Component') as mock_oauth2_component:
            mock_oauth2_instance = MagicMock()
            mock_oauth2_component.return_value = mock_oauth2_instance

            # Call the function
            oauth2 = app.setup_oauth()

            # Verify OAuth2Component was created with correct parameters
            mock_oauth2_component.assert_called_once_with(
                "test-client-id",
                "test-client-secret",
                "https://accounts.google.com/o/oauth2/auth",
                "https://oauth2.googleapis.com/token",
                "https://oauth2.googleapis.com/token",
                "https://oauth2.googleapis.com/revoke",
                "http://test-redirect-uri"
            )

            # Verify the function returned the OAuth2Component instance
            assert oauth2 == mock_oauth2_instance
