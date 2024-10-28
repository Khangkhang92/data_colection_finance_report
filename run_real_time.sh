#!/bin/bash

cd /home/shota72fx/data_colection_finance_report

# docker compose up -d 


source /home/shota72fx/miniconda3/bin/activate data

python /home/shota72fx/data_colection_finance_report/realtime_daily.py > /home/shota72fx/data_colection_finance_report/logs/realtime.log 2>&1

