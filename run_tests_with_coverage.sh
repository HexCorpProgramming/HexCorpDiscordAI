# Terminate with error if any test fails.
set -e

# Run the unit tests and record coverage data.
python -m coverage run --source=. --omit=test/*,env/* -m unittest

# Produce a coverage report as HTML in "./htmlcov/index.html".
python -m coverage html
