# teison_ct_clamp_hassio Component for Home Assistant

A custom Home Assistant component that listens for meter data via WebSocket and exposes power, voltage, and current readings as sensors.

## Features

- **WebSocket Server**: Listens for incoming meter data (OCPP-compatible format)
- **Sensor Entities**: Exposes readings as Home Assistant sensors
  - Voltage (V)
  - Power (W)
  - Energy (kWh)
  - Current L1, L2, L3 (A)
- **Real-time Updates**: Sensors update automatically when new meter data is received

## Installation

1. Install via HACS as a custom repository (Integration) or manually copy the `teison_ct_clamp_hassio` folder to your Home Assistant `custom_components` directory:
   ```
   ~/.homeassistant/custom_components/teison_ct_clamp_hassio
   ```

2. Restart Home Assistant

3. Go to Settings > Devices & Services > Create Integration and search for "teison_ct_clamp_hassio"

4. Configure the host (default `0.0.0.0`) and port (default `8080`)

## Data Format

The component expects OCPP-formatted WebSocket messages:

```json
[
  2,
  "unique-message-id",
  "MeterValues",
  {
    "connectorId": 1,
    "meterValue": [
      {
        "timestamp": "2025-12-11T00:10:20.000Z",
        "sampledValue": [
          {
            "value": "237.828",
            "context": "Sample.Periodic",
            "measurand": "Voltage",
            "location": "Inlet",
            "unit": "V"
          },
          {
            "value": "5.122",
            "context": "Sample.Periodic",
            "measurand": "Current.Import",
            "phase": "L1",
            "location": "Inlet",
            "unit": "A"
          },
          {
            "value": "0.852",
            "context": "Sample.Periodic",
            "measurand": "Current.Import",
            "phase": "L2",
            "location": "Inlet",
            "unit": "A"
          },
          {
            "value": "2.077",
            "context": "Sample.Periodic",
            "measurand": "Current.Import",
            "phase": "L3",
            "location": "Inlet",
            "unit": "A"
          },
          {
            "value": "1914.652",
            "context": "Sample.Periodic",
            "measurand": "Power.Active.Import",
            "location": "Inlet",
            "unit": "W"
          },
          {
            "value": "11.941",
            "context": "Sample.Periodic",
            "measurand": "Energy.Active.Import.Register",
            "location": "Inlet",
            "unit": "kWh"
          }
        ]
      }
    ]
  }
]
```

## Available Sensors

After setup, the following sensors will be available:

- `sensor.meter_voltage` - Voltage reading
- `sensor.meter_power` - Active power consumption
- `sensor.meter_energy` - Total energy consumed
- `sensor.meter_current_l1` - Phase L1 current
- `sensor.meter_current_l2` - Phase L2 current
- `sensor.meter_current_l3` - Phase L3 current

## Usage in Automations/Scripts

You can use these sensors in automations and templates:

```yaml
- alias: "Alert high power usage"
  trigger:
    platform: numeric_state
    entity_id: sensor.meter_power
    above: 3000
  action:
    service: notify.mobile_app_phone
    data:
      message: "Power usage is {{ state_attr('sensor.meter_power', 'native_value') }}W"
```

## Configuration

The component is configured via the Home Assistant UI. No YAML configuration is required.

## License

MIT
