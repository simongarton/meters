
# run this script to set up the Tempest server

echo
echo 'Running Tempest server ...'
echo

export FLASK_RUN_PORT=8002
flask run --host 0.0.0.0
