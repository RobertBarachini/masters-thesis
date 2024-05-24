# NOTE: Doesn't work. Amazon API no longer supports the Product Advertising API (PAAPI) 5.0. Use the Amazon Associates API instead - applied but not yet approved.

# CamelCamelCamel uses ASINs to identify products. Find a way to link/search all indexed products from Pangoly to CamelCamelCamel.
# Use rapidfuzz to find the closest match between the product name and the product name on CamelCamelCamel.???

import os
from typing import Optional
import boto3
from botocore.client import BaseClient
from dotenv import load_dotenv

load_dotenv()

AWS_REGION_DEFAULT = os.getenv('AWS_REGION_DEFAULT', 'eu-central-1')


def get_amazon_client(
    service_name: str = 'apai',
    region_name: str = AWS_REGION_DEFAULT
) -> Optional[boto3.Session]:  #Optional[BaseClient]:
	'''
		Args:
			client_type (str): The type of client to create. Valid values are: 'apapi', 'product_advertising', 'paapi'.
			region_name (str): The region name to use for the client.

		Returns:
			Amazon client object.
	'''

	# Set up the Product Advertising API client
	amazon = boto3.client(
	    service_name,  # 'apapi',
	    region_name='eu-central-1',
	    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
	    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))

	return amazon  # type: ignore


amazon = get_amazon_client()
assert amazon

# Search for a product and retrieve its information
response = amazon.search_items(Keywords='amd ryzen 7 2700x',
                               SearchIndex='Electronics',
                               Resources=[
                                   'Images.Primary.Small', 'ItemInfo.Title',
                                   'Offers.Listings.Price'
                               ])

# Print the product details
for item in response['SearchResult']['Items']:
	print(f"Title: {item['ItemInfo']['Title']['DisplayValue']}")
	print(f"Price: {item['Offers']['Listings'][0]['Price']['DisplayAmount']}")
	print(f"Image URL: {item['Images']['Primary']['Small']['URL']}\n")

if __name__ == "__main__":
	print("ALL DONE")