#!/bin/sh

cd ..
pybabel extract -F ./babel.cfg -o ./locale/messages.pot ./

pybabel update -l it -d ./locale -i ./locale/messages.pot -N

pybabel update -l en -d ./locale -i ./locale/messages.pot -N

pybabel update -l de -d ./locale -i ./locale/messages.pot -N

pybabel update -l en_GB -d ./locale -i ./locale/messages.pot -N

pybabel compile -f -d ./locale
