#!/bin/bash
cd /home/kavia/workspace/code-generation/fastweatherqwik-842-d3b63b13/weather_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

