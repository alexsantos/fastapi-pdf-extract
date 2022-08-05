import os
import secrets

from fastapi import FastAPI, UploadFile, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pdfminer.pdfparser import PDFSyntaxError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import pdfextract

app = FastAPI()
templates = Jinja2Templates(directory="templates/")
app.mount("/static", StaticFiles(directory="static"), name="static")
security = HTTPBasic()

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1vB_eHMVn1yIQ3K8RyEMMo-SM71AAtwKwQh3VZ_E5ZrA'
SAMPLE_RANGE_NAME = 'Folha1!A:G'


def append_values(values):
    print(f"Nº de resultados a inserir: {len(values)}")
    resource = {
        "majorDimension": "ROWS",
        "values": values
    }
    try:
        service = build('sheets', 'v4')

        # Call the Sheets API
        sheet = service.spreadsheets()
        request = sheet.values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                        range=SAMPLE_RANGE_NAME,
                                        valueInputOption="USER_ENTERED",
                                        body=resource)
        response = request.execute()
        print(response)
        return {"result": "Dados inseridos na Google Sheet com Sucesso."}
    except HttpError as e:
        print(e.reason)
        return {"result": "Erro", "message": e.reason}


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "larafernandes")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/", response_class=HTMLResponse)
async def main(request: Request, username: str = Depends(get_current_username)):
    print(f"Username: {username}")
    return templates.TemplateResponse('form.html', context={'request': request})


@app.post("/", response_class=HTMLResponse)
async def create_upload_file(request: Request, files: list[UploadFile], username: str = Depends(get_current_username)):
    response = []
    values_list = list()
    for file in files:
        try:
            result = pdfextract.compute(file.file)
            values_list.extend(result)
            response.append({"filename": file.filename, "result": "Ficheiro convertido com Sucesso."})
        except PDFSyntaxError:
            response.append({"filename": file.filename, "result": "Erro", "message": "Not a valid PDF"})
    if len(values_list) > 0:
        response.append(append_values(values_list))
    return templates.TemplateResponse('form.html', context={"request": request, "response": response})

if __name__ == "__main__":
    import uvicorn
    server_port = os.environ.get('PORT', '8000')
    uvicorn.run("main:app", host="0.0.0.0", port=server_port, log_level="info", proxy_headers=True)
