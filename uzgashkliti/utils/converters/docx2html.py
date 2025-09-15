import os
import uuid
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from bs4 import BeautifulSoup as BS
from docx.opc.constants import RELATIONSHIP_TYPE
from lxml import etree
from docx.oxml.ns import qn
from docx.text.run import Run
from docx.text.hyperlink import Hyperlink
from docx.enum.text import WD_ALIGN_PARAGRAPH

hAlignments = {
    0: 'left',
    1: 'center',
    2: 'right',
    3: 'justify',
}

vAlignments = {
    0: 'top',
    1: 'center',
    3: 'bottom',
}

namespaces = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
}


class Docx2Html:
    def extract_images(self):
        media_folder = "media-files"
        public_folder = os.path.join(media_folder, "public")
        html_images_folder = os.path.join(public_folder, "html_images")

        if not os.path.exists(media_folder):
            os.makedirs(media_folder)

        if not os.path.exists(public_folder):
            os.makedirs(public_folder)

        if not os.path.exists(html_images_folder):
            os.makedirs(html_images_folder)

        url = f"https://development.airi.uz/media/public/html_images"

        # url = "/Users/shakhriyormamadaliev/My files/Airi projects/converters/python-docx/media-files/public/html_images"

        for rel in self.rels.values():
            if rel.reltype == RELATIONSHIP_TYPE.IMAGE:
                rId = rel.rId
                img = rel.target_part
                img_name = f"{uuid.uuid4()}{os.path.splitext(img.partname)[-1]}"

                self.images[rId] = f"{url}/{img_name}"
                with open(os.path.join(html_images_folder, img_name), "wb") as img_file:
                    img_file.write(img.blob)

    def paragraph_style(self, paragraph):
        content_type = paragraph.style.name

        space_before = self.space_before if paragraph.paragraph_format.space_before is None else paragraph.paragraph_format.space_before.pt
        space_after = self.space_after if paragraph.paragraph_format.space_after is None else paragraph.paragraph_format.space_after.pt

        left_indent = 0 if paragraph.paragraph_format.left_indent is None else paragraph.paragraph_format.left_indent.pt
        right_indent = 0 if paragraph.paragraph_format.right_indent is None else paragraph.paragraph_format.right_indent.pt

        line_height = 1.1 if paragraph.paragraph_format.line_spacing is None else round(
            paragraph.paragraph_format.line_spacing / 12700 / 8, 2)

        if line_height == 0:
            line_height = 1.1

        bold = "Normal"

        if content_type is not None and (
                content_type == "Title" or content_type[0:-2] == "Heading" and int(content_type[-1]) > 0 and int(
            content_type[-1]) < 7 and int(
            content_type[-1]) != 5):
            bold = "bold"

        return f"""word-wrap: break-word; text-align: {hAlignments.get(paragraph.alignment, "justify")}; font-weight: {bold}; line-height: {line_height}; margin-left: {left_indent}pt; margin-right: {right_indent}pt; margin-top: {space_before}pt; margin-bottom: {space_after if space_after > 0 else 8}pt"""

    def process_table(self, table):
        html_table = BS('<table></table>', 'html.parser').table
        html_tbody = BS('<tbody></tbody>', 'html.parser').tbody

        tblPr = table._tblPr

        tbl_borders = tblPr.find(qn('w:tblBorders'))
        tbl_alignment = table.alignment

        if tbl_alignment == WD_ALIGN_PARAGRAPH.LEFT:
            tbl_alignment = "left"
        elif tbl_alignment == WD_ALIGN_PARAGRAPH.CENTER:
            tbl_alignment = "center"
        elif tbl_alignment == WD_ALIGN_PARAGRAPH.RIGHT:
            tbl_alignment = "right"
        elif tbl_alignment == WD_ALIGN_PARAGRAPH.JUSTIFY:
            tbl_alignment = "justify"

        table_borders = {
            "top": 0,
            "bottom": 0,
            "right": 0,
            "left": 0,
        }

        cell_borders = {
            "top": 0,
            "bottom": 0,
            "right": 0,
            "left": 0,
        }

        if tblPr.style is not None:
            table_borders = {
                "top": 0.75,
                "bottom": 0.75,
                "right": 0.75,
                "left": 0.75
            }
            cell_borders = {
                "top": 0.75,
                "bottom": 0.75,
                "right": 0.75,
                "left": 0.75
            }

        if tbl_borders is not None:
            top = tbl_borders.find(qn('w:top'))
            bottom = tbl_borders.find(qn('w:bottom'))
            left = tbl_borders.find(qn('w:left'))
            right = tbl_borders.find(qn('w:right'))
            insideH = tbl_borders.find(qn('w:insideV'))
            insideV = tbl_borders.find(qn('w:insideV'))

            if top is not None:
                # val = top.get(qn('w:val'), 0)
                table_borders["top"] = int(top.get(qn('w:sz'), 0)) / 8
                # color = top.get(qn('w:color'), 0)

            if bottom is not None:
                # val = bottom.get(qn('w:val'), 0)
                table_borders["bottom"] = int(bottom.get(qn('w:sz'), 0)) / 8
                # color = bottom.get(qn('w:color'), 0)

            if left is not None:
                # val = left.get(qn('w:val'), 0)
                table_borders["left"] = int(left.get(qn('w:sz'), 0)) / 8
                # color = left.get(qn('w:color'), 0)

            if right is not None:
                # val = right.get(qn('w:val'), 0)
                table_borders["right"] = int(right.get(qn('w:sz'), 0)) / 8
                # color = right.get(qn('w:color'), 0)

        rows = table.rows
        n = len(rows)
        m = max(len(row.cells) for row in table.rows)

        html_rows = [BS('<tr></tr>', 'html.parser').tr for _ in range(n)]
        table_matrix = [[] for _ in range(n)]

        spans = [1 for _ in range(n)]

        for j in range(m):
            rowspan = 1
            for i in range(n - 1, -1, -1):
                if j < len(rows[i].cells):
                    cell = rows[i].cells[j]
                    colspan = cell.grid_span
                    if spans[i] > 1:
                        spans[i] -= 1
                        continue

                    spans[i] = colspan

                    if i > 0:
                        prev_cell = rows[i - 1].cells[j]._element
                    else:
                        prev_cell = None

                    cell_element = rows[i].cells[j]._element

                    table_matrix[i].append({"text": cell.text.strip(), "colspan": cell.grid_span, "rowspan": rowspan})

                    if prev_cell == cell_element:
                        rowspan += 1
                    else:
                        html_cell = BS('<td></td>', 'html.parser').td
                        tc = cell._tc
                        tcPr = tc.tcPr
                        tcBorders = tcPr.find(qn('w:tcBorders'))
                        tcWidth = tcPr.width

                        if tcWidth is not None:
                            tcWidth = f"""{tcWidth / 12700}pt"""
                        else:
                            tcWidth = "auto"
                        if tcBorders is not None:
                            top = tcBorders.find(qn('w:top'))
                            bottom = tcBorders.find(qn('w:bottom'))
                            left = tcBorders.find(qn('w:left'))
                            right = tcBorders.find(qn('w:right'))
                            if top is not None:
                                # val = top.get(qn('w:val'), 0)
                                cell_borders["top"] = int(top.get(qn('w:sz'), 0)) / 8
                                # color = top.get(qn('w:color'), 0)

                            if bottom is not None:
                                # val = bottom.get(qn('w:val'), 0)
                                cell_borders["bottom"] = int(bottom.get(qn('w:sz'), 0)) / 8
                                # color = bottom.get(qn('w:color'), 0)

                            if left is not None:
                                # val = left.get(qn('w:val'), 0)
                                cell_borders["left"] = int(left.get(qn('w:sz'), 0)) / 8
                                # color = left.get(qn('w:color'), 0)

                            if right is not None:
                                # val = right.get(qn('w:val'), 0)
                                cell_borders["right"] = int(right.get(qn('w:sz'), 0)) / 8
                                # color = right.get(qn('w:color'), 0)

                        # if cell_styles == "":
                        #     cell_styles = table_styles

                        for paragraph in cell.paragraphs:
                            block_name = paragraph.style.name
                            line_height = 1.1 if paragraph.paragraph_format.line_spacing is None else round(
                                paragraph.paragraph_format.line_spacing / 12700 / 8, 2)
                            content_style = f"""display: inline-block; max-width: {tcWidth}; text-align: {hAlignments.get(paragraph.alignment, "justify")}; line-height: {line_height}; margin-top: 0; margin-bottom: 0; padding: 2pt"""

                            if block_name == "List Paragraph":
                                self.process_list(paragraph, content_style)

                            else:
                                if self.ul is not None:
                                    html_cell.append(self.ul)
                                    self.ul = None

                                paragraph_content = self.process_paragraph(paragraph, content_style)

                                if len(paragraph_content) > 0:
                                    html_cell.append(paragraph_content)

                                else:
                                    html_cell.append(" ")

                        if self.ul is not None:
                            html_cell.append(self.ul)
                            self.ul = None

                        html_cell[
                            "style"] = f"""vertical-align: {vAlignments.get(cell.vertical_alignment, "top")}; padding: 0 4px; border-top: {cell_borders["top"]}pt solid #000000; border-bottom: {cell_borders["bottom"]}pt solid #000000; border-right: {cell_borders["right"]}pt solid #000000; border-left: {cell_borders["left"]}pt solid #000000"""

                        html_cell["colspan"] = colspan
                        html_cell["rowspan"] = rowspan

                        html_rows[i].append(html_cell)

                        rowspan = 1

                else:
                    print(f"Row {i} has no cell at column {j}")

        for i, r in enumerate(html_rows):
            html_tbody.append(r)

        html_table[
            "style"] = f"""width: 100%; table-layout: fixed; border-collapse: collapse; padding: 0 4px; margin: 0; font-size: 12pt; border-top: {table_borders["top"]}pt solid #000000; border-bottom: {table_borders["bottom"]}pt solid #000000; border-right: {table_borders["right"]}pt solid #000000; border-left: {table_borders["left"]}pt solid #000000; text-align: {tbl_alignment}"""
        html_table.append(html_tbody)

        self.content.append(html_table)

    def process_block(self, block):
        block_name = block.style.name
        style = self.paragraph_style(block)
        if block_name == "List Paragraph":
            self.process_list(block, style)

        else:
            if self.ul is not None:
                self.content.append(self.ul)
                self.ul = None
            self.content.append(self.process_paragraph(block, style))

    def process_list(self, content, style):
        li = BS('<li></li>', 'html.parser').li
        li["style"] = style
        if self.ul is None:
            self.ul = BS('<ul></ul>', 'html.parser').ul
            self.ul["style"] = "margin-left: 40px"

        self.ul.append(self.process_runs(content, li))

    def process_paragraph(self, content, style):
        p = BS('<p></p>', 'html.parser').p
        p["style"] = style
        self.process_runs(content, p)

        return p

    def process_runs(self, content, container):
        first_line = True

        for item in content._p:
            tag = etree.QName(item.tag).localname
            if tag == "r":

                xml_str = etree.tostring(item, encoding="unicode")
                root = etree.fromstring(xml_str)
                alt_content = root.find(".//mc:AlternateContent", namespaces)

                if alt_content is not None:
                    drawing = alt_content.find(".//w:drawing", namespaces)
                else:
                    drawing = item.find(qn("w:drawing"))

                if drawing is not None:
                    blip = drawing.find('.//a:blip', namespaces)
                    src = None

                    if blip is not None:
                        rId = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                        src = self.images.get(rId, None)

                    if src is not None:
                        extent = drawing.find(".//wp:extent", namespaces)
                        if extent is not None:
                            width_emu = int(extent.get("cx"))
                            height_emu = int(extent.get("cy"))

                            width_px = int((width_emu / 914400) * 96)
                            height_px = int((height_emu / 914400) * 96)

                            img = BS('<img/>', 'html.parser').img
                            img["style"] = f"""width: {width_px}px; height: {height_px}px; max-width: 100%;"""
                            img["src"] = src
                            img["alt"] = "Failed to load image"

                            container.append(img)


                else:
                    run = Run(item, content)

                    font = getattr(run, "font", "'Times New Roman', Times, serif")
                    element_styles = []

                    if first_line:
                        try:
                            element_styles.append(f"""margin-left: {content.paragraph_format.first_line_indent.pt}pt""")
                            first_line = False
                        except:
                            first_line = False

                    span = BS("<span></span>", "html.parser").span
                    if font.name is not None:
                        element_styles.append(f"font-family: {font.name}")

                    if font.size is not None:
                        element_styles.append(f"font-size: {font.size.pt}pt")

                    if font.color.rgb is not None:
                        element_styles.append(f"color: #{font.color.rgb}")

                    if font.bold:
                        element_styles.append("font-weight: bold")

                    if font.italic:
                        element_styles.append("font-style: italic")

                    if font.underline:
                        element_styles.append("text-decoration-line: underline")

                    span.append(run.text)

                    if len(element_styles) > 0:
                        span["style"] = "; ".join(element_styles)

                    if span.text == "":
                        container.append(" ")
                    else:
                        container.append(span)

            elif tag == "hyperlink":
                hyperlink = Hyperlink(item, content)
                font = getattr(hyperlink, "font", "'Times New Roman', Times, serif")
                element_styles = []
                anchor = BS("<a></a>", "html.parser").a
                # if font.name is not None:
                #     element_styles.append(f"font-family: {font.name}")

                # if font.size is not None:
                #     element_styles.append(f"font-size: {font.size.pt}pt")

                # if font.color.rgb is not None:
                #     element_styles.append(f"color: #{font.color.rgb}")

                # if font.bold:
                #     element_styles.append("font-weight: bold")

                # if font.italic:
                #     element_styles.append("font-style: italic")

                # if font.underline:
                #     element_styles.append("text-decoration-line: underline")

                anchor.append(hyperlink.text)
                anchor["href"] = hyperlink.address
                anchor["alt"] = hyperlink.text
                anchor["target"] = "_blank"

                if len(element_styles) > 0:
                    anchor["style"] = "; ".join(element_styles)

                if anchor.text == "":
                    container.append(" ")
                else:
                    container.append(anchor)

            elif tag == "oMath":
                xslt = etree.parse("OMML2MML.XSL")
                transform = etree.XSLT(xslt)

                mathml = transform(item)
                math_xml = BS(etree.tostring(mathml, encoding="unicode"), 'xml')

                container.append(math_xml)
            elif tag == "oMathPara":
                xslt = etree.parse("OMML2MML.XSL")
                transform = etree.XSLT(xslt)

                span = BS("<span></span>", "html.parser").span
                span["style"] = "display: inline-block; width: 100%; text-align: center"

                mathml = transform(item)
                math_xml = BS(etree.tostring(mathml, encoding="unicode"), 'xml')

                span.append(math_xml)
                container.append(span)

        return container

    def generate_html(self, docx_file):
        self.doc = Document(docx_file)
        self.rels = self.doc.part.rels
        self.styles = self.doc.styles['Normal']
        self.space_after = 8 if self.styles.paragraph_format.space_after is None else self.styles.paragraph_format.space_after.pt
        self.space_before = 0 if self.styles.paragraph_format.space_before is None else self.styles.paragraph_format.space_before.pt

        self.rels = self.doc.part.rels
        self.container = BS('<main></main>', 'html.parser').main

        self.container[
            'style'] = f"""display: flex; flex-direction: column; min-height: 100vh; align-items: center; gap: 16px; background-color: #f8fafc; padding: 16px; font-family: {"'Times New Roman', Times, serif" if self.styles.font.name is None else self.styles.font.name}; font-size: {"14pt" if self.styles.font.size is None else self.styles.font.size.pt}pt"""

        self.content = BS('<div class="paper"></div>', 'html.parser').div

        self.size = "thin"
        self.images = {}
        self.ul = None

        for c in self.doc.iter_inner_content():

            if isinstance(c, Table):
                self.process_table(c.table)

            if isinstance(c, Paragraph):
                self.process_block(c)

        if self.ul is not None:
            self.content.append(self.ul)
            self.ul = None

        self.container.append(self.content)

        html = f"""
                 <!DOCTYPE html>
                 <html lang="en">
                     <head>
                         <meta charset="UTF-8" />
                         <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                         <title>Sample HTML</title>
                         <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
                             <style>
                             * {{
                               box-sizing: border-box;
                               margin: 0;
                               padding: 0;
                             }}

                             .paper {{
                                 width: 210mm;  
                                 min-height: 297mm;
                                 background-color: white;
                                 padding: 20mm;
                                 box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
                                 box-sizing: border-box;
                             }}

                             h1, p {{
                                 margin: 0 0 20px;
                             }}

                             /* Responsive style */
                             @media (max-width: 1024px) {{
                                 .paper {{
                                     width: 100%;
                                     min-height: auto;
                                     padding: 10mm;
                                 }}
                             }}

                             @media (max-width: 768px) {{
                                 .paper {{
                                     padding: 5mm;
                                 }}
                             }}

                             @media (max-width: 480px) {{
                                 .paper {{
                                     width: 100%;
                                     padding: 2mm;
                                 }}
                             }}
                         </style>
                     </head>
                     <body>
                         {self.container}
                     </body>
                 </html>
                 """
        return html






