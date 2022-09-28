import pandas as pd
import numpy as np

# choose file (file picker?)
# report = input(enter path to this weeks report:)
report = 'sample_report.csv'

report_data = pd.read_csv(report)
lookup = pd.read_csv('sku_replacement.csv')




# merge (vlookup) from lookup.csv:

qb_merged = report_data.merge(lookup, how='left', on='sku')
# check for errors (😬)
# add new replacement sku to sku_replacement.csv for next time

# new sku and multiplier:
# print(qb_merged.head(30))

# multiply qty by multiplier

qb_merged['new qty'] = qb_merged['quantity'] * qb_merged['mulipier']

# print(qb_merged.head(30))

# set all negative adjustments as refund type

# pivot report_data on new sku, total new qty, total price

pivot = pd.pivot_table(qb_merged, index=['type', 'qb_sku'], values=['new qty', 'total'], aggfunc=np.sum)
# print(pivot)

# any skus of type order and of marketplace Ebay must be deducted from qty (not price total)

# export properly formatted invoice as per qb requirements


pivot.to_csv('invoice.csv')

# export credit memo of all returns and fees to be entered manually (💩)


