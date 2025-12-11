"""Config flow for Meter Values."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

DOMAIN = "teison_ct_clamp_hassio"

class MeterValuesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meter Values."""
    
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # Validate the input
            host = user_input.get(CONF_HOST, "0.0.0.0")
            port = user_input.get(CONF_PORT, 12345)
            
            return self.async_create_entry(
                title=f"Meter Values ({host}:{port})",
                data=user_input
            )
        
        # Show form
        data_schema = vol.Schema({
            vol.Required(CONF_HOST, default="0.0.0.0"): str,
            vol.Required(CONF_PORT, default=12345): int,
        })
        
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this config entry."""
        return MeterValuesOptionsFlow(config_entry)

class MeterValuesOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Meter Values."""
    
    def __init__(self, config_entry):
        """Initialize."""
        self.config_entry = config_entry
    
    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_abort(reason="success")
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({})
        )
