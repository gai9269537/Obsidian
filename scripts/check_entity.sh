#!/usr/bin/env bash
# Check a DataHub dataset entity by URN
# Usage: ./check_entity.sh <dataset_name>
#   dataset_name: Name portion of the URN (e.g., "obsidian.Kha.Python")

# Exit on any error
set -e

# DataHub endpoints
: "${DATAHUB_GMS:=http://localhost:8080}"
: "${DATAHUB_UI:=http://localhost:9002}"

if [ -z "$1" ]; then
    echo "Usage: $0 <dataset_name>"
    echo "Example: $0 obsidian.Kha.Python"
    exit 1
fi

# Construct and encode the URN
DATASET_NAME="$1"
URN="urn:li:dataset:(urn:li:dataPlatform:obsidian,$DATASET_NAME,PROD)"
ENC_URN=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$URN")

# Print UI and API URLs
echo "DataHub UI URL:"
echo "  $DATAHUB_UI/entity?urn=$ENC_URN"
echo
echo "DataHub GMS API URL:"
echo "  $DATAHUB_GMS/entities?urn=$ENC_URN"
echo

# Fetch entity from GMS API
echo "Fetching entity from GMS..."
curl -s -H "Accept: application/json" "$DATAHUB_GMS/entities?urn=$ENC_URN" | python3 -m json.tool