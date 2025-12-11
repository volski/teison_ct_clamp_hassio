"""Meter Values component for Home Assistant."""
import logging
import json
import asyncio
from datetime import datetime, timezone
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
    port = entry.data.get(CONF_PORT, 12345)

    # Store the meter data in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "host": host,
        "port": port,
        "meter_data": {},
        "last_update": None,
        "listeners": [],
        "server": None,
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

    # If a server is already running for this entry, close it first
    existing_server = entry_data.get("server")
    if existing_server is not None:
        existing_server.close()
        await existing_server.wait_closed()
        entry_data["server"] = None

    # websockets.serve in current HA expects handlers with a single
    # websocket argument; the connection path is available as
    # websocket.path if needed.
    async def handle_client(websocket):
        """Handle incoming WebSocket connection."""
        _LOGGER.info("Meter client connected from %s", websocket.remote_address)
        try:
            async for message in websocket:
                _LOGGER.debug("Raw WebSocket message: %s", message)
                try:
                    msg = json.loads(message)
                    if isinstance(msg, list) and len(msg) >= 4:
                        msg_type, msg_id, action, payload = msg[0], msg[1], msg[2], msg[3]

                        # Handle OCPP BootNotification so the charger will continue
                        if action == "BootNotification":
                            _LOGGER.debug("Received BootNotification: %s", payload)
                            boot_response = [
                                3,
                                msg_id,
                                {
                                    "status": "Accepted",
                                    "currentTime": datetime.now(timezone.utc).isoformat(),
                                    "interval": 300,
                                },
                            ]
                            await websocket.send(json.dumps(boot_response))
                            continue

                        if action == "MeterValues":
                            _LOGGER.debug("Received MeterValues: %s", payload)
                            # Store meter data and update timestamp
                            entry_data["meter_data"] = payload
                            entry_data["last_update"] = datetime.now(timezone.utc)
                            
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
        entry_data = hass.data[DOMAIN].get(entry.entry_id)
        server = entry_data.get("server") if entry_data else None

        if server is not None:
            server.close()
            await server.wait_closed()

        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
