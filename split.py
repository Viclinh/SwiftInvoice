import json
import requests 
import sys 
import os
from time import sleep 
import zipfile 
import io

with open('config.json', 'r') as f:
    config = json.load(f)

CLIENT_ID = config['client_id']
CLIENT_SECRET = config['client_secret']
HOST = config['host']

NUM_PAGES_FOR_PREVIEW = 3

# Find PDF files in inputfilessplit folder
pdf_files = [f for f in os.listdir('inputfilessplit') if f.lower().endswith('.pdf')]
if not pdf_files:
    print("No PDF files found in inputfilessplit folder")
    sys.exit()
SOURCE_PDF = pdf_files[0]
print(f"Processing file: {SOURCE_PDF}")

def uploadDoc(path, id, secret):
	
	headers = {
		"client_id":id,
		"client_secret":secret
	}

	with open(path, 'rb') as f:
		files = {'file': f}

		request = requests.post(f"{HOST}/pdf-services/api/documents/upload", files=files, headers=headers)
		return request.json()


def splitPDF(doc, count, id, secret):
	
	headers = {
		"client_id":id,
		"client_secret":secret,
		"Content-Type":"application/json"
	}

	body = {
		"documentId":doc,
		"pageCount":count
	}

	request = requests.post(f"{HOST}/pdf-services/api/documents/modify/pdf-split", json=body, headers=headers)
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

def getResult(doc, id, secret):
	
	headers = {
		"client_id":id,
		"client_secret":secret
	}

	return requests.get(f"{HOST}/pdf-services/api/documents/{doc}/download", headers=headers).content


doc = uploadDoc(f"inputfilessplit/{SOURCE_PDF}", CLIENT_ID, CLIENT_SECRET)
print(f"Uploaded {SOURCE_PDF} to Foxit")

task = splitPDF(doc["documentId"], NUM_PAGES_FOR_PREVIEW, CLIENT_ID, CLIENT_SECRET)
print(f"Started split operation")

result = checkTask(task["taskId"], CLIENT_ID, CLIENT_SECRET)
print(f"Done with split")

bits = getResult(result["resultDocumentId"],  CLIENT_ID, CLIENT_SECRET)
zf = zipfile.ZipFile(io.BytesIO(bits), "r")

firstEntry = zf.infolist()[0]

with zf.open(firstEntry) as pdf:
	with open(f"Split_Output/{SOURCE_PDF}", "wb") as output:
		output.write(pdf.read())

print("Done")
		
