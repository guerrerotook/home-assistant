"""Constants for the the iberdrola component."""
from datetime import timedelta

DOMAIN = "iberdrola"
UPDATE_INTERVAL = timedelta(seconds=30)
COMPONENTS = {"sensor": "sensor"}
SIGNAL_STATE_UPDATED = "{}.updated".format(DOMAIN)
