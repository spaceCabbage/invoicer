import pandas as pd
import numpy as np

# ? choose file

# @(file picker?)
#  report = input(enter path to this weeks report:)

report = 'sample_report.csv'

report_data = pd.read_csv(report)
lookup = pd.read_csv('sku_replacement.csv')


# ? get all skus that are not found in lookup df

er_df = report_data.merge(lookup, how='outer', on='sku', indicator=True)

er_df = er_df[er_df['_merge'] == 'left_only']

er_df = er_df.drop_duplicates(subset='sku')


# @ fix missing skus
def ercheck():
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
        new_skus.to_csv('sku_replacement.csv', mode='a', index=False, header=False)
        

    elif confirm == 'n':
        # check for typos and try again
        print('OK lets try this again:')
        print('-------------------')
        print('---- ATTEMPT 2 ----') 
        print('-------------------')
        ercheck()
    
ercheck()   
    
# @ add new replacement sku to sku_replacement.csv for next time

def append_new_sku(newsku, multiplier):
    newsku = newsku
    multiplier = multiplier
    
    
# ? get correct skus from lookup df

qb_merged = report_data.merge(lookup, how='left', on='sku')



# ? new sku and multiplier:

# multiply qty by multiplier

qb_merged['new qty'] = qb_merged['quantity'] * qb_merged['multiplier']

# print(qb_merged.head(30))


# @ set all negative adjustments as type refund


# @ set all order skus starting wiht "amzn.gr." as type "GR"




# ? pivot report_data on new sku, total new qty, total price

pivot = pd.pivot_table(qb_merged, index=['type', 'qb_sku'], values=['new qty', 'total'], aggfunc=np.sum)
# print(pivot)




# @ deduct ebay order qty from total qty (leave total price)



# ? export properly formatted invoice as per qb requirements

# pivot.to_csv('invoice.csv')



# @ export credit memo of all returns and fees to be entered manually (💩)


