import os
import json
import time
import keepa

'''
	Constants and global variables
'''

# Load environment variables

API_KEY = os.environ.get('KEEPA_API_KEY')

api = keepa.Keepa(API_KEY)

products = api.query('B07B428M7F')

keepa.plot_product(products[0])

# show the plot
keepa.plt.show()