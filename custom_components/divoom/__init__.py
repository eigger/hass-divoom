# __init__.py
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
import logging, time
from .const import DOMAIN
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
        pixoo = hass.data[DOMAIN][entry.entry_id]['pixoo']
        hass.async_add_executor_job(async_service, pixoo, call)

    @callback
    def countdown_service(call: ServiceCall) -> None:
        """My first service."""
        pixoo = hass.data[DOMAIN][entry.entry_id]['pixoo']
        hass.async_add_executor_job(async_service, pixoo, call)
        
    @callback
    def stopwatch_service(call: ServiceCall) -> None:
        """My first service."""
        pixoo = hass.data[DOMAIN][entry.entry_id]['pixoo']
        hass.async_add_executor_job(async_service, pixoo, call)

    # Register our service with Home Assistant.
    hass.services.async_register(DOMAIN, 'show_message', message_service)
    hass.services.async_register(DOMAIN, 'countdown', countdown_service)
    hass.services.async_register(DOMAIN, 'stopwatch', stopwatch_service)
    return True

def async_service(pixoo, call):
    if 'message' in call.data:
        msg = call.data['message']
        channel = pixoo.get_channel()
        pixoo.clear()
        pixoo.push()
        time.sleep(2)
        response = pixoo.send_text(str(msg))
        _LOGGER.info(f"response message: {response}")
        time.sleep(call.data['duration'])
        pixoo.set_channel(channel)
    elif 'minute' in call.data and 'second' in call.data:
        minute = call.data['minute']
        second = call.data['second']
        if int(minute) > 0 or int(second) > 0:
            response = pixoo.start_countdown(minute, second)
        else:
            response = pixoo.stop_countdown(minute, second)
        _LOGGER.info(f"response message: {response}")
    elif 'mode' in call.data:
        mode = call.data['mode']
        if mode == 'reset':
            response = pixoo.set_stopwatch(2)
        elif mode == 'start': 
            response = pixoo.set_stopwatch(1)
        else:
            response = pixoo.set_stopwatch(0)
        _LOGGER.info(f"response message: {response}")
    else:
        _LOGGER.error(f"Error message: {call.data}")

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

