# Instamart Customer Intelligence & Support Copilot

## Overview

This project builds a customer intelligence and support copilot using synthetic data. It includes data cleaning, customer segmentation, lapse prediction, ticket triage, policy question answering and refund processing.

## Reproduce

1. Clone the repository: `git clone https://github.com/javid-07/instamart-customer-copilot.git`
2. Enter the project directory: `cd instamart-customer-copilot`
3. Create a virtual environment using Python 3.11: `python -m venv .venv`
4. Activate the virtual environment in PowerShell: `.\.venv\Scripts\Activate.ps1`
5. Install dependencies: `python -m pip install -r requirements.txt`
6. Generate the synthetic data: `python generate_data.py`

Expected generator output:

`generated: customers=1200 products=40 orders_raw=13084 tickets=164`
