from homeassistant.components.light import (LightEntity, ATTR_EFFECT, ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, ColorMode, LightEntityFeature)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.device_registry import DeviceInfo, CONNECTION_NETWORK_MAC

from . import DOMAIN

from .pixoo64._pixoo import Pixoo
import logging

_LOGGER = logging.getLogger(__name__)
BRIGHTNESS_SCALE = (1, 100)


async def async_setup_entry(hass, config_entry: ConfigEntry, async_add_entities):
    async_add_entities([ DivoomLight(config_entry=config_entry, pixoo=hass.data[DOMAIN][config_entry.entry_id]["pixoo"]) ], True)


class DivoomLight(LightEntity):
    def __init__(self, ip_address=None, config_entry: ConfigEntry = None, pixoo: Pixoo = None):
        self._ip_address = ip_address
        self._config_entry = config_entry
        self._attr_has_entity_name = True
        self._name = "Light"
        self._pixoo = Pixoo(self._ip_address) if pixoo is None else pixoo
        self.color_mode = ColorMode.BRIGHTNESS
        self._brightness = None
        self._state = None
        self.effect_list = ["Faces", "Cloud Channel", "Visualizer", "Custom"]
        _LOGGER.debug(f"Divoom IP address from configuration: {self._ip_address}")

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self) -> bool | None:
        return self._state

    @property
    def brightness(self):
        return self._brightness

    def turn_on(self, **kwargs):
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
            brightness_percent = int((self._brightness / 255.0) * 100)
            self._pixoo.set_brightness(brightness_percent)
        if ATTR_EFFECT in kwargs:
            self.effect = kwargs[ATTR_EFFECT]
            if self.effect in self.effect_list:
                channel = self.effect_list.index(self.effect)
                self._pixoo.set_channel(channel)

        self._state = True
        self._pixoo.set_screen(True)

    def turn_off(self, **kwargs):
        self._state = False
        self._pixoo.set_screen(False)

    def update(self) -> None:
        try:
            if len(self._pixoo.name) == 0:
                devices = self._pixoo.get_lan_devices()
                for device in devices:
                    if self._pixoo.address is device["DevicePrivateIP"]:
                        self._pixoo.name = device["DeviceName"]
                        self._pixoo.id_number = device["DeviceId"]
                        self._pixoo.mac_address = device["DeviceMac"]

            conf = self._pixoo.get_all_conf()
            self._state = conf['LightSwitch'] == 1
            brightness_percent = conf['Brightness']
            channel = self._pixoo.get_channel()
            self.effect = self.effect_list[channel]
            self._brightness = int((brightness_percent / 100.0) * 255)


        except:
            pass

    @property
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        return {ColorMode.BRIGHTNESS}
    
    @property
    def supported_features(self) -> LightEntityFeature:
        """Flag supported features."""
        return self._attr_supported_features | LightEntityFeature.EFFECT
    
    @property
    def unique_id(self):
        return "light_" + str(self._config_entry.entry_id)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._config_entry.entry_id)) if self._config_entry is not None else (DOMAIN, "divoom")},
            connections={
                (
                    CONNECTION_NETWORK_MAC,
                    self._pixoo.mac_address,
                )
            },
            name=self._config_entry.title,
            manufacturer="Divoom",
            model=self._pixoo.name,
            model_id=self._pixoo.id_number,
        )

    @property
    def icon(self) -> str | None:
        """Icon of the entity, based on time."""
        if self.effect == "Faces":
            return "mdi:clock"
        elif self.effect == "Cloud Channel":
            return "mdi:cloud"
        elif self.effect == "Visualizer":
            return "mdi:waveform"
        elif self.effect == "Custom":
            return "mdi:panorama-variant"       
        return "mdi:monitor-shimmer"