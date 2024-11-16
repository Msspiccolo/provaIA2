from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import xmltodict
import csv
import json
from datetime import datetime
import pymongo


app = FastAPI ()
app.add_middleware (
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


genai.configure (api_key="SUA_CHAVE_API_GOOGLE_AQUI")


client = pymongo.MongoClient ("mongodb://localhost:27017/")
db = client["AnalisadorArquivos"]
metadados_collection = db["Metadados"]

def format_schedule_text(text: str) -> str:
    text = text.replace ("```json\n", "") \
        .replace ("```", "") \
        .replace ("\n", "") \
        .strip ()
    return text



@app.post ("/process-file/")
async def process_file(file: UploadFile = File (...)):
    try:

        if not (file.filename.endswith (".csv") or file.filename.endswith (".txt") or file.filename.endswith (
                ".xml") or file.filename.endswith (".json")):
            raise HTTPException (
                status_code=400, detail="Arquivo não suportado. Envie um arquivo .csv, .txt, .xml ou .json.")

        content = await file.read ()
        try:
            decoded_content = content.decode ("utf-8")
        except UnicodeDecodeError:
            decoded_content = content.decode ("latin1")


        if file.filename.endswith (".csv"):
            csv_content = decoded_content.splitlines ()
            csv_reader = csv.DictReader (csv_content)
            csv_data = [row for row in csv_reader]
            structured_content = json.dumps (csv_data, ensure_ascii=False)
            file_format = "csv"

        elif file.filename.endswith (".txt"):
            structured_content = decoded_content
            file_format = "txt"

        elif file.filename.endswith (".xml"):
            try:
                xml_dict = xmltodict.parse (decoded_content)
                structured_content = json.dumps (xml_dict, ensure_ascii=False)
                file_format = "xml"
            except Exception as e:
                raise HTTPException (status_code=400, detail=f"Erro ao processar XML: {str (e)}")

        elif file.filename.endswith (".json"):
            try:
                json_data = json.loads (decoded_content)
                structured_content = json.dumps (json_data, ensure_ascii=False)
                file_format = "json"
            except json.JSONDecodeError as e:
                raise HTTPException (status_code=400, detail=f"Erro ao processar JSON: {str (e)}")


        prompt = (
            f"Analise o conteúdo deste arquivo '{file.filename}'. "
            f"Aqui está o conteúdo processado:\n\n{structured_content}\n\n"
            f"Responda em português no seguinte formato JSON: "
            f"[{{\"nomeColuna\": \"nome\", \"tipo\": \"string\"}}]. "
            f"Retorne uma lista com objetos no formato nomeColuna e tipo. Não envie nada além do JSON."
        )
        response = genai.generate_text (prompt=prompt)


        formatted_result = format_schedule_text (response.text)

        metadados = {
            "id": metadados_collection.estimated_document_count () + 1,
            "data": datetime.now (),
            "nome_arquivo": file.filename,
            "formato_arquivo": file_format,
            "colunas": formatted_result
        }
        metadados_collection.insert_one (metadados)

        return {"analysis": formatted_result, "metadata_id": metadados["id"]}

    except Exception as e:
        raise HTTPException (status_code=500, detail=f"Erro ao processar o arquivo: {str (e)}")
