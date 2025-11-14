"""
Unit tests for WeatherEventManager class

Tests the weather event simulation system that affects sensor readings.
"""
import pytest
import time
from weather_event_manager import WeatherEventManager


class TestWeatherEventManagerInitialization:
    """Test WeatherEventManager initialization"""

    def test_initialization(self, weather_event_manager):
        """Should initialize with no active events"""
        assert len(weather_event_manager.active_events) == 0

    def test_available_events(self, weather_event_manager):
        """Should have correct set of available weather events"""
        expected_events = ["heatwave", "coldfront", "rainstorm", "drought", "frost"]
        assert list(weather_event_manager.available_events.keys()) == expected_events

    def test_heatwave_effects_defined(self, weather_event_manager):
        """Heatwave should have proper effect definitions"""
        heatwave = weather_event_manager.available_events["heatwave"]

        assert "description" in heatwave
        assert "temperature_effect" in heatwave
        assert "humidity_effect" in heatwave
        assert "soil_moisture_effect" in heatwave

        # Temperature should increase
        assert heatwave["temperature_effect"][0] > 0

        # Humidity should decrease
        assert heatwave["humidity_effect"][1] < 0


class TestParseDuration:
    """Test duration string parsing"""

    def test_parse_seconds(self, weather_event_manager):
        """Should parse seconds correctly"""
        assert weather_event_manager._parse_duration("30s") == 30
        assert weather_event_manager._parse_duration("1s") == 1
        assert weather_event_manager._parse_duration("120s") == 120

    def test_parse_minutes(self, weather_event_manager):
        """Should parse minutes correctly"""
        assert weather_event_manager._parse_duration("1m") == 60
        assert weather_event_manager._parse_duration("5m") == 300
        assert weather_event_manager._parse_duration("30m") == 1800

    def test_parse_hours(self, weather_event_manager):
        """Should parse hours correctly"""
        assert weather_event_manager._parse_duration("1h") == 3600
        assert weather_event_manager._parse_duration("2h") == 7200
        assert weather_event_manager._parse_duration("24h") == 86400

    def test_parse_days(self, weather_event_manager):
        """Should parse days correctly"""
        assert weather_event_manager._parse_duration("1d") == 86400
        assert weather_event_manager._parse_duration("7d") == 604800

    def test_parse_invalid_format(self, weather_event_manager):
        """Should raise error for invalid format"""
        with pytest.raises(ValueError, match="Invalid duration format"):
            weather_event_manager._parse_duration("invalid")

        with pytest.raises(ValueError, match="Invalid duration format"):
            weather_event_manager._parse_duration("30")  # Missing unit

        with pytest.raises(ValueError, match="Invalid duration format"):
            weather_event_manager._parse_duration("s30")  # Wrong order


class TestAddEvent:
    """Test adding weather events"""

    def test_add_heatwave_event(self, weather_event_manager):
        """Should add a heatwave event"""
        event = weather_event_manager.add_event("heatwave", "30s")

        assert event["event_name"] == "heatwave"
        assert "id" in event
        assert "start_time" in event
        assert "end_time" in event
        assert event["duration_seconds"] == 30

    def test_add_event_with_affected_sensors(self, weather_event_manager):
        """Should add event with specific affected sensors"""
        affected = ["TEMP001", "TEMP002"]
        event = weather_event_manager.add_event("rainstorm", "1m", affected_sensors=affected)

        assert event["affected_sensors"] == affected

    def test_add_event_without_affected_sensors(self, weather_event_manager):
        """Should add event affecting all sensors when None specified"""
        event = weather_event_manager.add_event("coldfront", "5m", affected_sensors=None)

        assert event["affected_sensors"] is None

    def test_add_event_calculates_end_time(self, weather_event_manager):
        """Should calculate end time correctly"""
        start_before = time.time()
        event = weather_event_manager.add_event("drought", "10s")
        start_after = time.time()

        # Event start time should be close to current time
        assert start_before <= event["start_time"] <= start_after

        # End time should be start time + duration
        expected_end = event["start_time"] + 10
        assert abs(event["end_time"] - expected_end) < 0.1

    def test_add_unknown_event(self, weather_event_manager):
        """Should raise error for unknown event type"""
        with pytest.raises(ValueError, match="Unknown weather event"):
            weather_event_manager.add_event("earthquake", "30s")

    def test_event_stored_in_active_events(self, weather_event_manager):
        """Should store event in active events dictionary"""
        event = weather_event_manager.add_event("frost", "15s")

        assert event["id"] in weather_event_manager.active_events
        assert weather_event_manager.active_events[event["id"]] == event

    @pytest.mark.parametrize("event_name", [
        "heatwave", "coldfront", "rainstorm", "drought", "frost"
    ])
    def test_add_all_event_types(self, weather_event_manager, event_name):
        """Should be able to add all available event types"""
        event = weather_event_manager.add_event(event_name, "30s")
        assert event["event_name"] == event_name


class TestGetActiveEvents:
    """Test getting active events"""

    def test_get_active_events_empty(self, weather_event_manager):
        """Should return empty list when no active events"""
        events = weather_event_manager.get_active_events()
        assert events == []

    def test_get_active_events_with_one_event(self, weather_event_manager):
        """Should return list with one event"""
        added_event = weather_event_manager.add_event("heatwave", "1h")

        events = weather_event_manager.get_active_events()

        assert len(events) == 1
        assert events[0]["id"] == added_event["id"]

    def test_get_active_events_with_multiple_events(self, weather_event_manager):
        """Should return all active events"""
        event1 = weather_event_manager.add_event("heatwave", "1h")
        event2 = weather_event_manager.add_event("drought", "2h")

        events = weather_event_manager.get_active_events()

        assert len(events) == 2
        event_ids = {e["id"] for e in events}
        assert event1["id"] in event_ids
        assert event2["id"] in event_ids

    def test_get_active_events_excludes_expired(self, weather_event_manager):
        """Should not return expired events"""
        # Add event that expires very soon
        weather_event_manager.add_event("frost", "1s")

        # Wait for it to expire
        time.sleep(1.5)

        # Should be cleaned up
        events = weather_event_manager.get_active_events()
        assert len(events) == 0


class TestGetEventsForSensor:
    """Test getting events for a specific sensor"""

    def test_get_events_for_sensor_none_active(self, weather_event_manager):
        """Should return empty list when no events"""
        events = weather_event_manager.get_events_for_sensor("TEMP001")
        assert events == []

    def test_get_events_for_sensor_global_event(self, weather_event_manager):
        """Should return global events (affecting all sensors)"""
        event = weather_event_manager.add_event("heatwave", "1h", affected_sensors=None)

        events = weather_event_manager.get_events_for_sensor("TEMP001")

        assert len(events) == 1
        assert events[0]["id"] == event["id"]

    def test_get_events_for_specific_sensor(self, weather_event_manager):
        """Should return events affecting specific sensor"""
        event = weather_event_manager.add_event("rainstorm", "1h",
                                                affected_sensors=["TEMP001", "TEMP002"])

        # TEMP001 should get the event
        events = weather_event_manager.get_events_for_sensor("TEMP001")
        assert len(events) == 1

        # TEMP003 should not
        events = weather_event_manager.get_events_for_sensor("TEMP003")
        assert len(events) == 0

    def test_get_events_for_sensor_multiple_events(self, weather_event_manager):
        """Should return all applicable events for a sensor"""
        # Global event
        event1 = weather_event_manager.add_event("heatwave", "1h")

        # Specific event including TEMP001
        event2 = weather_event_manager.add_event("drought", "1h",
                                                 affected_sensors=["TEMP001"])

        events = weather_event_manager.get_events_for_sensor("TEMP001")

        assert len(events) == 2
        event_ids = {e["id"] for e in events}
        assert event1["id"] in event_ids
        assert event2["id"] in event_ids


class TestClearAllEvents:
    """Test clearing all events"""

    def test_clear_all_events_empty(self, weather_event_manager):
        """Should handle clearing when no events"""
        count = weather_event_manager.clear_all_events()
        assert count == 0

    def test_clear_all_events_with_events(self, weather_event_manager):
        """Should clear all active events"""
        weather_event_manager.add_event("heatwave", "1h")
        weather_event_manager.add_event("drought", "1h")
        weather_event_manager.add_event("frost", "1h")

        assert len(weather_event_manager.active_events) == 3

        count = weather_event_manager.clear_all_events()

        assert count == 3
        assert len(weather_event_manager.active_events) == 0

    def test_clear_all_events_returns_count(self, weather_event_manager):
        """Should return number of events cleared"""
        weather_event_manager.add_event("heatwave", "1h")
        weather_event_manager.add_event("drought", "1h")

        count = weather_event_manager.clear_all_events()

        assert count == 2


class TestApplyEventsToReading:
    """Test applying events to sensor readings"""

    def test_apply_events_no_active_events(self, weather_event_manager):
        """Should return original value when no events"""
        value = weather_event_manager.apply_events_to_reading("TEMP001", "temperature", 25.0)
        assert value == 25.0

    def test_apply_heatwave_to_temperature(self, weather_event_manager):
        """Heatwave should increase temperature"""
        weather_event_manager.add_event("heatwave", "1h")

        original_value = 25.0
        modified_value = weather_event_manager.apply_events_to_reading(
            "TEMP001", "temperature", original_value)

        # Should increase temperature (effect is 10-20 degrees)
        assert modified_value > original_value
        assert modified_value >= 35.0  # At least +10

    def test_apply_coldfront_to_temperature(self, weather_event_manager):
        """Cold front should decrease temperature"""
        weather_event_manager.add_event("coldfront", "1h")

        original_value = 25.0
        modified_value = weather_event_manager.apply_events_to_reading(
            "TEMP001", "temperature", original_value)

        # Should decrease temperature (effect is -15 to -5 degrees)
        assert modified_value < original_value
        assert modified_value <= 20.0  # At most -5

    def test_apply_rainstorm_to_humidity(self, weather_event_manager):
        """Rainstorm should increase humidity"""
        weather_event_manager.add_event("rainstorm", "1h")

        original_value = 50.0
        modified_value = weather_event_manager.apply_events_to_reading(
            "HUM001", "humidity", original_value)

        # Should increase humidity (effect is +20 to +30)
        assert modified_value > original_value
        assert modified_value >= 70.0  # At least +20

    def test_apply_rainstorm_to_soil_moisture(self, weather_event_manager):
        """Rainstorm should increase soil moisture"""
        weather_event_manager.add_event("rainstorm", "1h")

        original_value = 40.0
        modified_value = weather_event_manager.apply_events_to_reading(
            "SOIL001", "soil_moisture", original_value)

        # Should increase soil moisture (effect is +15 to +25)
        assert modified_value > original_value
        assert modified_value >= 55.0  # At least +15

    def test_apply_drought_effects(self, weather_event_manager):
        """Drought should have appropriate effects on all sensor types"""
        weather_event_manager.add_event("drought", "1h")

        # Temperature should increase
        temp_modified = weather_event_manager.apply_events_to_reading(
            "TEMP001", "temperature", 25.0)
        assert temp_modified > 25.0

        # Humidity should decrease
        humidity_modified = weather_event_manager.apply_events_to_reading(
            "HUM001", "humidity", 60.0)
        assert humidity_modified < 60.0

        # Soil moisture should decrease significantly
        moisture_modified = weather_event_manager.apply_events_to_reading(
            "SOIL001", "soil_moisture", 50.0)
        assert moisture_modified < 50.0

    def test_apply_multiple_events(self, weather_event_manager):
        """Should apply effects from multiple events"""
        # Add two events that both affect temperature
        weather_event_manager.add_event("heatwave", "1h")
        weather_event_manager.add_event("drought", "1h")

        original_value = 25.0
        modified_value = weather_event_manager.apply_events_to_reading(
            "TEMP001", "temperature", original_value)

        # Both events increase temperature, so effect should be larger
        assert modified_value > original_value
        # Heatwave: +10 to +20, Drought: +5 to +10 = +15 to +30 total
        assert modified_value >= 40.0  # At least +15

    def test_apply_events_only_to_affected_sensors(self, weather_event_manager):
        """Should only apply events to affected sensors"""
        # Event only affects TEMP001
        weather_event_manager.add_event("heatwave", "1h", affected_sensors=["TEMP001"])

        # TEMP001 should be affected
        temp001_value = weather_event_manager.apply_events_to_reading(
            "TEMP001", "temperature", 25.0)
        assert temp001_value > 25.0

        # TEMP002 should not be affected
        temp002_value = weather_event_manager.apply_events_to_reading(
            "TEMP002", "temperature", 25.0)
        assert temp002_value == 25.0

    def test_apply_events_with_unknown_sensor_type(self, weather_event_manager):
        """Should handle unknown sensor types gracefully"""
        weather_event_manager.add_event("heatwave", "1h")

        # Unknown sensor type should return original value
        value = weather_event_manager.apply_events_to_reading(
            "UNKNOWN001", "unknown_type", 50.0)
        assert value == 50.0


class TestEventExpiration:
    """Test event expiration and cleanup"""

    def test_expired_events_are_cleaned_up(self, weather_event_manager):
        """Expired events should be removed from active events"""
        # Add event that expires very soon
        event = weather_event_manager.add_event("frost", "1s")

        # Verify it's active initially
        assert event["id"] in weather_event_manager.active_events

        # Wait for expiration
        time.sleep(1.5)

        # Trigger cleanup by calling get_active_events
        weather_event_manager.get_active_events()

        # Event should be removed
        assert event["id"] not in weather_event_manager.active_events

    def test_active_events_remain(self, weather_event_manager):
        """Non-expired events should remain active"""
        # Add long-duration event
        event = weather_event_manager.add_event("heatwave", "1h")

        # Get active events (triggers cleanup)
        active = weather_event_manager.get_active_events()

        # Event should still be there
        assert len(active) == 1
        assert event["id"] in weather_event_manager.active_events


class TestEdgeCases:
    """Test edge cases"""

    def test_add_very_short_duration_event(self, weather_event_manager):
        """Should handle very short duration events"""
        event = weather_event_manager.add_event("frost", "1s")
        assert event["duration_seconds"] == 1

    def test_add_very_long_duration_event(self, weather_event_manager):
        """Should handle very long duration events"""
        event = weather_event_manager.add_event("drought", "365d")
        assert event["duration_seconds"] == 365 * 86400

    def test_apply_events_with_zero_value(self, weather_event_manager):
        """Should handle applying events to zero value"""
        weather_event_manager.add_event("heatwave", "1h")

        modified = weather_event_manager.apply_events_to_reading(
            "TEMP001", "temperature", 0.0)

        # Should still apply effect
        assert modified > 0.0

    def test_apply_events_with_negative_value(self, weather_event_manager):
        """Should handle applying events to negative value"""
        weather_event_manager.add_event("coldfront", "1h")

        modified = weather_event_manager.apply_events_to_reading(
            "TEMP001", "temperature", -10.0)

        # Should still apply effect
        assert modified < -10.0
