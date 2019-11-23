"""
CANNIBALIZATION

Gerard Mazi
gerard.mazi@gmail.com
862-221-2477
"""

import pandas as pd
import numpy as np
import os
import glob

###################################################################
# Import files
files = glob.glob(
    os.path.join(
        r'C:\Users\gmazi\Desktop\Deposit Modeling\cannibal',
        "*.csv"
    )
)

dep = pd.concat(
    pd.read_csv(
        f,
        parse_dates=['Full Date'],
        usecols=[
            'Full Date',
            'Prmy Cust Number',
            'Account Instrument Int Plan Desc',
            'Account Ledger Balance',
            'Account Closed Reason Code'
        ],
        low_memory=False
    ) for f in files
)
dep.columns = ['Date', 'Cust', 'Product', 'Balance', 'Status']

###################################################################
# Save and load data
dep.to_pickle('dep.pkl')
#dep = pd.read_pickle('dep.pkl')

# Declare variables
from_prod = 'MONEY MARKET SPECIAL'
to_prod = 'PROMOTIONAL PLUS MMA'
prior = dep['Date'].min()
current = dep['Date'].max()

###################################################################
# Subset data of interest
dep = dep.loc[
    (dep['Product'].isin([from_prod, to_prod])
     ) & (dep['Status'] == ' '),
    ['Date', 'Cust', 'Product', 'Balance']
]

##################################################################
# From table
from_table = pd.DataFrame(
    {
        'Cust': pd.unique(
            dep.loc[dep['Product'] == from_prod, 'Cust']
        ),
        'From': from_prod
    }
)

##################################################################
# To table
to_table = pd.DataFrame(
    {
        'Cust': pd.unique(
            dep.loc[dep['Product'] == to_prod, 'Cust']
        ),
        'To': to_prod
    }
)

##################################################################
# Lookup table
lookup = dep.groupby(
    ['Cust', 'Product', 'Date']
)['Balance'].sum().unstack().reset_index()

# Set NaN to 0
lookup.loc[lookup[prior].isnull(), prior] = 0
lookup.loc[lookup[current].isnull(), current] = 0

# Month over month balance change
lookup['Delta'] = lookup[current] - lookup[prior]

# Import From product
lookup = pd.merge(lookup, from_table, how='left', on='Cust')

# Import To product
lookup = pd.merge(lookup, to_table, how='left', on='Cust')

#################################################################
# Final lookup table
final = lookup[
    (~lookup['From'].isnull()) & (~lookup['To'].isnull())
]


retain_delta = final.groupby(
    ['Cust', 'Product']
)['Delta'].sum().unstack().reset_index()

retain_prior = final.groupby(
    ['Cust', 'Product']
)[prior].sum().unstack().reset_index().iloc[:,[0,1]]

retain_recent = final.groupby(
    ['Cust', 'Product']
)[current].sum().unstack().reset_index().iloc[:,[0,2]]

retain = pd.merge(
    retain_delta,
    retain_prior,
    how='left',
    on='Cust',
    suffixes=['_Delta', '_Bal']
)

retain = pd.merge(
    retain,
    retain_recent,
    how='left',
    on='Cust',
    suffixes=['_Delta', '_Bal']
)

retain['Test_Neg'] = (retain['MONEY MARKET SPECIAL_Delta'] < 0) & \
                     (retain['PROMOTIONAL PLUS MMA_Delta'] > 0)

retain['Test_Int'] = retain['PROMOTIONAL PLUS MMA_Delta'] > \
                     (retain['PROMOTIONAL PLUS MMA_Bal'] *
                      0.025 / 12)

retain = retain[
    (retain['Test_Neg'] == 1) & (retain['Test_Int'] == 1)
]

retain['Flow'] = np.minimum(
    retain['MONEY MARKET SPECIAL_Delta'] * -1,
    retain['PROMOTIONAL PLUS MMA_Delta']
)

print(retain['Flow'].sum())