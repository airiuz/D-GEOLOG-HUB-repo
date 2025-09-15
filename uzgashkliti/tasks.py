import json
import os, sys
from uzgashkliti.utils.converters.docx2html import Docx2Html
from celery import shared_task
from django.core.files.base import ContentFile
from uzgashkliti.utils.converters.json2html import Json2Html
from uzgashkliti.utils.converters.json2docx import Json2Docx
from files.models import File


from deploy import PDFparser

def process_pdf_worker(pdf_path):
    parser = PDFparser()
    print(pdf_path)
    result = parser.process_pdf(pdf_path)
    print('result')
    return result


@shared_task
def pdf2html_task(file_id):
    file_instance = File.objects.get(id=file_id)
    file = file_instance.file
    generated_file = File()
    file_name = file.file.name

    full_path = f"{os.path.splitext(file_name)[0]}.html"
    base_name = os.path.basename(full_path)

    r = process_pdf_worker(file.path)

    data = r.get("result", [])
    json2html = Json2Html()
    html = json2html.generate_html(data)
    generated_file.file.save(base_name, ContentFile(html))

    return {
        "initial": file_id,
        "result": generated_file.id,
    }



@shared_task
def json2html_task(file_id):
    file = File.objects.get(id=file_id).file
    json_data = file.read().decode('utf-8')
    data = json.loads(json_data)
    generated_file = File()
    file_name = file.file.name

    full_path = f"{os.path.splitext(file_name)[0]}.html"
    base_name = os.path.basename(full_path)

    json2html = Json2Html()
    html = json2html.generate_html(data)
    generated_file.file.save(base_name, ContentFile(html))

    return {
        "initial": file_id,
        "result": generated_file.id,
    }


@shared_task
def pdf2json_task(file_id):
    file_instance = File.objects.get(id=file_id)
    file = file_instance.file
    generated_file = File()
    file_name = file.file.name


    full_path = f"{os.path.splitext(file_name)[0]}.json"
    base_name = os.path.basename(full_path)

    r = process_pdf_worker(file.path)
    json_data = r.get("result", [])

    json_string = json.dumps(json_data, ensure_ascii=False)

    generated_file.file.save(base_name, ContentFile(json_string.encode('utf-8')))  # Encode as bytes

    return {
        "initial": file_id,
        "result": generated_file.id,
    }

@shared_task
def pdf2docx_task(file_id):
    file_instance = File.objects.get(id=file_id)
    file = file_instance.file
    generated_file = File()
    file_name = file.file.name

    full_path = f"{os.path.splitext(file_name)[0]}.docx"
    base_name = os.path.basename(full_path)

    r = process_pdf_worker(file.path)
    data = r.get("result", [])
    with open("/home/wsmsi4090/FOZILJON/UZGASHKLITI/media-files/JSON/output.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    json2docx = Json2Docx()
    docx = json2docx.generate_docx(data)
    generated_file.file.save(base_name, ContentFile(docx))

    return {
        "initial": file_id,
        "result": generated_file.id,
    }



@shared_task
def json2docx_task(file_id):
    file = File.objects.get(id=file_id).file
    json_data = file.read().decode('utf-8')
    data = json.loads(json_data)
    generated_file = File()
    file_name = file.file.name

    full_path = f"{os.path.splitext(file_name)[0]}.docx"
    base_name = os.path.basename(full_path)

    json2docx = Json2Docx()
    docx = json2docx.generate_docx(data)
    generated_file.file.save(base_name, ContentFile(docx))

    return {
        "initial": file_id,
        "result": generated_file.id,
    }



@shared_task
def docx2html_task(file_id):
    file = File.objects.get(id=file_id).file
    generated_file = File()
    file_name = file.file.name

    full_path = f"{os.path.splitext(file_name)[0]}.html"
    base_name = os.path.basename(full_path)

    docx2html = Docx2Html()
    html = docx2html.generate_html(file)
    generated_file.file.save(base_name, ContentFile(html))

    return {
        "initial": file_id,
        "result": generated_file.id,
    }