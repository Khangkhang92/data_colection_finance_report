#!/bin/bash

cd /media/computer/4e7b67c0-0b77-4ca9-9c68-0568856a766b/self/data_colection_finance_report

docker compose up -d 


source /home/computer/miniconda3/bin/activate data

python /media/computer/4e7b67c0-0b77-4ca9-9c68-0568856a766b/self/data_colection_finance_report/realtime.py > /media/computer/4e7b67c0-0b77-4ca9-9c68-0568856a766b/self/data_colection_finance_report/logfile.log 2>&1
