#!/bin/bash

cd /home/shota72fx/data_colection_finance_report
#docker compose up -d 

source /home/shota72fx/miniconda3/bin/activate data


python /home/shota72fx/data_colection_finance_report/market_metion.py > /home/shota72fx/data_colection_finance_report/market_metion.log 2>&1
python /home/shota72fx/data_colection_finance_report/posts.py > /home/shota72fx/data_colection_finance_report/posts.log 2>&1
