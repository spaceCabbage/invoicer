import pandas as pd
import numpy as np

# choose file 
# report = input(enter path to this weeks report:)
report = 'sample_report.csv'

report_data = pd.read_csv(report)
lookup = pd.read_csv('sku_replacement.csv')
name = "yehuda"

# merge (vlookup) from lookup.csv
# new sku and multiplier

# check for errors (😬)

# add new replacement sku to sku_replacement.csv for next time

# multiply qty by multiplier

# set all negative adjustments as refund type

# pivot report_data on new sku, total new qty, total price

# any skus of type order and of marketplace Ebay must be deducted from qty (not price total)

# export properly formatted invoice as per qb requirements

# export credit memo of all returns and fees to be entered manually (💩)


