"""
import sys
sys.path.append('../schemas')

for p in sys.path:
    print(p)


python -m pip install -e .
"""

from schemas.mongo_schema import MongoManager
import pandas as pd
from tabulate import tabulate
from devtools import debug

df_f1 = pd.read_excel('army.xlsx'  , sheet_name='10001404'     ).iloc[4:,  :]
df_f2 = pd.read_excel('myself.xlsx', sheet_name='data'         ).iloc[2:,  :]
df_f3 = pd.read_excel('abra.xlsx'  , sheet_name='Eithan S Katz').iloc[10:, :]

df_f1.columns = df_f1.iloc[0, :]
df_f1 = df_f1.iloc[1:, :]
df_f1 = df_f1[['כניסה', 'יציאה', 'תאריך']]
df_f1.columns = ('h-in', 'h-out', 'date')
df_f1.dropna(inplace=True)
df_f1.reset_index(inplace=True, drop=True)

df_f1 = df_f1.astype(str)
df_f1['h-in' ] = df_f1['h-in' ] + ':00'
df_f1['h-out'] = df_f1['h-out'] + ':00'
df_f1['in' ] = df_f1.apply(lambda x: pd.to_datetime(f'{x["date"]} {x["h-in" ]}', format='%d/%m/%Y %H:%M:%S'), axis=1)
df_f1['out'] = df_f1.apply(lambda x: pd.to_datetime(f'{x["date"]} {x["h-out"]}', format='%d/%m/%Y %H:%M:%S'), axis=1)
df_f1 = df_f1[['in', 'out']]

#################################
df_f2.columns = df_f2.iloc[0, :]
df_f2 = df_f2.iloc[1:, :]
df_f2 = df_f2[['כניסה', 'יציאה', 'תאריך']]
df_f2.columns = ('h-in', 'h-out', 'date')
df_f2.dropna(inplace=True)
df_f2.reset_index(inplace=True, drop=True)

df_f2['date'] = df_f2['date'].apply(lambda x: x.strftime('%d/%m/%Y'))
df_f2 = df_f2.astype(str)
df_f2['in' ] = df_f2.apply(lambda x: pd.to_datetime(f'{x["date"]} {x["h-in" ]}', format='%d/%m/%Y %H:%M:%S'), axis=1)
df_f2['out'] = df_f2.apply(lambda x: pd.to_datetime(f'{x["date"]} {x["h-out"]}', format='%d/%m/%Y %H:%M:%S'), axis=1)
df_f2 = df_f2[['in', 'out']]

#################################
df_f3.columns = df_f3.iloc[0, :]
df_f3 = df_f3.iloc[1:, :]
df_f3 = df_f3[['סיום עבודה', 'תחילת עבודה', 'תאריך']]
df_f3.columns = ('out', 'in', 'date')
df_f3.dropna(inplace=True)
df_f3.reset_index(inplace=True, drop=True)


df_f3['h-in' ] = df_f3['in'  ].apply(lambda x: x.strftime('%H:%M:%S'))
df_f3['h-out'] = df_f3['out' ].apply(lambda x: x.strftime('%H:%M:%S'))
df_f3['date' ] = df_f3['date'].apply(lambda x: x.strftime('%d/%m/%Y'))
df_f3['in'   ] = df_f3.apply(lambda x: pd.to_datetime(f'{x["date"]} {x["h-in" ]}', format='%d/%m/%Y %H:%M:%S'), axis=1)
df_f3['out'  ] = df_f3.apply(lambda x: pd.to_datetime(f'{x["date"]} {x["h-out"]}', format='%d/%m/%Y %H:%M:%S'), axis=1)
df_f3 = df_f3[['in', 'out']]

#################################
def print_table(dff: pd.DataFrame, message: str)-> None:
    dff['in' ] = dff['in' ].dt.strftime('%d/%m/%Y %H:%M')
    dff['out'] = dff['out'].dt.strftime('%d/%m/%Y %H:%M')
    print(message)
    print(tabulate(dff, showindex=True, headers=['in', 'out']))
    return

mask = df_f2.ne(df_f1)
print_table(
    df_f2[mask].dropna(how='all', axis='columns').dropna(how='all', axis='rows'), message='diff from myself to army'
)

mask = df_f2.ne(df_f3)
dff = df_f2[mask].dropna(how='all', axis='columns').dropna(how='all', axis='rows')
print_table(
    df_f2[mask].dropna(how='all', axis='columns').dropna(how='all', axis='rows'), message='\n\ndiff from myself to abra'
)
