#!/bin/bash

cd /home/shota72fx/data_colection_finance_report
#docker compose up -d 

source /home/shota72fx/miniconda3/bin/activate data


python /home/shota72fx/data_colection_finance_report/market_mention.py > /home/shota72fx/data_colection_finance_report/logs/market_mention.log 2>&1
python /home/shota72fx/data_colection_finance_report/posts.py > /home/shota72fx/data_colection_finance_report/logs/posts.log 2>&1
python /home/shota72fx/data_colection_finance_report/update_quote.py > /home/shota72fx/data_colection_finance_report/logs/update_quote.log 2>&1
