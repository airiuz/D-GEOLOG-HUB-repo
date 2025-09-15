from django.urls import re_path
from uzgashkliti.views import Pdf2HtmlView, Json2HtmlView, \
    Pdf2DocxView, Json2DocxView, Docx2HtmlView, Pdf2JsonView

app_name = 'uzgashkliti'

urlpatterns = [
    re_path(r'^pdf2json/?$', Pdf2JsonView.as_view(), name="pdf2json"),
    re_path(r'^pdf2html/?$', Pdf2HtmlView.as_view(), name="pdf2html"),
    re_path(r'^json2html/?$', Json2HtmlView.as_view(), name="json2html"),
    re_path(r'^pdf2docx/?$', Pdf2DocxView.as_view(), name="pdf2docx"),
    re_path(r'^json2docx/?$', Json2DocxView.as_view(), name="json2docx"),
    re_path(r'^docx2html/?$', Docx2HtmlView.as_view(), name="docx2html"),
]