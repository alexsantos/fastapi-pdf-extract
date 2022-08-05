# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
import pdfplumber
import pandas as pd

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1vB_eHMVn1yIQ3K8RyEMMo-SM71AAtwKwQh3VZ_E5ZrA'
SAMPLE_RANGE_NAME = 'Folha1!A:G'


def compute(pdfFile):
    pdf = pdfplumber.open(pdfFile)
    p0 = pdf.pages[0]
    posto_box = p0.within_bbox((0, 55, 300, 85))
    posto = posto_box.extract_text().split(':').pop().lstrip(' ')
    table_settings = {
        "vertical_strategy": "lines"
    }
    table = p0.extract_table(table_settings)
    df = pd.DataFrame(table[1:],
                      columns=['Programa principal', 'Rpt.', 'Dimensões', 'Resíduo', 'Duração [hh:mm:ss]',
                               'Chapas feitas'])
    df['Posto'] = posto
    df.drop(index=df.index[0],
            axis=0,
            inplace=True)
    for column in ['Programa principal']:
        df[column] = df[column].str.replace(r"^[A-Za-z0-9]*_", "", regex=True)
    for column in ['Duração [hh:mm:ss]']:
        df[column] = df[column].str.replace(r"\n\[h:min:s\]", "", regex=True)
    for column in ['Dimensões', 'Resíduo']:
        df[column] = df[column].str.replace(r"\n", " ", regex=True)
    print(df)
    values = df.values.tolist()
    return values
