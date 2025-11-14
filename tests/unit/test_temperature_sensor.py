"""
Unit tests for Temperature Sensor (sensors/temp/app.py)

Tests the core logic of the temperature sensor including:
- Temperature reading with fault modes
- Data formatting (JSON, CSV, binary, minimal)
- Sensor calibration
- Fault simulation (stuck, drift, spike, dropout)

Note: These tests focus on the core sensor logic without requiring
Flask/MQTT infrastructure by extracting and testing the classes directly.
"""
import pytest
import json
import time
import struct
import random
from unittest.mock import Mock, MagicMock


# ============================================================================
# Extract Core Classes (Simulating Sensor Logic Without Full App)
# ============================================================================

class TemperatureSensor:
    """Simplified TemperatureSensor for testing (based on sensors/temp/app.py)"""

    def __init__(self):
        self.base_temperature = 25.0
        self.running = True
        self.fault_mode = "none"
        self.last_reading = None
        self.drift_offset = 0.0
        self.calibration_offset = 0.0
        self.data_client = Mock()
        self.data_client.fetch_temperature = Mock(return_value=25.0)

    def read(self):
        """Read temperature with fault simulation"""
        # Dropout mode
        if self.fault_mode == "dropout":
            return None

        # Get base temperature
        base_temperature = self.data_client.fetch_temperature()

        # Stuck mode
        if self.fault_mode == "stuck":
            if self.last_reading is None:
                reading = round(self.base_temperature + random.uniform(-0.5, 0.5), 2)
                self.last_reading = reading
            return self.last_reading + self.calibration_offset

        # Drift mode
        if self.fault_mode == "drift":
            self.drift_offset += 0.1
            reading = round(self.base_temperature + self.drift_offset + random.uniform(-0.5, 0.5), 2)
            self.last_reading = reading
            return reading + self.calibration_offset

        # Spike mode
        if self.fault_mode == "spike":
            normal_reading = self.base_temperature + random.uniform(-0.5, 0.5)
            if random.random() < 0.5:
                spike_value = normal_reading * 10
                self.last_reading = round(spike_value, 2)
                return self.last_reading + self.calibration_offset
            else:
                self.last_reading = round(normal_reading, 2)
                return self.last_reading + self.calibration_offset

        # Normal mode
        reading = round(base_temperature + random.uniform(-0.5, 0.5), 2)
        self.last_reading = reading
        return reading + self.calibration_offset


class DataFormatter:
    """Data formatter for sensor readings (based on sensors/temp/app.py)"""

    SENSOR_ID = "TEMP001"

    @staticmethod
    def format_rich_json(sensor_data):
        """Full metadata-rich JSON format"""
        return {
            "temperature": sensor_data.value,
            "unit": "celsius",
            "timestamp": time.time(),
            "sensor_id": DataFormatter.SENSOR_ID
        }

    @staticmethod
    def format_minimal(sensor_data):
        """Just the raw value as string"""
        return str(sensor_data.value)

    @staticmethod
    def format_csv(sensor_data):
        """Simple CSV format"""
        return f"{DataFormatter.SENSOR_ID},{sensor_data.value},{int(time.time())}"

    @staticmethod
    def format_binary(sensor_data):
        """Binary format"""
        import struct
        sensor_id_int = int(DataFormatter.SENSOR_ID.replace('TEMP', ''))
        return struct.pack(">Hfi", sensor_id_int, sensor_data.value, int(time.time()))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_sensor():
    """Create a fresh TemperatureSensor instance"""
    return TemperatureSensor()


@pytest.fixture
def data_formatter():
    """Create DataFormatter instance"""
    return DataFormatter()


@pytest.fixture
def mock_sensor_data():
    """Create mock sensor data object"""
    return type('SensorData', (), {'value': 25.5})


# ============================================================================
# TemperatureSensor Tests
# ============================================================================

class TestTemperatureSensorInitialization:
    """Test TemperatureSensor initialization"""

    def test_initialization_defaults(self, temp_sensor):
        """Should initialize with correct default values"""
        assert temp_sensor.base_temperature == 25.0
        assert temp_sensor.running == True
        assert temp_sensor.fault_mode == "none"
        assert temp_sensor.last_reading is None
        assert temp_sensor.drift_offset == 0.0
        assert temp_sensor.calibration_offset == 0.0


class TestTemperatureSensorReadNormal:
    """Test normal temperature reading (no faults)"""

    def test_read_normal_returns_value(self, temp_sensor):
        """Should return a temperature value in normal mode"""
        temp = temp_sensor.read()
        assert temp is not None
        assert isinstance(temp, float)

    def test_read_normal_within_expected_range(self, temp_sensor):
        """Normal readings should be close to base temperature"""
        temp = temp_sensor.read()
        # Base is 25.0, random is ±0.5, so should be 24.5-25.5
        assert 24.0 <= temp <= 26.0

    def test_read_normal_updates_last_reading(self, temp_sensor):
        """Should update last_reading on each read"""
        temp = temp_sensor.read()
        assert temp_sensor.last_reading is not None

    def test_read_normal_multiple_readings_vary(self, temp_sensor):
        """Multiple readings should vary slightly"""
        readings = [temp_sensor.read() for _ in range(10)]
        # Should have some variation
        assert len(set(readings)) > 1


class TestTemperatureSensorFaultStuck:
    """Test stuck sensor fault mode"""

    def test_stuck_mode_returns_same_value(self, temp_sensor):
        """Stuck mode should return the same value repeatedly"""
        temp_sensor.fault_mode = "stuck"

        reading1 = temp_sensor.read()
        reading2 = temp_sensor.read()
        reading3 = temp_sensor.read()

        assert reading1 == reading2 == reading3

    def test_stuck_mode_sets_last_reading(self, temp_sensor):
        """Stuck mode should set last_reading on first read"""
        temp_sensor.fault_mode = "stuck"

        assert temp_sensor.last_reading is None
        temp_sensor.read()
        assert temp_sensor.last_reading is not None

    def test_stuck_mode_applies_calibration(self, temp_sensor):
        """Stuck mode should apply calibration offset"""
        temp_sensor.fault_mode = "stuck"
        temp_sensor.calibration_offset = 2.0

        reading_without_cal = temp_sensor.read()
        expected_with_cal = temp_sensor.last_reading + 2.0

        # Read again (should be same stuck value + calibration)
        reading_with_cal = temp_sensor.read()
        assert abs(reading_with_cal - expected_with_cal) < 0.01


class TestTemperatureSensorFaultDrift:
    """Test drift sensor fault mode"""

    def test_drift_mode_increases_over_time(self, temp_sensor):
        """Drift mode should show gradual increase"""
        temp_sensor.fault_mode = "drift"

        readings = [temp_sensor.read() for _ in range(10)]

        # The drift offset increases by 0.1 each time, so after 10 readings it's +1.0
        # With random variation of ±0.5, the last reading should still be notably higher
        # Check that the overall trend is upward (last > first with tolerance for random)
        assert readings[-1] > readings[0] + 0.5  # Should have drifted at least 0.5 degrees up

    def test_drift_mode_updates_drift_offset(self, temp_sensor):
        """Drift mode should increase drift_offset"""
        temp_sensor.fault_mode = "drift"

        assert temp_sensor.drift_offset == 0.0
        temp_sensor.read()
        assert temp_sensor.drift_offset == 0.1
        temp_sensor.read()
        assert temp_sensor.drift_offset == 0.2

    def test_drift_mode_applies_calibration(self, temp_sensor):
        """Drift mode should apply calibration offset"""
        temp_sensor.fault_mode = "drift"
        temp_sensor.calibration_offset = 1.5

        reading = temp_sensor.read()
        # Reading should include calibration offset
        assert reading is not None


class TestTemperatureSensorFaultSpike:
    """Test spike sensor fault mode"""

    def test_spike_mode_produces_varied_readings(self, temp_sensor):
        """Spike mode should produce both normal and extreme values"""
        temp_sensor.fault_mode = "spike"

        readings = [temp_sensor.read() for _ in range(20)]

        # Should have some variation (spikes and normal readings)
        assert len(set(readings)) > 1

        # Should have at least one very high value (spike)
        max_reading = max(readings)
        assert max_reading > 100  # Spike multiplier is 10x

    def test_spike_mode_applies_calibration(self, temp_sensor):
        """Spike mode should apply calibration offset"""
        temp_sensor.fault_mode = "spike"
        temp_sensor.calibration_offset = 3.0

        reading = temp_sensor.read()
        assert reading is not None


class TestTemperatureSensorFaultDropout:
    """Test dropout sensor fault mode"""

    def test_dropout_mode_returns_none(self, temp_sensor):
        """Dropout mode should return None"""
        temp_sensor.fault_mode = "dropout"

        reading = temp_sensor.read()
        assert reading is None

    def test_dropout_mode_consistent(self, temp_sensor):
        """Dropout mode should consistently return None"""
        temp_sensor.fault_mode = "dropout"

        for _ in range(10):
            assert temp_sensor.read() is None


class TestTemperatureSensorCalibration:
    """Test sensor calibration offset"""

    def test_calibration_offset_applied(self, temp_sensor):
        """Calibration offset should be applied to readings"""
        temp_sensor.calibration_offset = 5.0

        # Read without calibration first
        temp_sensor.calibration_offset = 0.0
        reading_without = temp_sensor.read()

        # Apply calibration
        temp_sensor.calibration_offset = 5.0
        temp_sensor.last_reading = None  # Reset to get new reading
        reading_with = temp_sensor.read()

        # Difference should be approximately the calibration offset
        # (accounting for random variation)
        assert abs((reading_with - reading_without) - 5.0) < 1.0

    def test_negative_calibration_offset(self, temp_sensor):
        """Should handle negative calibration offsets"""
        temp_sensor.calibration_offset = -3.0
        reading = temp_sensor.read()

        assert reading is not None

    def test_zero_calibration_offset(self, temp_sensor):
        """Zero calibration should not affect readings"""
        temp_sensor.calibration_offset = 0.0
        reading = temp_sensor.read()

        assert reading is not None


class TestTemperatureSensorFaultModeChanges:
    """Test changing fault modes"""

    def test_change_from_normal_to_stuck(self, temp_sensor):
        """Should be able to change from normal to stuck mode"""
        # Normal mode
        assert temp_sensor.fault_mode == "none"
        normal_reading = temp_sensor.read()

        # Switch to stuck
        temp_sensor.fault_mode = "stuck"
        temp_sensor.last_reading = None  # Reset

        stuck_reading1 = temp_sensor.read()
        stuck_reading2 = temp_sensor.read()

        assert stuck_reading1 == stuck_reading2

    def test_reset_state_when_changing_modes(self, temp_sensor):
        """Should reset state when changing fault modes"""
        # Drift mode to build up offset
        temp_sensor.fault_mode = "drift"
        for _ in range(5):
            temp_sensor.read()

        drift_offset = temp_sensor.drift_offset
        assert drift_offset > 0

        # Manually reset (as the endpoint does)
        temp_sensor.fault_mode = "none"
        temp_sensor.last_reading = None
        temp_sensor.drift_offset = 0.0

        assert temp_sensor.drift_offset == 0.0


# ============================================================================
# DataFormatter Tests
# ============================================================================

class TestDataFormatterRichJSON:
    """Test rich JSON formatting"""

    def test_format_rich_json_structure(self, data_formatter, mock_sensor_data):
        """Rich JSON should have correct structure"""
        result = data_formatter.format_rich_json(mock_sensor_data)

        assert isinstance(result, dict)
        assert "temperature" in result
        assert "unit" in result
        assert "timestamp" in result
        assert "sensor_id" in result

    def test_format_rich_json_temperature_value(self, data_formatter, mock_sensor_data):
        """Should include correct temperature value"""
        result = data_formatter.format_rich_json(mock_sensor_data)

        assert result["temperature"] == 25.5

    def test_format_rich_json_unit(self, data_formatter, mock_sensor_data):
        """Should use celsius as unit"""
        result = data_formatter.format_rich_json(mock_sensor_data)

        assert result["unit"] == "celsius"

    def test_format_rich_json_timestamp(self, data_formatter, mock_sensor_data):
        """Should include current timestamp"""
        before = time.time()
        result = data_formatter.format_rich_json(mock_sensor_data)
        after = time.time()

        assert before <= result["timestamp"] <= after


class TestDataFormatterMinimal:
    """Test minimal formatting"""

    def test_format_minimal_returns_string(self, data_formatter, mock_sensor_data):
        """Minimal format should return string"""
        result = data_formatter.format_minimal(mock_sensor_data)

        assert isinstance(result, str)

    def test_format_minimal_contains_value(self, data_formatter, mock_sensor_data):
        """Minimal format should contain the temperature value"""
        result = data_formatter.format_minimal(mock_sensor_data)

        assert "25.5" in result

    def test_format_minimal_parseable(self, data_formatter, mock_sensor_data):
        """Minimal format output should be parseable as float"""
        result = data_formatter.format_minimal(mock_sensor_data)

        value = float(result)
        assert value == 25.5


class TestDataFormatterCSV:
    """Test CSV formatting"""

    def test_format_csv_returns_string(self, data_formatter, mock_sensor_data):
        """CSV format should return string"""
        result = data_formatter.format_csv(mock_sensor_data)

        assert isinstance(result, str)

    def test_format_csv_structure(self, data_formatter, mock_sensor_data):
        """CSV should have correct structure: sensor_id,value,timestamp"""
        result = data_formatter.format_csv(mock_sensor_data)

        parts = result.split(',')
        assert len(parts) == 3

    def test_format_csv_sensor_id(self, data_formatter, mock_sensor_data):
        """CSV should include sensor ID as first field"""
        result = data_formatter.format_csv(mock_sensor_data)

        parts = result.split(',')
        assert parts[0].startswith("TEMP")

    def test_format_csv_temperature_value(self, data_formatter, mock_sensor_data):
        """CSV should include temperature as second field"""
        result = data_formatter.format_csv(mock_sensor_data)

        parts = result.split(',')
        assert float(parts[1]) == 25.5

    def test_format_csv_timestamp(self, data_formatter, mock_sensor_data):
        """CSV should include timestamp as third field"""
        result = data_formatter.format_csv(mock_sensor_data)

        parts = result.split(',')
        timestamp = int(parts[2])
        assert timestamp > 0


class TestDataFormatterBinary:
    """Test binary formatting"""

    def test_format_binary_returns_bytes(self, data_formatter, mock_sensor_data):
        """Binary format should return bytes"""
        result = data_formatter.format_binary(mock_sensor_data)

        assert isinstance(result, bytes)

    def test_format_binary_correct_length(self, data_formatter, mock_sensor_data):
        """Binary format should be 10 bytes (2+4+4)"""
        result = data_formatter.format_binary(mock_sensor_data)

        # 2 bytes for sensor ID + 4 bytes for float + 4 bytes for timestamp
        assert len(result) == 10

    def test_format_binary_parseable(self, data_formatter, mock_sensor_data):
        """Binary format should be parseable back to values"""
        result = data_formatter.format_binary(mock_sensor_data)

        # Unpack: >Hfi = big-endian unsigned short, float, int
        sensor_id_int, temperature, timestamp = struct.unpack(">Hfi", result)

        assert temperature == pytest.approx(25.5, abs=0.01)
        assert timestamp > 0

    def test_format_binary_sensor_id_extraction(self, data_formatter, mock_sensor_data):
        """Should be able to extract sensor ID from binary"""
        result = data_formatter.format_binary(mock_sensor_data)

        sensor_id_int, _, _ = struct.unpack(">Hfi", result)
        assert sensor_id_int == 1  # TEMP001 -> 1


class TestDataFormatterMultipleFormats:
    """Test using different formats together"""

    def test_all_formats_produce_output(self, data_formatter, mock_sensor_data):
        """All format methods should produce output"""
        rich_json = data_formatter.format_rich_json(mock_sensor_data)
        minimal = data_formatter.format_minimal(mock_sensor_data)
        csv = data_formatter.format_csv(mock_sensor_data)
        binary = data_formatter.format_binary(mock_sensor_data)

        assert rich_json is not None
        assert minimal is not None
        assert csv is not None
        assert binary is not None

    def test_different_sensor_values(self, data_formatter):
        """Different sensor values should produce different outputs"""
        data1 = type('SensorData', (), {'value': 20.0})
        data2 = type('SensorData', (), {'value': 30.0})

        result1 = data_formatter.format_minimal(data1)
        result2 = data_formatter.format_minimal(data2)

        assert result1 != result2


# ============================================================================
# Integration Tests
# ============================================================================

class TestTemperatureSensorWithDataClient:
    """Test sensor integration with DataServerClient"""

    def test_sensor_uses_data_client_temperature(self, temp_sensor):
        """Sensor should use temperature from data client"""
        # Mock returns 30.0
        temp_sensor.data_client.fetch_temperature.return_value = 30.0

        reading = temp_sensor.read()

        # Should be around 30 ± random variation
        assert 29.0 <= reading <= 31.0


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_extreme_calibration_offset(self, temp_sensor):
        """Should handle very large calibration offsets"""
        temp_sensor.calibration_offset = 100.0
        reading = temp_sensor.read()

        assert reading > 100.0

    def test_negative_temperature_reading(self, temp_sensor):
        """Should handle negative temperatures"""
        temp_sensor.data_client.fetch_temperature.return_value = -10.0
        reading = temp_sensor.read()

        assert reading < 0.0

    def test_all_fault_modes_exist(self, temp_sensor):
        """All documented fault modes should work"""
        fault_modes = ["none", "stuck", "drift", "spike", "dropout"]

        for mode in fault_modes:
            temp_sensor.fault_mode = mode
            temp_sensor.last_reading = None
            temp_sensor.drift_offset = 0.0

            # Should not raise exception
            reading = temp_sensor.read()

            if mode == "dropout":
                assert reading is None
            else:
                assert reading is not None
