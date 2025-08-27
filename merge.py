import os
import requests 
import sys 
import json
from time import sleep 

# Load credentials from config file
with open('config.json', 'r') as f:
    config = json.load(f)

CLIENT_ID = config['client_id']
CLIENT_SECRET = config['client_secret']
HOST = config['host']

# Find PDF files in source folder
source_pdf_files = [f for f in os.listdir('./source') if f.lower().endswith('.pdf')]
if not source_pdf_files:
    print("No PDF files found in source folder")
    sys.exit()
BOILERPLATE_PDF = f"./source/{source_pdf_files[0]}"
print(f"Found boilerplate file: {source_pdf_files[0]}")

# Find PDF files in inputfiles folder
input_pdf_files = [f for f in os.listdir('./inputfiles') if f.lower().endswith('.pdf')]
if not input_pdf_files:
    print("No PDF files found in inputfiles folder")
    sys.exit()
SOURCE_PDF = input_pdf_files[0]
print(f"Found input file: {SOURCE_PDF}")

def uploadDoc(path, id, secret):
	
	headers = {
		"client_id":id,
		"client_secret":secret
	}

	with open(path, 'rb') as f:
		files = {'file': f}

		request = requests.post(f"{HOST}/pdf-services/api/documents/upload", files=files, headers=headers)
		return request.json()


def combinePDF(docs, id, secret, level="MEDIUM"):
	
	headers = {
		"client_id":id,
		"client_secret":secret,
		"Content-Type":"application/json"
	}

	body = {
		"documentInfos": docs
	}

	request = requests.post(f"{HOST}/pdf-services/api/documents/enhance/pdf-combine", json=body, headers=headers)
	return request.json()

def checkTask(task, id, secret):

	headers = {
		"client_id":id,
		"client_secret":secret,
		"Content-Type":"application/json"
	}

	done = False
	while done is False:

		request = requests.get(f"{HOST}/pdf-services/api/tasks/{task}", headers=headers)
		status = request.json()
		if status["status"] == "COMPLETED":
			done = True
			# really only need resultDocumentId, will address later
			return status
		elif status["status"] == "FAILED":
			print("Failure. Here is the last status:")
			print(status)
			sys.exit()
		else:
			print(f"Current status, {status['status']}, percentage: {status['progress']}")
			sleep(5)

def downloadResult(doc, path, id, secret):
	
	headers = {
		"client_id":id,
		"client_secret":secret
	}

	with open(path, "wb") as output:
		
		bits = requests.get(f"{HOST}/pdf-services/api/documents/{doc}/download", stream=True, headers=headers).content 
		output.write(bits)

doc1 = uploadDoc(BOILERPLATE_PDF, CLIENT_ID, CLIENT_SECRET)
print(f"Uploaded boilerplate pdf to Foxit")

doc2 = uploadDoc(f"./inputfiles/{SOURCE_PDF}", CLIENT_ID, CLIENT_SECRET)
print(f"Uploaded input pdf to Foxit")

task = combinePDF([doc1, doc2], CLIENT_ID, CLIENT_SECRET)
print(f"Started combine operation")

result = checkTask(task["taskId"], CLIENT_ID, CLIENT_SECRET)
print(f"Done with combine")

downloadResult(result["resultDocumentId"], f"./Merged_Output/{SOURCE_PDF}", CLIENT_ID, CLIENT_SECRET)
print("Done and saved")

