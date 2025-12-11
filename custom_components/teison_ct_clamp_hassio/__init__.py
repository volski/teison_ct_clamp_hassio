"""Meter Values component for Home Assistant."""
import logging
import json
import asyncio
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import websockets

_LOGGER = logging.getLogger(__name__)

DOMAIN = "teison_ct_clamp_hassio"
PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Meter Values from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    host = entry.data.get(CONF_HOST, "0.0.0.0")
    port = entry.data.get(CONF_PORT, 8080)
    
    # Store the meter data in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "host": host,
        "port": port,
        "meter_data": {},
        "listeners": []
    }
    
    # Start WebSocket server
    try:
        await start_websocket_server(hass, entry, host, port)
    except Exception as e:
        _LOGGER.error("Failed to start WebSocket server: %s", e)
        return False
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def start_websocket_server(hass: HomeAssistant, entry: ConfigEntry, host: str, port: int):
    """Start WebSocket server to listen for meter data."""
    import websockets
    
    entry_data = hass.data[DOMAIN][entry.entry_id]
    
    async def handle_client(websocket, path):
        """Handle incoming WebSocket connection."""
        _LOGGER.info("Meter client connected from %s", websocket.remote_address)
        try:
            async for message in websocket:
                try:
                    msg = json.loads(message)
                    if isinstance(msg, list) and len(msg) >= 4:
                        msg_type, msg_id, action, payload = msg[0], msg[1], msg[2], msg[3]
                        
                        if action == "MeterValues":
                            _LOGGER.debug("Received MeterValues: %s", payload)
                            # Store meter data
                            entry_data["meter_data"] = payload
                            
                            # Notify listeners (sensors) about update
                            for listener in entry_data.get("listeners", []):
                                listener()
                            
                            # Send acknowledgment
                            response = [3, msg_id, {}]
                            await websocket.send(json.dumps(response))
                            
                except json.JSONDecodeError as e:
                    _LOGGER.error("Failed to parse JSON: %s", e)
        except websockets.exceptions.ConnectionClosed:
            _LOGGER.info("Meter client disconnected")
    
    # Start WebSocket server
    try:
        server = await websockets.serve(handle_client, host, port)
        _LOGGER.info("WebSocket server started on ws://%s:%d", host, port)
        entry_data["server"] = server
        
        # Store server cleanup task
        async def stop_server():
            if "server" in entry_data:
                entry_data["server"].close()
                await entry_data["server"].wait_closed()
        
        hass.bus.async_listen_once("homeassistant_stop", lambda event: asyncio.create_task(stop_server()))
    except Exception as e:
        _LOGGER.error("Failed to start WebSocket server: %s", e)
        raise

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
