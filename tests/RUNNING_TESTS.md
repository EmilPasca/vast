# Running VAST Tests

Comprehensive guide for running the VAST test suite.

## Test Suite Overview

**Total Tests:** 155 (as of 2025-11-14)

| Module | Tests | Status |
|--------|-------|--------|
| data_storage.py | 24 | ✅ |
| vulnerability_manager.py | 44 | ✅ |
| weather_event_manager.py | 45 | ✅ |
| **temperature_sensor** (sensors/temp/app.py) | 42 | ✅ |
| **TOTAL** | **155** | **100%** |

## Prerequisites

### Install Dependencies

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Install data-server dependencies
cd data-server && pip install -r requirements.txt

# Install sensor dependencies (optional for isolated tests)
cd sensors/temp && pip install -r requirements.txt
```

##Quick Start

### Run All Unit Tests

```bash
# From project root
pytest tests/unit/ -v
```

### Run All Tests with Coverage

```bash
pytest tests/unit/ --cov=data-server --cov-report=html
```

### View Coverage Report

```bash
# Open in browser
open htmlcov/index.html
```

## Running Specific Test Modules

### Data Server Core Components

```bash
# Data storage tests (24 tests)
pytest tests/unit/test_data_storage.py -v

# Vulnerability manager tests (44 tests)
pytest tests/unit/test_vulnerability_manager.py -v

# Weather event manager tests (45 tests)
pytest tests/unit/test_weather_event_manager.py -v
```

### IoT Sensor Tests

```bash
# Temperature sensor tests (42 tests)
pytest tests/unit/test_temperature_sensor.py -v
```

## Test Organization

### By Test Class

Run specific test classes:

```bash
# Test only temperature sensor fault modes
pytest tests/unit/test_temperature_sensor.py::TestTemperatureSensorFaultStuck -v
pytest tests/unit/test_temperature_sensor.py::TestTemperatureSensorFaultDrift -v
pytest tests/unit/test_temperature_sensor.py::TestTemperatureSensorFaultSpike -v
pytest tests/unit/test_temperature_sensor.py::TestTemperatureSensorFaultDropout -v

# Test only data formatters
pytest tests/unit/test_temperature_sensor.py::TestDataFormatterRichJSON -v
pytest tests/unit/test_temperature_sensor.py::TestDataFormatterCSV -v
pytest tests/unit/test_temperature_sensor.py::TestDataFormatterBinary -v
```

### By Test Markers

```bash
# Run only unit tests
pytest -m unit -v

# Run only vulnerability tests
pytest -m vulnerability -v

# Skip slow tests
pytest -m "not slow" -v
```

## Test Output Options

### Verbose Output

```bash
pytest tests/unit/ -v
```

### Show Print Statements

```bash
pytest tests/unit/ -s
```

### Stop on First Failure

```bash
pytest tests/unit/ -x
```

### Run Last Failed Tests

```bash
pytest tests/unit/ --lf
```

### Show Slowest Tests

```bash
pytest tests/unit/ --durations=10
```

## Coverage Options

### Generate HTML Report

```bash
pytest tests/unit/ --cov=data-server --cov-report=html
```

### Generate Terminal Report

```bash
pytest tests/unit/ --cov=data-server --cov-report=term-missing
```

### Generate XML Report (for CI)

```bash
pytest tests/unit/ --cov=data-server --cov-report=xml
```

### Check Coverage Threshold

```bash
pytest tests/unit/ --cov=data-server --cov-fail-under=80
```

## Understanding Test Results

### Temperature Sensor Tests

The temperature sensor tests validate:

**1. Fault Modes** (5 modes tested):
- `none`: Normal operation with random variation
- `stuck`: Sensor returns same value repeatedly
- `drift`: Gradual increase over time (+0.1°C per reading)
- `spike`: Random extreme values (10x normal)
- `dropout`: Sensor returns None (no data)

**2. Data Formatters** (4 formats):
- `rich_json`: Full metadata with timestamp and sensor_id
- `minimal`: Raw value as string ("25.5")
- `csv`: Comma-separated (TEMP001,25.5,1234567890)
- `binary`: Packed binary (10 bytes: sensor_id + float + timestamp)

**3. Calibration**:
- Positive/negative offsets
- Applied to all fault modes
- Preserved across readings

Example test output:
```
tests/unit/test_temperature_sensor.py::TestTemperatureSensorFaultStuck::test_stuck_mode_returns_same_value PASSED
tests/unit/test_temperature_sensor.py::TestDataFormatterBinary::test_format_binary_parseable PASSED
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Ensure you're in the project root
cd /path/to/vast

# Install dependencies
pip install -r requirements-dev.txt
cd data-server && pip install -r requirements.txt
```

### Flask/MQTT Errors for Sensor Tests

The temperature sensor tests use isolated implementations and don't require Flask/MQTT. If you see import errors:

```bash
pip install flask werkzeug requests
```

### Coverage Not Working

```bash
# Reinstall pytest-cov
pip install --upgrade pytest-cov
```

## Common Test Patterns

### Testing Randomness

For tests with random behavior (like `spike` mode or random variation):

```python
# Test multiple times to account for randomness
readings = [temp_sensor.read() for _ in range(20)]
assert any(reading > 100 for reading in readings)  # At least one spike
```

### Testing Probabilities

For probability-based features (like vulnerability injection):

```python
# Test over many trials
results = [vulnerability_manager.should_inject_data_vulnerability()
          for _ in range(10000)]
injection_rate = sum(results) / len(results)
assert 0.25 <= injection_rate <= 0.35  # ~30% with tolerance
```

### Testing Time-Based Features

For features with timeouts or expiration:

```python
# Add event with short duration
weather_manager.add_event("frost", "1s")

# Wait for expiration
time.sleep(1.5)

# Verify cleanup
assert len(weather_manager.get_active_events()) == 0
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: cd data-server && pip install -r requirements.txt
      - run: pytest tests/unit/ --cov=data-server --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Next Steps

### Adding New Tests

1. Create test file in appropriate directory:
   - `tests/unit/` - Unit tests
   - `tests/integration/` - Integration tests
   - `tests/vulnerabilities/` - Security tests

2. Follow naming convention:
   - File: `test_<module_name>.py`
   - Class: `Test<FeatureName>`
   - Method: `test_<specific_behavior>`

3. Use existing fixtures from `conftest.py`

4. Run your new tests:
   ```bash
   pytest tests/unit/test_your_module.py -v
   ```

### Writing Integration Tests

Coming soon:
- Data Server API endpoints
- Gateway API endpoints
- End-to-end sensor data flow

### Writing Vulnerability Tests

Coming soon:
- BOLA (Broken Object Level Authorization)
- Authentication bypass
- Command injection
- Resource exhaustion

## Support

For issues or questions:
- Check existing test examples in `tests/unit/`
- Review `tests/conftest.py` for available fixtures
- See `tests/TEST_SUMMARY.md` for detailed coverage info

---

**Last Updated:** 2025-11-14
**Test Suite Version:** 1.0
**Total Tests:** 155 ✅
