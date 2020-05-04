#!/bin/bash
echo "Running main.py"
pkill -F /var/tmp/python.pid
cd /var/www/azDNA/azDNA
t=`date | tr -s ' ' | cut -d ' ' -f 2,3,4 | sed 's/ /_/g'`
mv nohup.out logs/$t
nohup python3 /var/www/azDNA/azDNA/main.py &
echo $! > /var/tmp/python.pid
chmod 664 nohup.out
