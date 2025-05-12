import pytest
from schemas import ProjectDetails, ChatRequest
def test_valid_project_details():
    """Test valid project details"""
    data = {
        "project_type": "kitchen_remodel",
        "property_type": "single_family",
        "city": "San Diego",
        "state": "CA",
        "square_footage": 200
    }
    project = ProjectDetails(**data)
    assert project.city == "San Diego"
def test_invalid_city():
    """Test invalid city validation"""
    data = {
        "project_type": "kitchen_remodel",
        "property_type": "single_family",
        "city": "Phoenix",
        "state": "CA",
        "square_footage": 200
    }
    with pytest.raises(ValueError):
        ProjectDetails(**data)
def test_la_normalization():
    """Test LA to Los Angeles normalization"""
    data = {
        "project_type": "kitchen_remodel",
        "property_type": "single_family",
        "city": "LA",
        "state": "CA",
        "square_footage": 200
    }
    project = ProjectDetails(**data)
    assert project.city == "Los Angeles"