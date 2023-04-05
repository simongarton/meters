
# run this script to set up the Tempest server

echo
echo 'Running Tempest server ...'
echo

cd /home/pi/tempest
export FLASK_RUN_PORT=8002
flask run --host 0.0.0.0
