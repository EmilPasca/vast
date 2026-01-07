"""
Unit tests for DataStorage class

Tests the in-memory storage system for sensor data readings.
"""
import pytest
from data_storage import DataStorage
from models.models import SensorReading, SensorContext, SensorMetadata, EnrichedReading


class TestDataStorageInitialization:
    """Test DataStorage initialization"""

    def test_initialization_with_default_max_size(self):
        """DataStorage should initialize with default max_size"""
        storage = DataStorage()
        assert storage.max_size == 1000
        assert len(storage.readings) == 0

    def test_initialization_with_custom_max_size(self):
        """DataStorage should initialize with custom max_size"""
        storage = DataStorage(max_size=500)
        assert storage.max_size == 500
        assert len(storage.readings) == 0


class TestAddReading:
    """Test adding readings to storage"""

    def test_add_single_reading(self, data_storage, mock_enriched_reading):
        """Should add a single reading to storage"""
        data_storage.add_reading("TEMP001", mock_enriched_reading)

        assert "TEMP001" in data_storage.readings
        assert len(data_storage.readings["TEMP001"]) == 1

    def test_add_multiple_readings_same_sensor(self, data_storage, mock_enriched_reading):
        """Should add multiple readings for the same sensor"""
        for i in range(5):
            data_storage.add_reading("TEMP001", mock_enriched_reading)

        assert len(data_storage.readings["TEMP001"]) == 5

    def test_add_readings_different_sensors(self, data_storage, mock_enriched_reading):
        """Should add readings for different sensors independently"""
        data_storage.add_reading("TEMP001", mock_enriched_reading)
        data_storage.add_reading("TEMP002", mock_enriched_reading)
        data_storage.add_reading("HUM001", mock_enriched_reading)

        assert len(data_storage.readings) == 3
        assert "TEMP001" in data_storage.readings
        assert "TEMP002" in data_storage.readings
        assert "HUM001" in data_storage.readings

    def test_respects_max_size_limit(self, mock_enriched_reading):
        """Should respect max_size limit using deque"""
        storage = DataStorage(max_size=10)

        # Add 15 readings (more than max_size)
        for i in range(15):
            storage.add_reading("TEMP001", mock_enriched_reading)

        # Should only keep the last 10
        assert len(storage.readings["TEMP001"]) == 10


class TestGetLatestReading:
    """Test getting the latest reading"""

    def test_get_latest_reading_empty_storage(self, data_storage):
        """Should return None when no readings exist"""
        result = data_storage.get_latest_reading("TEMP001")
        assert result is None

    def test_get_latest_reading_single_reading(self, data_storage, mock_enriched_reading):
        """Should return the single reading that was added"""
        data_storage.add_reading("TEMP001", mock_enriched_reading)

        result = data_storage.get_latest_reading("TEMP001")
        assert result is not None
        assert result.reading.value == mock_enriched_reading.reading.value

    def test_get_latest_reading_multiple_readings(self, data_storage):
        """Should return the most recent reading"""
        from models.models import SensorReading, SensorContext, SensorMetadata, EnrichedReading

        # Create readings with different values
        for i in range(5):
            reading = SensorReading(value=20.0 + i, unit="celsius", timestamp=1000.0 + i)
            context = SensorContext()
            metadata = SensorMetadata(sensor_id="TEMP001")
            enriched = EnrichedReading(reading=reading, context=context, metadata=metadata)
            data_storage.add_reading("TEMP001", enriched)

        result = data_storage.get_latest_reading("TEMP001")
        assert result.reading.value == 24.0  # Last value added
        assert result.reading.timestamp == 1004.0

    def test_get_latest_reading_nonexistent_sensor(self, data_storage, mock_enriched_reading):
        """Should return None for sensor that doesn't exist"""
        data_storage.add_reading("TEMP001", mock_enriched_reading)

        result = data_storage.get_latest_reading("TEMP999")
        assert result is None


class TestGetSensorHistory:
    """Test getting historical readings"""

    def test_get_history_empty_storage(self, data_storage):
        """Should return empty list when no readings exist"""
        result = data_storage.get_sensor_history("TEMP001")
        assert result == []

    def test_get_history_with_default_limit(self, data_storage):
        """Should return history with default limit of 100"""
        from models.models import SensorReading, SensorContext, SensorMetadata, EnrichedReading

        # Add 10 readings
        for i in range(10):
            reading = SensorReading(value=20.0 + i, unit="celsius")
            context = SensorContext()
            metadata = SensorMetadata(sensor_id="TEMP001")
            enriched = EnrichedReading(reading=reading, context=context, metadata=metadata)
            data_storage.add_reading("TEMP001", enriched)

        result = data_storage.get_sensor_history("TEMP001")
        assert len(result) == 10

    def test_get_history_with_custom_limit(self, data_storage):
        """Should respect custom limit parameter"""
        from models.models import SensorReading, SensorContext, SensorMetadata, EnrichedReading

        # Add 10 readings
        for i in range(10):
            reading = SensorReading(value=20.0 + i, unit="celsius")
            context = SensorContext()
            metadata = SensorMetadata(sensor_id="TEMP001")
            enriched = EnrichedReading(reading=reading, context=context, metadata=metadata)
            data_storage.add_reading("TEMP001", enriched)

        result = data_storage.get_sensor_history("TEMP001", limit=5)
        assert len(result) == 5

    def test_get_history_returns_most_recent_first(self, data_storage):
        """Should return readings in reverse chronological order (most recent first)"""
        from models.models import SensorReading, SensorContext, SensorMetadata, EnrichedReading

        # Add readings with increasing values
        for i in range(5):
            reading = SensorReading(value=20.0 + i, unit="celsius", timestamp=1000.0 + i)
            context = SensorContext()
            metadata = SensorMetadata(sensor_id="TEMP001")
            enriched = EnrichedReading(reading=reading, context=context, metadata=metadata)
            data_storage.add_reading("TEMP001", enriched)

        result = data_storage.get_sensor_history("TEMP001")

        # First item should be the last one added
        assert result[0].reading.value == 24.0
        assert result[0].reading.timestamp == 1004.0

        # Last item should be the first one added
        assert result[-1].reading.value == 20.0
        assert result[-1].reading.timestamp == 1000.0

    def test_get_history_limit_larger_than_available(self, data_storage):
        """Should return all available readings when limit is larger"""
        from models.models import SensorReading, SensorContext, SensorMetadata, EnrichedReading

        # Add 5 readings
        for i in range(5):
            reading = SensorReading(value=20.0 + i, unit="celsius")
            context = SensorContext()
            metadata = SensorMetadata(sensor_id="TEMP001")
            enriched = EnrichedReading(reading=reading, context=context, metadata=metadata)
            data_storage.add_reading("TEMP001", enriched)

        result = data_storage.get_sensor_history("TEMP001", limit=100)
        assert len(result) == 5

    def test_get_history_nonexistent_sensor(self, data_storage):
        """Should return empty list for nonexistent sensor"""
        result = data_storage.get_sensor_history("TEMP999")
        assert result == []


class TestGetAllSensorIds:
    """Test getting all sensor IDs"""

    def test_get_all_sensor_ids_empty_storage(self, data_storage):
        """Should return empty list when no sensors"""
        result = data_storage.get_all_sensor_ids()
        assert result == []

    def test_get_all_sensor_ids_single_sensor(self, data_storage, mock_enriched_reading):
        """Should return list with single sensor ID"""
        data_storage.add_reading("TEMP001", mock_enriched_reading)

        result = data_storage.get_all_sensor_ids()
        assert len(result) == 1
        assert "TEMP001" in result

    def test_get_all_sensor_ids_multiple_sensors(self, data_storage, mock_enriched_reading):
        """Should return all unique sensor IDs"""
        data_storage.add_reading("TEMP001", mock_enriched_reading)
        data_storage.add_reading("TEMP002", mock_enriched_reading)
        data_storage.add_reading("HUM001", mock_enriched_reading)
        data_storage.add_reading("TEMP001", mock_enriched_reading)  # Duplicate

        result = data_storage.get_all_sensor_ids()
        assert len(result) == 3
        assert "TEMP001" in result
        assert "TEMP002" in result
        assert "HUM001" in result


class TestClearSensorData:
    """Test clearing data for a specific sensor"""

    def test_clear_sensor_data_existing_sensor(self, data_storage, mock_enriched_reading):
        """Should clear all readings for specified sensor"""
        # Add readings for multiple sensors
        data_storage.add_reading("TEMP001", mock_enriched_reading)
        data_storage.add_reading("TEMP001", mock_enriched_reading)
        data_storage.add_reading("TEMP002", mock_enriched_reading)

        # Clear TEMP001
        data_storage.clear_sensor_data("TEMP001")

        # TEMP001 should be empty
        assert len(data_storage.readings["TEMP001"]) == 0

        # TEMP002 should still have data
        assert len(data_storage.readings["TEMP002"]) == 1

    def test_clear_sensor_data_nonexistent_sensor(self, data_storage):
        """Should handle clearing nonexistent sensor gracefully"""
        # Should not raise an exception
        data_storage.clear_sensor_data("TEMP999")


class TestClearAll:
    """Test clearing all sensor data"""

    def test_clear_all_empty_storage(self, data_storage):
        """Should handle clearing empty storage"""
        data_storage.clear_all()
        assert len(data_storage.readings) == 0

    def test_clear_all_with_data(self, data_storage, mock_enriched_reading):
        """Should clear all sensor readings"""
        # Add readings for multiple sensors
        data_storage.add_reading("TEMP001", mock_enriched_reading)
        data_storage.add_reading("TEMP002", mock_enriched_reading)
        data_storage.add_reading("HUM001", mock_enriched_reading)

        # Verify data exists
        assert len(data_storage.readings) == 3

        # Clear all
        data_storage.clear_all()

        # Verify all data is cleared
        assert len(data_storage.readings) == 0
        assert data_storage.get_all_sensor_ids() == []


class TestConcurrentAccess:
    """Test handling of concurrent-like access patterns"""

    def test_interleaved_reads_and_writes(self, data_storage):
        """Should handle interleaved reads and writes correctly"""
        from models.models import SensorReading, SensorContext, SensorMetadata, EnrichedReading

        for i in range(10):
            # Add reading
            reading = SensorReading(value=20.0 + i, unit="celsius")
            context = SensorContext()
            metadata = SensorMetadata(sensor_id="TEMP001")
            enriched = EnrichedReading(reading=reading, context=context, metadata=metadata)
            data_storage.add_reading("TEMP001", enriched)

            # Read latest
            latest = data_storage.get_latest_reading("TEMP001")
            assert latest.reading.value == 20.0 + i

            # Read history
            history = data_storage.get_sensor_history("TEMP001", limit=100)
            assert len(history) == i + 1
