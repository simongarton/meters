
# run this script to set up the meter agent as something that can respond to calls
# as well as update data - so redials, config changes etc.

# I have disabled this on kili, as it uses meter.py, not meter_pico.py, which is
# is drifting out of sync.

# there was also a meter.sh which ran meter.py just once, also deleted.

echo
echo 'Running meter agent ...'
echo

export FLASK_RUN_PORT=8001
flask run --host 0.0.0.0
