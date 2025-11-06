# Start DataHub using quickstart
python3 -m pip install --upgrade pip wheel setuptools
python3 -m pip install --upgrade acryl-datahub
datahub version

# Wait for all services to start (usually takes a few minutes)
docker ps

datahub docker quickstart