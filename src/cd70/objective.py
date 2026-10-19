"""Which fuel number the optimiser, sensitivity analysis, robustness check, figures and paper use.

The value is set in config/optimiser.yaml. Every module imports FUEL_KEY from here, so there is one definition.
"""

from cd70 import config

_OPT = config.optimiser()
FUEL_KEY = str(_OPT["fuel_metric"])
FUEL_LABEL = str(_OPT["fuel_label"])
