import os
import pytest
import tempfile
import h5py
import json
import shutil
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_h5_file(temp_dir):
    """Create a temporary HDF5 file for testing."""
    h5_path = os.path.join(temp_dir, "test_countries.h5")
    with h5py.File(h5_path, "w") as f:
        # Create basic structure
        f.create_group("/players")
    yield h5_path
    # File will be cleaned up when temp_dir is removed

@pytest.fixture
def sample_palette():
    """Return a sample color palette for testing."""
    return ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#00FFFF"]

@pytest.fixture
def mock_palettes_json(temp_dir):
    """Create a mock palettes.json file for testing."""
    json_dir = os.path.join(temp_dir, "JSON")
    os.makedirs(json_dir, exist_ok=True)
    
    json_path = os.path.join(json_dir, "palettes.json")
    palette_data = {
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
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(palette_data, f)
    
    yield json_path

@pytest.fixture
def mock_countries_geojson(temp_dir):
    """Create a mock countries.geojson file with minimal data for testing."""
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
            }
        ]
    }
    
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f)
    
    yield geojson_path