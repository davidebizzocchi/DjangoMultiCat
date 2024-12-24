#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Return value of the last command to exit with a n

docker compose logs -f
