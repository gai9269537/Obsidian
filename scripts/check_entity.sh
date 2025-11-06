#!/usr/bin/env bash
# Check a DataHub dataset entity by URN
# Usage: ./check_entity.sh <dataset_name> [--aspects <aspect1,aspect2>]
#   dataset_name: Name portion of the URN (e.g., "obsidian.Kha.Python")
#   --aspects: Optional comma-separated list of aspects to fetch (e.g., ownership,schema)

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

# Handle aspects parameter
ASPECTS=""
if [ "$2" = "--aspects" ] && [ -n "$3" ]; then
    ASPECTS="&aspects=$(echo $3 | tr ',' '&aspects=')"
fi

# Print UI and API URLs
echo "DataHub UI URL:"
echo "  $DATAHUB_UI/entity?urn=$ENC_URN"
echo
echo "DataHub GMS API URL:"
echo "  $DATAHUB_GMS/v2/datasets/$ENC_URN"
echo

# Fetch entity from GMS API (with GraphQL fallback for domain lookups)
echo "Fetching entity from GMS..."
if [ -n "$3" ]; then
    # Fetch specific aspects
    for aspect in $(echo $3 | tr ',' ' '); do
        echo "Fetching aspect: $aspect"
        # Special-case domains: v2 aspect read often returns 404; use GraphQL for reliable domain lookup
        if [ "$aspect" = "domains" ] || [ "$aspect" = "domain" ]; then
            # call helper Python script to query GraphQL and pretty-print result
            python3 "$(dirname "$0")/check_domain.py" "$URN" "$DATAHUB_GMS" || true
        else
            # Try v2 endpoint first; if it returns 404, fall back to GraphQL domain lookup when appropriate
            HTTP_STATUS=$(curl -s -o /tmp/check_entity_out.json -w "%{http_code}" -H "Accept: application/json" "$DATAHUB_GMS/v2/datasets/$ENC_URN/aspects/$aspect")
            if [ "$HTTP_STATUS" = "200" ]; then
                cat /tmp/check_entity_out.json | python3 -m json.tool
            else
                echo "v2 GET returned status $HTTP_STATUS for aspect $aspect"
                if [ "$aspect" = "domains" ] || [ "$aspect" = "domain" ]; then
                    python3 "$(dirname "$0")/check_domain.py" "$URN" "$DATAHUB_GMS" || true
                else
                    cat /tmp/check_entity_out.json || true
                fi
            fi
        fi
        echo
    done
else
    # Fetch full entity
    curl -s -H "Accept: application/json" "$DATAHUB_GMS/v2/datasets/$ENC_URN" | python3 -m json.tool
fi

# Check response
if [ $? -eq 0 ]; then
    echo -e "\nSuccess! Entity found."
else
    echo -e "\nError: Could not fetch entity or invalid response."
    exit 1
fi