"""Sensor platform for Meter Values."""
import logging
from datetime import datetime, timedelta, timezone
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfPower, UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

DOMAIN = "teison_ct_clamp_hassio"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    
    # Create sensor entities
    sensors = [
        # Voltage sensor
        MeterValuesSensor(entry, "voltage", "Voltage", UnitOfElectricPotential.VOLT, "mdi:flash"),
        # Power sensor
        MeterValuesSensor(entry, "power", "Power", UnitOfPower.WATT, "mdi:flash-circle"),
        # Energy sensor
        MeterValuesSensor(entry, "energy", "Energy", UnitOfEnergy.KILO_WATT_HOUR, "mdi:lightning-bolt"),
        # Per-phase current sensors
        MeterValuesSensor(entry, "current_l1", "Current L1", UnitOfElectricCurrent.AMPERE, "mdi:alpha-l"),
        MeterValuesSensor(entry, "current_l2", "Current L2", UnitOfElectricCurrent.AMPERE, "mdi:alpha-l"),
        MeterValuesSensor(entry, "current_l3", "Current L3", UnitOfElectricCurrent.AMPERE, "mdi:alpha-l"),
    ]
    
    async_add_entities(sensors)
    
    # Register update listener
    @callback
    def update_sensors():
        for sensor in sensors:
            sensor.async_write_ha_state()
    
    entry_data["listeners"].append(update_sensors)

class MeterValuesSensor(SensorEntity):
    """Sensor entity for Meter Values."""
    
    def __init__(self, entry: ConfigEntry, sensor_type: str, name: str, unit: str, icon: str):
        """Initialize the sensor."""
        self.entry = entry
        self.sensor_type = sensor_type
        self._name = name
        self._unit = unit
        self._icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._state = None
        self._last_value = None
    
    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"Meter {self._name}"
    
    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self.entry.entry_id}_{self.sensor_type}"
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        try:
            entry_data = self.hass.data[DOMAIN][self.entry.entry_id]
            meter_data = entry_data.get("meter_data", {})

            # Reset sensors if data is stale (no update for 60 seconds)
            last_update = entry_data.get("last_update")
            if last_update is None:
                return self._last_value

            # last_update is stored as an aware UTC datetime
            if datetime.now(timezone.utc) - last_update > timedelta(seconds=60):
                self._last_value = None
                return None
            
            if not meter_data.get("meterValue"):
                return self._last_value
            
            meter_value = meter_data["meterValue"][0]
            sampled_values = meter_value.get("sampledValue", [])
            
            # Extract values based on sensor type
            if self.sensor_type == "voltage":
                for sv in sampled_values:
                    if sv.get("measurand") == "Voltage" and not sv.get("phase"):
                        self._last_value = float(sv.get("value", 0))
                        return self._last_value
            
            elif self.sensor_type == "power":
                for sv in sampled_values:
                    if sv.get("measurand") == "Power.Active.Import":
                        self._last_value = float(sv.get("value", 0))
                        return self._last_value
            
            elif self.sensor_type == "energy":
                for sv in sampled_values:
                    if sv.get("measurand") == "Energy.Active.Import.Register":
                        self._last_value = float(sv.get("value", 0))
                        return self._last_value
            
            elif self.sensor_type == "current_l1":
                for sv in sampled_values:
                    if sv.get("measurand") == "Current.Import" and sv.get("phase") == "L1":
                        self._last_value = float(sv.get("value", 0))
                        return self._last_value
            
            elif self.sensor_type == "current_l2":
                for sv in sampled_values:
                    if sv.get("measurand") == "Current.Import" and sv.get("phase") == "L2":
                        self._last_value = float(sv.get("value", 0))
                        return self._last_value
            
            elif self.sensor_type == "current_l3":
                for sv in sampled_values:
                    if sv.get("measurand") == "Current.Import" and sv.get("phase") == "L3":
                        self._last_value = float(sv.get("value", 0))
                        return self._last_value
        
        except Exception as e:
            _LOGGER.error("Error extracting sensor value: %s", e)
        
        return self._last_value
