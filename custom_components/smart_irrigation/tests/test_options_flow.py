"""Test the Smart Irrigation options flow."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.data_entry_flow import FlowResultType

from custom_components.smart_irrigation.options_flow import (
    SmartIrrigationOptionsFlowHandler,
)
from custom_components.smart_irrigation.const import (
    CONF_USE_WEATHER_SERVICE,
    CONF_WEATHER_SERVICE,
    CONF_WEATHER_SERVICE_API_KEY,
    CONF_WEATHER_SERVICE_API_VERSION,
    CONF_WEATHER_SERVICE_OWM,
)
from custom_components.smart_irrigation.helpers import CannotConnect, InvalidAuth


class TestSmartIrrigationOptionsFlow:
    """Test Smart Irrigation options flow."""

    @pytest.fixture
    def mock_hass(self):
        """Return a mock Home Assistant instance."""
        hass = Mock()
        hass.data = {}
        return hass

    @pytest.fixture
    def mock_config_entry(self):
        """Return a mock config entry."""
        return ConfigEntry(
            version=1,
            domain="smart_irrigation",
            title="Smart Irrigation",
            data={
                CONF_USE_WEATHER_SERVICE: False,
                CONF_WEATHER_SERVICE: None,
                CONF_WEATHER_SERVICE_API_KEY: None,
                CONF_WEATHER_SERVICE_API_VERSION: None,
            },
            options={},
            source="user",
            entry_id="test_entry_id",
        )

    @pytest.fixture
    def mock_config_entry_with_weather(self):
        """Return a mock config entry with weather service enabled."""
        return ConfigEntry(
            version=1,
            domain="smart_irrigation",
            title="Smart Irrigation",
            data={
                CONF_USE_WEATHER_SERVICE: True,
                CONF_WEATHER_SERVICE: CONF_WEATHER_SERVICE_OWM,
                CONF_WEATHER_SERVICE_API_KEY: "test_api_key",
                CONF_WEATHER_SERVICE_API_VERSION: "3.0",
            },
            options={},
            source="user",
            entry_id="test_entry_id",
        )

    @pytest.fixture
    def options_flow(self, mock_hass, mock_config_entry):
        """Return a SmartIrrigationOptionsFlowHandler instance."""
        flow = SmartIrrigationOptionsFlowHandler(mock_config_entry)
        flow.hass = mock_hass
        return flow

    @pytest.fixture
    def options_flow_with_weather(self, mock_hass, mock_config_entry_with_weather):
        """Return a SmartIrrigationOptionsFlowHandler instance with weather service."""
        flow = SmartIrrigationOptionsFlowHandler(mock_config_entry_with_weather)
        flow.hass = mock_hass
        return flow

    def test_options_flow_initialization(self, options_flow, mock_config_entry):
        """Test options flow initialization."""
        assert options_flow.config_entry == mock_config_entry
        assert options_flow._use_weather_service is False
        assert options_flow._weather_service is None
        assert options_flow._weather_service_api_key is None

    def test_options_flow_initialization_with_weather(self, options_flow_with_weather):
        """Test options flow initialization with weather service."""
        assert options_flow_with_weather._use_weather_service is True
        assert options_flow_with_weather._weather_service == CONF_WEATHER_SERVICE_OWM
        assert options_flow_with_weather._weather_service_api_key == "test_api_key"

    async def test_async_step_init_no_weather_service(self, options_flow):
        """Test init step without weather service."""
        user_input = {CONF_USE_WEATHER_SERVICE: False}

        result = await options_flow.async_step_init(user_input)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_USE_WEATHER_SERVICE] is False
        assert result["data"][CONF_WEATHER_SERVICE_API_KEY] is None

    async def test_async_step_init_with_weather_service(self, options_flow):
        """Test init step with weather service."""
        user_input = {CONF_USE_WEATHER_SERVICE: True}

        with patch.object(options_flow, "_show_step_1") as mock_show_step_1:
            mock_show_step_1.return_value = {"type": "form", "step_id": "step1"}

            result = await options_flow.async_step_init(user_input)

            assert result["type"] == "form"
            assert result["step_id"] == "step1"
            mock_show_step_1.assert_called_once_with(user_input)

    async def test_async_step_init_no_input(self, options_flow):
        """Test init step without user input."""
        result = await options_flow.async_step_init(None)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"
        assert CONF_USE_WEATHER_SERVICE in result["data_schema"].schema

    async def test_async_step_step1_valid_api_key(self, options_flow):
        """Test step1 with valid API key."""
        options_flow._use_weather_service = True
        user_input = {
            CONF_WEATHER_SERVICE: CONF_WEATHER_SERVICE_OWM,
            CONF_WEATHER_SERVICE_API_KEY: "valid_api_key",
        }

        with patch(
            "custom_components.smart_irrigation.options_flow.test_api_key"
        ) as mock_test_api:
            mock_test_api.return_value = True

            result = await options_flow.async_step_step1(user_input)

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["data"][CONF_WEATHER_SERVICE] == CONF_WEATHER_SERVICE_OWM
            assert result["data"][CONF_WEATHER_SERVICE_API_KEY] == "valid_api_key"
            assert result["data"][CONF_USE_WEATHER_SERVICE] is True

    async def test_async_step_step1_invalid_api_key(self, options_flow):
        """Test step1 with invalid API key."""
        options_flow._use_weather_service = True
        user_input = {
            CONF_WEATHER_SERVICE: CONF_WEATHER_SERVICE_OWM,
            CONF_WEATHER_SERVICE_API_KEY: "invalid_api_key",
        }

        with patch(
            "custom_components.smart_irrigation.options_flow.test_api_key"
        ) as mock_test_api:
            mock_test_api.side_effect = InvalidAuth()

            with patch.object(options_flow, "_show_step_1") as mock_show_step_1:
                mock_show_step_1.return_value = {"type": "form", "step_id": "step1"}

                result = await options_flow.async_step_step1(user_input)

                assert options_flow._errors["base"] == "auth"
                assert result["type"] == "form"
                mock_show_step_1.assert_called()

    async def test_async_step_step1_cannot_connect(self, options_flow):
        """Test step1 with connection error."""
        options_flow._use_weather_service = True
        user_input = {
            CONF_WEATHER_SERVICE: CONF_WEATHER_SERVICE_OWM,
            CONF_WEATHER_SERVICE_API_KEY: "test_api_key",
        }

        with patch(
            "custom_components.smart_irrigation.options_flow.test_api_key"
        ) as mock_test_api:
            mock_test_api.side_effect = CannotConnect()

            with patch.object(options_flow, "_show_step_1") as mock_show_step_1:
                mock_show_step_1.return_value = {"type": "form", "step_id": "step1"}

                result = await options_flow.async_step_step1(user_input)

                assert options_flow._errors["base"] == "auth"
                assert result["type"] == "form"

    async def test_async_step_step1_no_input(self, options_flow):
        """Test step1 without user input."""
        with patch.object(options_flow, "_show_step_1") as mock_show_step_1:
            mock_show_step_1.return_value = {"type": "form", "step_id": "step1"}

            result = await options_flow.async_step_step1(None)

            assert result["type"] == "form"
            mock_show_step_1.assert_called()

    def test_options_flow_migration_from_owm(self, mock_hass):
        """Test options flow migration from old OWM config."""
        mock_config_entry = ConfigEntry(
            version=1,
            domain="smart_irrigation",
            title="Smart Irrigation",
            data={
                "use_owm": True,
                "owm_api_key": "old_api_key",
            },
            options={},
            source="user",
            entry_id="test_entry_id",
        )

        flow = SmartIrrigationOptionsFlowHandler(mock_config_entry)

        assert flow._use_weather_service is True
        assert flow._weather_service == CONF_WEATHER_SERVICE_OWM
        assert flow._weather_service_api_key == "old_api_key"

    def test_options_flow_with_options_override(self, mock_hass):
        """Test options flow with options overriding data."""
        mock_config_entry = ConfigEntry(
            version=1,
            domain="smart_irrigation",
            title="Smart Irrigation",
            data={
                CONF_USE_WEATHER_SERVICE: False,
            },
            options={
                CONF_USE_WEATHER_SERVICE: True,
                CONF_WEATHER_SERVICE: CONF_WEATHER_SERVICE_OWM,
                CONF_WEATHER_SERVICE_API_KEY: "options_api_key",
            },
            source="user",
            entry_id="test_entry_id",
        )

        flow = SmartIrrigationOptionsFlowHandler(mock_config_entry)

        assert flow._use_weather_service is True
        assert flow._weather_service == CONF_WEATHER_SERVICE_OWM
        assert flow._weather_service_api_key == "options_api_key"

    def test_api_key_whitespace_stripping(self, mock_hass):
        """Test that API keys are stripped of whitespace."""
        mock_config_entry = ConfigEntry(
            version=1,
            domain="smart_irrigation",
            title="Smart Irrigation",
            data={
                CONF_WEATHER_SERVICE_API_KEY: "  api_key_with_spaces  ",
            },
            options={},
            source="user",
            entry_id="test_entry_id",
        )

        flow = SmartIrrigationOptionsFlowHandler(mock_config_entry)

        assert flow._weather_service_api_key == "api_key_with_spaces"
