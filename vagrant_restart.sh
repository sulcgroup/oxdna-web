#!/bin/bash
echo "Running main.py"
pkill gunicorn
cd /vagrant/oxdna-web
t=`date | tr -s ' ' | cut -d ' ' -f 2,3,4 | sed 's/ /_/g'`
mv nohup.out logs/$t
sh start.sh
chmod 664 nohup.out
