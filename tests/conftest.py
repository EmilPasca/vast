"""
Pytest configuration and shared fixtures for VAST tests
"""
import sys
import os
import pytest
from datetime import datetime
from typing import Dict, Any

# Add project directories to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'data-server'))
sys.path.insert(0, os.path.join(project_root, 'iot-gateway'))
sys.path.insert(0, os.path.join(project_root, 'dataset-tools'))


# ============================================================================
# Core Fixtures for Data Server Components
# ============================================================================

@pytest.fixture
def sample_sensor_config() -> Dict[str, Any]:
    """Sample sensor configuration for testing"""
    return {
        "type": "temperature",
        "location": "greenhouse-north",
        "environment": "greenhouse",
        "crop_type": "tomato",
        "soil_type": "loam",
        "base_temp": 25.0,
        "variation": 0.8,
        "active": True,
        "metadata": {
            "is_dummy": True,
            "source": "test_fixture",
            "created_at": datetime.now().isoformat()
        }
    }


@pytest.fixture
def sample_sensor_ids():
    """Common sensor IDs for testing"""
    return ["TEMP001", "TEMP002", "TEMP003", "TEMP004", "HUM001", "SOIL001", "LIGHT001"]


@pytest.fixture
def mock_sensor_reading():
    """Mock sensor reading data"""
    from models.models import SensorReading
    return SensorReading(
        value=25.5,
        unit="celsius",
        timestamp=1234567890.0
    )


@pytest.fixture
def mock_sensor_context():
    """Mock sensor context data"""
    from models.models import SensorContext
    return SensorContext(
        environment="greenhouse",
        crop_type="tomato",
        growth_stage="flowering",
        planting_zone="8b",
        season="summer",
        expected_range={"min": 20.0, "max": 28.0},
        critical_threshold={"min": 15.0, "max": 35.0},
        field_section="north",
        soil_type="loam"
    )


@pytest.fixture
def mock_enriched_reading(mock_sensor_reading, mock_sensor_context):
    """Mock enriched reading"""
    from models.models import EnrichedReading, SensorMetadata

    metadata = SensorMetadata(
        sensor_id="TEMP001",
        location={"lat": 40.7128, "lng": -74.0060, "name": "greenhouse-north"},
        manufacturer="TestCorp",
        model="TC-100"
    )

    return EnrichedReading(
        reading=mock_sensor_reading,
        context=mock_sensor_context,
        metadata=metadata
    )


# ============================================================================
# Component Fixtures
# ============================================================================

@pytest.fixture
def data_storage():
    """Create a fresh DataStorage instance"""
    from data_storage import DataStorage
    return DataStorage(max_size=100)


@pytest.fixture
def sensor_registry():
    """Create a fresh SensorRegistry instance without config file"""
    from sensor_registry import SensorRegistry
    return SensorRegistry(config_file=None)


@pytest.fixture
def data_generator(sensor_registry):
    """Create a DataGenerator instance with sensor registry"""
    from data_generator import DataGenerator
    return DataGenerator(sensor_registry=sensor_registry)


@pytest.fixture
def vulnerability_manager():
    """Create a VulnerabilityManager instance"""
    from vulnerability_manager import VulnerabilityManager
    return VulnerabilityManager()


@pytest.fixture
def weather_event_manager():
    """Create a WeatherEventManager instance"""
    from weather_event_manager import WeatherEventManager
    return WeatherEventManager()


@pytest.fixture
def data_formatter():
    """Create a DataFormatter instance"""
    from data_formatter import DataFormatter
    return DataFormatter()


# ============================================================================
# API Testing Fixtures
# ============================================================================

@pytest.fixture
def test_api_key():
    """Standard API key for testing"""
    return "INSECURE_API_KEY"


@pytest.fixture
def test_headers(test_api_key):
    """Standard headers for API requests"""
    return {
        "X-API-Key": test_api_key,
        "Content-Type": "application/json"
    }


# ============================================================================
# Time Manipulation Fixtures
# ============================================================================

@pytest.fixture
def freeze_time():
    """Freeze time for testing time-dependent functionality"""
    from freezegun import freeze_time
    return freeze_time


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration between tests"""
    import logging
    # Clear all handlers
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.setLevel(logging.NOTSET)
    yield
    # Cleanup after test
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(logger_name)
        logger.handlers = []


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_sensor_readings(count: int = 10, sensor_id: str = "TEMP001"):
    """Generate multiple mock sensor readings for testing"""
    from models.models import SensorReading
    import time

    readings = []
    base_time = time.time()
    for i in range(count):
        reading = SensorReading(
            value=20.0 + i * 0.5,
            unit="celsius",
            timestamp=base_time + i * 60
        )
        readings.append(reading)
    return readings


# ============================================================================
# Parametrization Helpers
# ============================================================================

# Common sensor types for parametrized tests
SENSOR_TYPES = ["temperature", "humidity", "soil_moisture", "light"]

# Common crop types
CROP_TYPES = ["tomato", "cucumber", "corn", "wheat", "generic"]

# Weather event types
WEATHER_EVENTS = ["heatwave", "coldfront", "rainstorm", "drought", "frost"]

# Vulnerability types
DATA_VULNERABILITIES = ["offset", "random_noise", "inversion", "freeze", "missing_data", "extreme_values"]
REQUEST_VULNERABILITIES = ["delay", "data_leak", "error_500", "corruption"]
