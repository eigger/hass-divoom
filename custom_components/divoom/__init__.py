# __init__.py
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
import logging
from .const import DOMAIN, VERSION
from .pixoo64 import Pixoo

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, update=False):
    """Set up Divoom from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    await async_detect_and_fix_old_entry(hass, entry)  # Tries to detect and fix old entries.
    _LOGGER.debug("Setting up entry %s.", entry.entry_id)

    try:
        pix = await hass.async_add_executor_job(load_pixoo, entry.options.get('ip_address'))
    except Exception as e:
        _LOGGER.error("Error setting up Pixoo: %s", e)
        return False

    hass.data[DOMAIN][entry.entry_id] = {}
    hass.data[DOMAIN][entry.entry_id]['pixoo'] = pix
    hass.data[DOMAIN][entry.entry_id]['entry_data'] = entry.options

    await hass.config_entries.async_forward_entry_setups(entry, ["light", "sensor"])
    if not update:
        entry.add_update_listener(async_update_entry)

    @callback
    def message_service(call: ServiceCall) -> None:
        """My first service."""
        hass.async_add_executor_job(await async_message_service(call))

    async def async_message_service(call):
        pixoo = hass.data[DOMAIN][entry.entry_id]['pixoo']
        pixoo.set_screen_off()

    # Register our service with Home Assistant.
    hass.services.async_register(DOMAIN, 'show_message', message_service)
    return True



def load_pixoo(ip_address: str):
    """Load the Pixoo device. This is a blocking call."""
    return Pixoo(ip_address)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry. Called by HA."""
    _LOGGER.debug("Unload entry %s.", entry.entry_id)

    del hass.data[DOMAIN][entry.entry_id]

    return await hass.config_entries.async_unload_platforms(entry, ["light", "sensor"])


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry):
    # Called by HA when the config entry is updated.
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry, True)
    _LOGGER.debug("Updated entry %s.", entry.entry_id)


async def async_detect_and_fix_old_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Detect old entry. Called for every entry when HA find the versions don't match."""


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry. Called for every entry when HA find the versions don't match."""
    return True

