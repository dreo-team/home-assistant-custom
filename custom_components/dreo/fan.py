"""Support for Dreo fans."""
from __future__ import annotations

import logging
import math
from functools import cached_property
from typing import Any
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage, int_states_in_range
)
from hscloud.const import DEVICE_TYPE, FAN_DEVICE

from . import MyConfigEntry
from .entity import DreoEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: MyConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Fan from a config entry."""

    async_add_entities([
        DreoFanHA(device, config_entry)
        for device in config_entry.runtime_data.devices
        if DEVICE_TYPE.get(device.get("model")) == FAN_DEVICE.get("type")
    ])


class DreoFanHA(DreoEntity, FanEntity):
    """Dreo fan."""

    _attr_supported_features = (FanEntityFeature.PRESET_MODE
                                | FanEntityFeature.SET_SPEED
                                | FanEntityFeature.OSCILLATE)

    def __init__(self, device, config_entry) -> None:
        """Initialize the Dreo fan."""
        super().__init__(device, config_entry)
        self._attr_preset_modes = FAN_DEVICE.get("config").get(self._model).get("preset_modes")
        self._attr_low_high_range = FAN_DEVICE.get("config").get(self._model).get("speed_range")
        self._attr_speed_count = int_states_in_range(self._attr_low_high_range)

    @property
    def is_on(self) -> bool | None:
        """Return True if device is on."""
        return self._attr_state

    @cached_property
    def preset_modes(self) -> list[str] | None:
        """Return a list of available preset modes.

        Requires FanEntityFeature.SET_SPEED.
        """
        if hasattr(self, "_attr_preset_modes"):
            return self._attr_preset_modes
        return None

    @cached_property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        if hasattr(self, "_attr_speed_count"):
            return self._attr_speed_count
        return 6

    @cached_property
    def percentage(self) -> int | None:
        """Return the current speed as a percentage."""
        if hasattr(self, "_attr_percentage"):
            return ranged_value_to_percentage(
                FAN_DEVICE.get("config").get(self._model).get("speed_range"),
                self._attr_percentage
            )
        return 0

    @property
    def available(self) -> bool:
        """Return True if device is available."""
        return self._attr_available

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        self._try_command(
            "Turn the device on failed.", power_switch=True
        )
        self._attr_state = True

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        self._try_command(
            "Turn the device off failed.", power_switch=False
        )
        self._attr_state = False

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of fan."""
        self._try_command(
            "Set the preset mode failed.", mode=preset_mode
        )
        self._attr_preset_mode = preset_mode

    def set_percentage(self, percentage: int) -> None:
        """Set the speed of fan."""
        speed = math.ceil(
            percentage_to_ranged_value(
                self._attr_low_high_range, percentage
            )
        )

        self._try_command(
            "Set the speed failed.", speed=speed
        )
        self._attr_percentage = speed

    def oscillate(self, oscillating: bool) -> None:
        """Set the Oscillate of fan."""
        self._try_command(
            "Set the Oscillate failed.", oscillate=oscillating
        )
        self._attr_oscillating = oscillating

    def update(self) -> None:
        """Update Dreo fan."""
        status = self._config_entry.runtime_data.client.get_status(self._device_id)
        if status is not None:
            self._attr_state = status.get('power_switch')
            self._attr_preset_mode = status.get('mode')
            self._attr_percentage = status.get('speed')
            self._attr_oscillating = status.get('oscillate')
            self._attr_available = status.get('connected')

        else:
            self._attr_available = False
