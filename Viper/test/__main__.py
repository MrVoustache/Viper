"""
Launches all the test in the Viper test suite.
"""

import argparse
from . import run_all, warning, set_level, WARNING, INFO, DEBUG




parser = argparse.ArgumentParser("Viper.test", description="Runs all tests of the Viper library.")

parser.add_argument("--verbosity", "-v", action="count", default=0, help="Increases the verbosity of the output.")

args = parser.parse_args()

set_level([WARNING, INFO, DEBUG][args.verbosity])
warning("Running all Viper tests...")

run_all()