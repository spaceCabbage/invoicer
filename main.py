import pandas as pd
import numpy as np
import easygui


# ? choose file

#GUI file picker
#report = easygui.fileopenbox()

report = 'sample_report.csv'

report_data = pd.read_csv(report)
lookup = pd.read_csv('sku_replacement.csv')

#! date picker
date_start = '4/4/2020'
date_end = '4/10/2020'

# ? get all skus that are not found in lookup df

er_df = report_data.merge(lookup, how='outer', on='sku', indicator=True)

er_df = er_df[er_df['_merge'] == 'left_only']

er_df = er_df.drop_duplicates(subset='sku')


# ? fix missing skus in lookup df

def ercheck(lookup):
    print('the following skus cannot be placed')
    print(er_df.sku)
    print('-------------------')

    new_skus = pd.DataFrame({
        'sku': [],
        'qb_sku': [],
        'multiplier': [],
    })


    for index, row in er_df.iterrows():
        ersku = row['sku']
        default_multiplier = 1
        
        newsku = input('enter correct sku for ' + ersku + ' as per QB\n')
        newmultiplier = input('enter product multiplier (leave blank for single packs): ') or default_multiplier
        
        print('-------------------')
        
        print('for sku ' + "\x1B[1;4m" + ersku + "\x1B[0m" + ' youve entered:\n' 'New SKU: ' + newsku + '\n' + 'Multiplier: ' + str(newmultiplier))
        
        print('-------------------')
        
        #add to newskus df
        new_skus = new_skus.append({'sku': ersku, 'qb_sku': newsku, 'multiplier': newmultiplier}, ignore_index=True)

    print(new_skus)
    confirm = input('does this look correct? (enter y/yes or n/no)\n')

    if confirm == 'y':
        print('CONFIRMED!\nAdding these rows to the lookup table for next time')
        # add df of new skus to lookup.csv
        #new_skus.to_csv('sku_replacement.csv', mode='a', index=False, header=False)
        lookup = lookup.append(new_skus, ignore_index=True)
        print('--------------------')


    elif confirm == 'n':
        # check for typos and try again
        print('OK lets try this again:')
        print('-------------------')
        print('---- ATTEMPT 2 ----') 
        print('-------------------')
        ercheck()
    
ercheck(lookup)   
    

    
# ? get correct skus from lookup df
#gotta figure out how to also lookup from the new_skus df too
qb_merged = report_data.merge(lookup, how='left', on='sku')


# ? multiply qty by multiplier

qb_merged['new qty'] = qb_merged['quantity'] * qb_merged['multiplier']


# ? set all negative adjustments as type refund

for index, row in qb_merged.iterrows():
    if row['type'] == 'Adjustment':
        if row['total'] < 0:
            qb_merged.at[index, 'type'] = 'Refund'
            print(row['sku'] + ' changed to refund')
            

# ? set all ORDER! skus starting with "amzn.gr." as type "GR"

for index, row in qb_merged.iterrows():
    if row['sku'].startswith('amzn.gr.'):
        if row['type'] == 'Order':
            qb_merged.at[index, 'type'] = 'G&R'
            print(row['sku'] + ' changed to G&R')
            
#! parse g&r skus to get proper skus


# ? pivot report_data on new sku, total new qty, total price

pivot = pd.pivot_table(qb_merged, index=['type', 'qb_sku'], values=['new qty', 'total'], aggfunc=np.sum)
pivot = pivot.reset_index()
print(pivot)

# dfs for each report to be exported as csv's
# they each need a col for
#'invoice No.', 'Customer', 'Invoice Date', 'Memo', 'Product/Service', 'Qty', 'Amount'
# customer, date, and memo only th efirst line should be filled
# the onvoice number should be 1001+ for all of them

#@ sales df

salesdf = pd.DataFrame({
        'Invoice No.': [],
        'Customer': [],
        'Invoice Date': [],
        'Memo': [],
        'Product/Service': [],
        'Qty': [],
        'Amount': [],
    })
print(pivot)
for index, row in pivot.iterrows():
    sku = row['qb_sku']
    qty = row['new qty']
    amount = row['total']
    if row['type'] == 'Order':
        salesdf = salesdf.append({
            'Invoice No.': int(1001),
            'Customer': 'Amazon',
            'Invoice Date': date_end,
            'Memo': f'Sales {date_start} - {date_end}',
            'Product/Service': sku,
            'Qty': int(qty),
            'Amount': amount,
            }, ignore_index=True)
        
print(salesdf)

#! deduct ebay order qty from total qty (leave total price)


#@ adjustments df

adjustmentsdf = pd.DataFrame({
        'Invoice No.': [],
        'Customer': [],
        'Invoice Date': [],
        'Memo': [],
        'Product/Service': [],
        'Qty': [],
        'Amount': [],
    })

for index, row in pivot.iterrows():
    sku = row['qb_sku']
    qty = row['new qty']
    amount = row['total']
    if row['type'] == 'Adjustment':
        salesdf = salesdf.append({
            'Invoice No.': int(1002),
            'Customer': 'Amazon',
            'Invoice Date': date_end,
            'Memo': f'Adjustments {date_start} - {date_end}',
            'Product/Service': sku,
            'Qty': int(qty),
            'Amount': amount,
            }, ignore_index=True)
        
print(adjustmentsdf)

#@ G&R and liquidations 

grdf = pd.DataFrame({
        'Invoice No.': [],
        'Customer': [],
        'Invoice Date': [],
        'Memo': [],
        'Product/Service': [],
        'Qty': [],
        'Amount': [],
    })

for index, row in pivot.iterrows():
    sku = row['qb_sku']
    qty = row['new qty']
    amount = row['total']
    if row['type'] == 'G&R' or row['type'] == 'Liquidation':
        salesdf = salesdf.append({
            'Invoice No.': int(1003),
            'Customer': 'Amazon',
            'Invoice Date': date_end,
            'Memo': f'Sales {date_start} - {date_end}',
            'Product/Service': sku,
            'Qty': int(qty),
            'Amount': amount,
            }, ignore_index=True)
        
print(grdf)

#! refunds and fees

refundsdf = pd.DataFrame({
        'Invoice No.': [],
        'Customer': [],
        'Invoice Date': [],
        'Memo': [],
        'Product/Service': [],
        'Qty': [],
        'Amount': [],
    })






#@ export properly formatted invoice as per qb requirements

# pivot.to_csv('invoice.csv')
print('--------------------')
print('Invoice successfully saved!')


# @ export credit memo of all returns and fees to be entered manually (💩)

# jeez i haven't even bothered with this yet