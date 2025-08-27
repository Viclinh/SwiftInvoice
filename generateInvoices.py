import requests
import sys 
import base64 
import json 

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

CLIENT_ID = config['client_id']
CLIENT_SECRET = config['client_secret']
HOST = config['host']

def docGen(doc, data, id, secret):
	
	headers = {
		"client_id":id,
		"client_secret":secret
	}

	body = {
		"outputFormat":"pdf",
		"documentValues": data,  
		"base64FileString":doc
	}

	request = requests.post(f"{HOST}/document-generation/api/GenerateDocumentBase64", json=body, headers=headers)

	return request.json()

with open('invoice.docx', 'rb') as file:
	bd = file.read()
	b64 = base64.b64encode(bd).decode('utf-8')

with open('invoicedata.json', 'r') as file:
	data = json.load(file)

for invoiceData in data:
	# Add alternative field names for addresses if they exist
	if 'billingAddress' in invoiceData:
		invoiceData['billing_address'] = invoiceData['billingAddress']
		invoiceData['BillingAddress'] = invoiceData['billingAddress']
	if 'shippingAddress' in invoiceData:
		invoiceData['shipping_address'] = invoiceData['shippingAddress']
		invoiceData['ShippingAddress'] = invoiceData['shippingAddress']
	
	result = docGen(b64, invoiceData, CLIENT_ID, CLIENT_SECRET)

	if result["base64FileString"] == None:
		print("Something went wrong.")
		print(result)
		sys.exit()

	b64_bytes = result["base64FileString"].encode('ascii')
	binary_data = base64.b64decode(b64_bytes)

	filename = f"invoice_account_{invoiceData["accountNumber"]}.pdf"

	with open(filename, 'wb') as file:
		file.write(binary_data)
		print(f"Done and stored to {filename}")