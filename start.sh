# sass /var/www/RaspiGardenBot/static/scss/styles.scss /var/www/RaspiGardenBot/static/css/styles.css
export FLASK_APP=/var/www/RaspiGardenBot/FlaskStart.py
# export FLASK_DEBUG=0
unset FLASK_DEBUG
export FLASK_ENV=production
flask assets build
python3 -m flask run --host=192.168.86.166 &
