import re

from bs4 import BeautifulSoup as BS

PAGE_SIZE = {
    "portrait": {
        "x": 816,
        "y": 1056
    },
    "landscape": {
        "x": 1056,
        "y": 816
    }
}


class Json2Html:

    def process_block(self, data):
        optized_data = []

        grouped_data = []
        new_group = []
        prev = {}
        labels = []
        positions = []
        alignments = []
        types = []
        footers = []
        for c, item in enumerate(data):
            id = prev.get("ID", None)
            label = prev.get("label", None)
            if (not prev or id == item["ID"]) and not label == "footer":
                new_group.append(item)
                labels.append(item["label"])
                positions.append(item["position"])
                alignments.append(item["alignment"])
                types.append(item["type"])

            else:
                grouped_data.append(
                    {"contents": new_group, "labels": labels, "positions": positions, "alignments": alignments,
                     "types": types})

                new_group = [item]
                labels = [item["label"]]
                positions = [item["position"]]
                alignments = [item["alignment"]]
                types = [item["type"]]

            if c == len(data) - 1:
                grouped_data.append(
                    {"contents": new_group, "labels": labels, "positions": positions, "alignments": alignments,
                     "types": types})

            prev = item

        for groups in grouped_data:
            prevGrID = None
            page_size = groups["contents"][0]["page_size"]
            page = {"width": page_size["width"], "height": page_size["height"], "ratio": {
                "width": PAGE_SIZE["portrait"]["x"] / page_size["width"],
                "height": PAGE_SIZE["portrait"]["y"] / page_size["height"]
            }, "orientation": "portrait"}

            if page["width"] > page["height"]:
                page["ratio"] = {
                    "width": PAGE_SIZE["landscape"]["x"] / page["width"],
                    "height": PAGE_SIZE["landscape"]["y"] / page["height"]
                }
                page["orientation"] = "landscape"

            block = {"page": page, "block_labels": groups["labels"], "block_positions": groups["positions"],
                     "block_alignments": groups["alignments"], "block_types": groups["types"]}

            block["groups"] = []
            new_group = []
            if groups["labels"][0] == "footer":
                block["groups"].append(groups["contents"])
                footers.append(block)
                continue

            for c, item in enumerate(groups["contents"]):

                if prevGrID is None or item["grID"] == prevGrID:
                    new_group.append(item)

                else:
                    block["groups"].append(new_group)
                    new_group = [item]

                if c == len(groups["contents"]) - 1:
                    block["groups"].append(new_group)

                prevGrID = item["grID"]

            optized_data.append(block)

        return optized_data, footers

    def single_group(self, data, prevData, nextData):
        block = None
        groups = data["groups"]
        label = data["block_labels"][0]
        page = data["page"]
        prevLabel = prevData["block_labels"][0] if prevData is not None else None

        item = groups[0][0]
        x0, y0, x1, y1 = item["box"]["xmin"], item["box"]["ymin"], item["box"]["xmax"], item["box"]["ymax"]

        if item["type"] == "image":
            block = BS("<p></p>", 'html.parser').p
            block[
                "style"] = f"""text-align: {item["alignment"]}; margin-top: {"0" if prevLabel == "caption" and item["label"] == "table" else "0.1in"}"""
            image = BS('<img/>', 'html.parser').img
            image['src'] = item["src"]
            image['alt'] = "picture"
            image[
                'style'] = f"""width: {(x1 - x0) * page["ratio"]["width"]}px; height: {(y1 - y0) * page["ratio"]["height"]}px"""
            block.append(image)

        elif label == "paragraph":
            block = BS("<p></p>", 'html.parser').p
            block[
                "style"] = f"""text-indent: 0.5in; text-align: {item["alignment"]}; font-weight: {item["font"]["weight"]}; font-style: {item["font"]["style"]}; font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5; margin-top: 0.1in"""
            block.string = item["src"]

        elif label == "continued" or label == "lined":
            block = BS("<p></p>", 'html.parser').p
            block[
                "style"] = f"""font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5; margin-top: 0.1in"""
            block.string = item["src"]

        elif label == "caption":
            if nextData["block_labels"][0] == "table" or nextData["block_labels"][0] == "picture":
                width = nextData["groups"][0][0]["box"]["xmax"] - nextData["groups"][0][0]["box"]["xmin"]
                ratio = nextData["page"]["ratio"]
                block = BS("<p></p>", 'html.parser').p
                block[
                    "style"] = f"""max-width: {width * ratio["width"]}px; margin: 0 auto; line-height: 1.5; text-align: {item["position"] if item["position"] != "full" else "left"}"""

                span = BS("<span></span>", 'html.parser').span
                span[
                    "style"] = f"""text-align: {item["alignment"]}; display: inline-block; font-size: {item["font"]["size"]}pt;font-size: {item["font"]["size"]}pt; font-weight: {item["font"]["weight"]}; font-style: {item["font"]["style"]}; font-family: 'Times New Roman', Times, serif"""
                span.string = item["src"]

                block.append(span)


            else:
                block = BS("<p></p>", 'html.parser').p
                block[
                    "style"] = f"""margin: 0.1in auto 0; line-height: 1.5; text-align: {item["position"] if item["position"] != "full" else "left"}; margin-top: 0.1in"""

                block[
                    "style"] = f"""text-align: {item["position"] if item["position"] != "full" else "left"}"""

                span = BS("<span></span>", 'html.parser').span
                span[
                    "style"] = f"""text-align: {item["alignment"]}; display: inline-block; font-size: {item["font"]["size"]}pt; max-width: {(x1 - x0) * page["ratio"]["width"]}px; font-size: {item["font"]["size"]}pt; font-weight: {item["font"]["weight"]}; font-style: {item["font"]["style"]}; font-family: 'Times New Roman', Times, serif"""
                span.string = item["src"]

                block.append(span)

        elif label == "subtitle":
            block = BS("<p></p>", 'html.parser').p
            block[
                "style"] = f"""text-indent: 0.5in; text-align: {item["alignment"]}; font-weight: {item["font"]["weight"]}; font-style: {item["font"]["style"]}; font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5; margin-top: 0.1in"""
            block.string = item["src"]

        elif label == "formula":
            try:
                block = BS("<p></p>", 'html.parser').p
                pattern = r"\\eqno|\\eqn|\\left|\\right|\\Bigg \\|\\left\\|\\right\\"
                latex = re.sub(pattern, " ", item["src"]["latex"])
                block[
                    "style"] = f"""font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5; text-align: {item["alignment"]}; margin-top: 0.1in"""
                block.string = f"""\\[{latex}\\]"""
            except:
                block = BS("<p></p>", 'html.parser').p
                block[
                    "style"] = f"""text-align: {item["alignment"]}; font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5; margin-top: {"0" if prevLabel == "caption" else "0.1in"}"""
                image = BS('<img/>', 'html.parser').img
                image['src'] = item["src"]["image"]
                image['alt'] = "picture"
                image[
                    'style'] = f"""width: {(x1 - x0) * page["ratio"]["width"]}px; height: {(y1 - y0) * page["ratio"]["height"]}px"""

        elif label == "title" or label == "central":
            block = BS("<p></p>", 'html.parser').p
            block[
                "style"] = f"""font-weight: {item["font"]["weight"]}; font-style: {item["font"]["style"]}; text-align: center; font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5; margin-top: 0.1in"""
            block.string = item["src"]


        elif label == "table":
            block = BS(item['src'], 'html.parser').find()
            block[
                'style'] = f"""margin: {"0" if prevLabel == "caption" else "0.1in"} auto 0; background-color: #fff; font-size: {item["font"]["size"]}pt; width: {(x1 - x0) * page["ratio"]["width"]}px; height: {(y1 - y0) * page["ratio"]["height"]}px"""
            block["class"] = "table"


        else:
            print("Label not Found", label)

        return block

    def multiple_group(self, data):
        block = BS("<table></table>", "html.parser").table
        groups = data["groups"]
        block["style"] = f"""width: 100%; table-layout: fixed; margin: 0.5in 0 0.4in"""
        page = data["page"]
        tr = BS("<tr></tr>", "html.parser").tr
        inline_tr = BS("<tr></tr>", "html.parser").tr
        for g, group in enumerate(groups):
            td = BS("<td></td>", "html.parser", preserve_whitespace_tags={'html'}).td
            inline_td = BS("<td></td>", "html.parser", preserve_whitespace_tags={'html'}).td
            rowspan = 1
            for i, item in enumerate(group):
                x0, y0, x1, y1 = item["box"]["xmin"], item["box"]["ymin"], item["box"]["xmax"], item["box"]["ymax"]
                if i > 0:
                    rowspan += 1
                    td.append(BS("<br></br>", "html.parser").br)

                if item["type"] == "image":
                    td[
                        "style"] = f"""text-align: {item["alignment"]}"""
                    image = BS('<img/>', 'html.parser').img
                    image['src'] = item["src"]
                    image['alt'] = "picture"
                    image[
                        'style'] = f"""width: {(x1 - x0) * page["ratio"]["width"]}px; height: {(y1 - y0) * page["ratio"]["height"]}px"""
                    td.append(image)

                elif item["label"] == "paragraph":
                    group_item = BS("<span></span>", "html.parser").span
                    group_item[
                        "style"] = f"""display: inline-block; text-align: {item["alignment"]}; font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5; font-weight: {item["font"]["weight"]}; font-style: {item["font"]["style"]}"""
                    group_item.string = item["src"]
                    td.append(group_item)

                elif item["label"] == "continued" or item["label"] == "lined":
                    group_item = BS("<span></span>", "html.parser").span
                    group_item[
                        "style"] = f"""display: inline-block; text-align: {item["alignment"]}; font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5; font-weight: {item["font"]["weight"]}; font-style: {item["font"]["style"]}"""
                    group_item.string = item["src"]
                    td.append(group_item)

                elif item["label"] == "caption":
                    td[
                        "style"] = f"""font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5; text-align: {item["position"] if item["position"] != "full" else "left"}"""
                    group_item = BS('<span></span>', 'html.parser').span
                    group_item[
                        "style"] = f"""display: inline-block; max-width: {(x1 - x0) * page["ratio"]["width"]}px; font-weight: {item["font"]["weight"]}; font-style: {item["font"]["style"]}; text-align: {item["alignment"]}"""
                    group_item.string = item["src"]
                    td.append(group_item)

                elif item["label"] == "subtitle":
                    group_item = BS("<span></span>", "html.parser").span
                    group_item[
                        "style"] = f"""display: inline-block; text-indent: 0.5in; text-align: {item["alignment"]}; font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5; font-weight: {item["font"]["weight"]}; font-style: {item["font"]["style"]}"""
                    group_item.string = item["src"]
                    td.append(group_item)


                elif item["label"] == "title" or item["label"] == "central":
                    td[
                        "style"] = f"""font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5; text-align: center"""
                    group_item = BS('<span></span>', 'html.parser').span
                    group_item[
                        "style"] = f"""font-weight: {item["font"]["weight"]}; font-style: {item["font"]["style"]}; text-align: {item["alignment"]}"""
                    group_item.string = item["src"]
                    td.append(group_item)


                elif item["label"] == "formula":
                    try:
                        td[
                            "style"] = f"""text-align: {item["alignment"]}; font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5"""
                        group_item = BS('<span></span>', 'html.parser').span
                        pattern = r"\\eqno|\\eqn|\\left|\\right|\\Bigg \\|\\left\\|\\right\\"
                        latex = re.sub(pattern, " ", item["src"]["latex"])

                        group_item.string = f"""\\[{latex}\\]"""
                        td.append(group_item)

                    except:
                        td[
                            "style"] = f"""text-align: {item["alignment"]}; font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5"""
                        image = BS('<img/>', 'html.parser').img
                        image['src'] = item["src"]["image"]
                        image['alt'] = "picture"
                        image[
                            'style'] = f"""width: {(x1 - x0) * page["ratio"]["width"]}px; height: {(y1 - y0) * page["ratio"]["height"]}px"""

                        td.append(image)

                elif item["label"] == "table":
                    td[
                        "style"] = f"""text-align: {item["alignment"]}; font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; line-height: 1.5"""

                    group_item = BS(item['src'], 'html.parser').find()
                    group_item[
                        'style'] = f"""background-color: #fff; font-size: 11pt; width: {(x1 - x0) * page["ratio"]["width"]}px; height: {(y1 - y0) * page["ratio"]["height"]}px"""
                    group_item["class"] = "table"

                else:
                    print(item["label"])

            if rowspan > 1:
                td["rowspan"] = rowspan

            if len(td) == 0:
                pre = BS("<pre></pre>", "html.parser").pre
                pre.string = " "
                td.append(pre)

            if len(inline_td) == 0:
                pre = BS("<pre></pre>", "html.parser").pre
                pre.string = " "
                inline_td.append(pre)

            tr.append(td)

            if "inline" in data["block_labels"] and rowspan == 1:
                inline_tr.append(inline_td)

        block.append(tr)
        if len(inline_tr) > 0:
            block.append(inline_tr)

        return block

    def footer_group(self, footer):
        groups = footer["groups"]
        item = groups[0][0]
        x0, y0, x1, y1 = item["box"]["xmin"], item["box"]["ymin"], item["box"]["xmax"], item["box"]["ymax"]

        tr = BS("<tr></tr>", 'html.parser').tr
        td = BS("<td></td>", 'html.parser').td

        td[
            "style"] = f"""text-align: {item["alignment"]}; font-weight: {item["font"]["weight"]}; font-style: italic; font-size: {item["font"]["size"]}pt; font-family: 'Times New Roman', Times, serif; padding: 4px 0; color: #15329e"""

        td.string = item["src"]

        tr.append(td)

        return tr

    def generate_html(self, jsonContent):

        optimized_data, footers = self.process_block(jsonContent)
        container = BS('<main></main>', 'html.parser').main
        container[
            'style'] = f"""background-color: #f8fafc; padding-top: 32px; min-height: 100vh; min-height: 100svh"""

        content = None
        orientation = None
        prevData = None
        nextData = None

        for d, data in enumerate(optimized_data):
            page = data["page"]
            block = None

            if d + 1 < len(optimized_data):
                nextData = optimized_data[d + 1]

            if orientation != page["orientation"]:
                if orientation is not None:
                    container.append(content)
                orientation = page["orientation"]
                content = BS('<div></div>', 'html.parser').div
                content[
                    'style'] = f"""background-color: #fff; overflow-x: auto; max-width: {PAGE_SIZE[orientation]["x"]}px; min-height: {PAGE_SIZE[orientation]["y"]}px; margin: 28px auto 0; box-shadow: -5px -5px 10px rgba(0, 0, 0, 0.1), 5px 5px 10px rgba(0, 0, 0, 0.1); padding: 32px 24px 36px 24px;"""

            if len(data["block_labels"]) == 1:
                block = self.single_group(data, prevData, nextData)

            else:
                block = self.multiple_group(data)

            if block is not None:
                content.append(block)

            prevData = data

        footer_block = BS('<table></table>', 'html.parser').table
        footer_block["style"] = "margin-top: 0.1in"
        for f, footer in enumerate(footers):
            footer_block.append(self.footer_group(footer))
            content.append(footer_block)

        if content is not None:
            container.append(content)

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <script>
                    window.MathJax = {{
                        tex: {{
                            autoload: {{
                                upgreek: [
                                    'upalpha', 'upbeta', 'upchi', 'updelta', 'Updelta', 'upepsilon',
                                    'upeta', 'upgamma', 'Upgamma', 'upiota', 'upkappa', 'uplambda',
                                    'Uplambda', 'upmu', 'upnu', 'upomega', 'Upomega', 'upomicron',
                                    'upphi', 'Upphi', 'uppi', 'Uppi', 'uppsi', 'Uppsi', 'uprho',
                                    'upsigma', 'Upsigma', 'uptau', 'uptheta', 'Uptheta', 'upupsilon',
                                    'Upupsilon', 'upvarepsilon', 'upvarphi', 'upvarpi', 'upvarrho',
                                    'upvarsigma', 'upvartheta', 'upxi', 'Upxi', 'upzeta'
                                ]
                            }}
                        }}
                    }};
                </script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js"></script>
                <title>Sample HTML</title>
            </head>
            <style>
                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }}
                .table, .table td, .table th {{
                    border: 1px solid;
                    border-collapse: collapse;
                    padding: 0 4px;
                }}


            </style>
            <body>
                {container}
            </body>
        </html>
        """

        return html
