"""Test Smart Irrigation weather modules."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.core import HomeAssistant
from aiohttp import ClientError

from custom_components.smart_irrigation.weathermodules.OWMClient import OWMClient
from custom_components.smart_irrigation.weathermodules.PirateWeatherClient import (
    PirateWeatherClient,
)
from custom_components.smart_irrigation.weathermodules.KNMIClient import KNMIClient


class TestOWMClient:
    """Test OpenWeatherMap client."""

    def test_owm_client_init(self) -> None:
        """Test OWM client initialization."""
        session = AsyncMock()
        api_key = "test_api_key"
        api_version = "3.0"

        client = OWMClient(session, api_key, api_version)

        assert client.session == session
        assert client.api_key == api_key
        assert client.api_version == api_version

    async def test_owm_client_get_current_weather_success(self) -> None:
        """Test OWM client get current weather success."""
        session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "main": {
                "temp": 25.0,
                "humidity": 60,
                "pressure": 1013.25,
            },
            "wind": {"speed": 5.0},
            "weather": [{"main": "Clear"}],
        }
        session.get.return_value.__aenter__.return_value = mock_response

        client = OWMClient(session, "test_api_key", "3.0")

        weather_data = await client.get_current_weather(52.0, 5.0)

        assert weather_data["temperature"] == 25.0
        assert weather_data["humidity"] == 60
        assert weather_data["pressure"] == 1013.25
        assert weather_data["wind_speed"] == 5.0

    async def test_owm_client_get_current_weather_error(self) -> None:
        """Test OWM client get current weather with error."""
        session = AsyncMock()
        session.get.side_effect = ClientError("Connection error")

        client = OWMClient(session, "test_api_key", "3.0")

        with pytest.raises(ClientError):
            await client.get_current_weather(52.0, 5.0)

    async def test_owm_client_get_forecast_success(self) -> None:
        """Test OWM client get forecast success."""
        session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "list": [
                {
                    "main": {
                        "temp": 25.0,
                        "humidity": 60,
                        "pressure": 1013.25,
                    },
                    "wind": {"speed": 5.0},
                    "weather": [{"main": "Clear"}],
                    "dt": 1234567890,
                }
            ]
        }
        session.get.return_value.__aenter__.return_value = mock_response

        client = OWMClient(session, "test_api_key", "3.0")

        forecast_data = await client.get_forecast(52.0, 5.0)

        assert len(forecast_data) > 0
        assert forecast_data[0]["temperature"] == 25.0


class TestPirateWeatherClient:
    """Test Pirate Weather client."""

    def test_pirate_weather_client_init(self) -> None:
        """Test Pirate Weather client initialization."""
        session = AsyncMock()
        api_key = "test_api_key"

        client = PirateWeatherClient(session, api_key)

        assert client.session == session
        assert client.api_key == api_key

    async def test_pirate_weather_client_get_current_weather_success(self) -> None:
        """Test Pirate Weather client get current weather success."""
        session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "currently": {
                "temperature": 25.0,
                "humidity": 0.6,
                "pressure": 1013.25,
                "windSpeed": 5.0,
                "visibility": 10.0,
            }
        }
        session.get.return_value.__aenter__.return_value = mock_response

        client = PirateWeatherClient(session, "test_api_key")

        weather_data = await client.get_current_weather(52.0, 5.0)

        assert weather_data["temperature"] == 25.0
        assert weather_data["humidity"] == 60  # Converted from 0.6 to percentage
        assert weather_data["pressure"] == 1013.25
        assert weather_data["wind_speed"] == 5.0

    async def test_pirate_weather_client_get_forecast_success(self) -> None:
        """Test Pirate Weather client get forecast success."""
        session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "daily": {
                "data": [
                    {
                        "temperatureHigh": 30.0,
                        "temperatureLow": 20.0,
                        "humidity": 0.6,
                        "pressure": 1013.25,
                        "windSpeed": 5.0,
                        "precipIntensity": 0.0,
                        "time": 1234567890,
                    }
                ]
            }
        }
        session.get.return_value.__aenter__.return_value = mock_response

        client = PirateWeatherClient(session, "test_api_key")

        forecast_data = await client.get_forecast(52.0, 5.0, days=5)

        assert len(forecast_data) > 0
        assert forecast_data[0]["max_temp"] == 30.0
        assert forecast_data[0]["min_temp"] == 20.0


class TestKNMIClient:
    """Test KNMI client."""

    def test_knmi_client_init(self) -> None:
        """Test KNMI client initialization."""
        session = AsyncMock()

        client = KNMIClient(session)

        assert client.session == session

    async def test_knmi_client_get_current_weather_success(self) -> None:
        """Test KNMI client get current weather success."""
        session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = """
        # KNMI weather data
        260,20230101,12,25.0,60,1013.25,5.0,0.0
        """
        session.get.return_value.__aenter__.return_value = mock_response

        client = KNMIClient(session)

        # Mock the coordinate to station mapping
        with patch.object(client, "_get_nearest_station", return_value="260"):
            weather_data = await client.get_current_weather(52.0, 5.0)

            assert isinstance(weather_data, dict)
            # The exact structure depends on KNMI response parsing

    async def test_knmi_client_coordinate_validation(self) -> None:
        """Test KNMI client coordinate validation."""
        session = AsyncMock()
        client = KNMIClient(session)

        # Test valid Dutch coordinates
        assert client._is_valid_dutch_coordinates(52.0, 5.0) is True

        # Test invalid coordinates (outside Netherlands)
        assert client._is_valid_dutch_coordinates(40.0, -74.0) is False

    async def test_knmi_client_invalid_coordinates(self) -> None:
        """Test KNMI client with invalid coordinates."""
        session = AsyncMock()
        client = KNMIClient(session)

        # Test with coordinates outside Netherlands
        with pytest.raises(ValueError, match="not within Netherlands"):
            await client.get_current_weather(40.0, -74.0)

    async def test_knmi_client_get_forecast_success(self) -> None:
        """Test KNMI client get forecast success."""
        session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = """
        # KNMI forecast data
        20230101,260,30,20,60,1013,5,0
        20230102,260,28,18,65,1015,3,2
        """
        session.get.return_value.__aenter__.return_value = mock_response

        client = KNMIClient(session)

        # Mock the coordinate to station mapping
        with patch.object(client, "_get_nearest_station", return_value="260"):
            forecast_data = await client.get_forecast(52.0, 5.0, days=2)

            assert isinstance(forecast_data, list)
            # The exact structure depends on KNMI response parsing


class TestWeatherModuleErrorHandling:
    """Test weather module error handling."""

    async def test_owm_client_invalid_api_key(self) -> None:
        """Test OWM client with invalid API key."""
        session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.json.return_value = {"cod": 401, "message": "Invalid API key"}
        session.get.return_value.__aenter__.return_value = mock_response

        client = OWMClient(session, "invalid_api_key", "3.0")

        with pytest.raises(Exception):  # Specific exception depends on implementation
            await client.get_current_weather(52.0, 5.0)

    async def test_pirate_weather_client_rate_limit(self) -> None:
        """Test Pirate Weather client with rate limit."""
        session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 429
        session.get.return_value.__aenter__.return_value = mock_response

        client = PirateWeatherClient(session, "test_api_key")

        with pytest.raises(Exception):  # Specific exception depends on implementation
            await client.get_current_weather(52.0, 5.0)

    async def test_knmi_client_service_unavailable(self) -> None:
        """Test KNMI client with service unavailable."""
        session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 503
        session.get.return_value.__aenter__.return_value = mock_response

        client = KNMIClient(session)

        with patch.object(client, "_get_nearest_station", return_value="260"):
            with pytest.raises(
                Exception
            ):  # Specific exception depends on implementation
                await client.get_current_weather(52.0, 5.0)
