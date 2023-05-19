#!/usr/bin/env python
# encoding: utf-8

import re
import pandas as pd
from bson import ObjectId
from random import randint, randrange

##########################################################################
password_regex = "((?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{6,64})"

##########################################################################
print(randint  (100000,  999999))  # randint is inclusive at both ends
print(randrange(100000, 1000000))  # randrange is exclusive at the stop
quit()

o = '64317b23fd407fb04b25b241'
print(ObjectId.is_valid('yochecved'))

x1 = '12.1.22'
x2 = '12/1/2022'

j1 = pd.to_datetime(re.sub(r'(\.|/)', '-', x1), format='%d-%m-%y').strftime('%Y-%m-%d')
j2 = pd.to_datetime(re.sub(r'(\.|/)', '-', x2), format='%d-%m-%Y').strftime('%Y-%m-%d')



