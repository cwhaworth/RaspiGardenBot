export FLASK_APP=/var/www/RaspiGardenBot/FlaskStart.py
# export FLASK_DEBUG=0
unset FLASK_DEBUG
python3 -m flask run --host=192.168.86.166 &
