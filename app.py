from io import BytesIO, StringIO

from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.pyplot as plt
import re
from flask import Flask, render_template, request, redirect, make_response, flash
from flask.helpers import make_response
import pandas as pd
import matplotlib
import urllib.parse
import json
matplotlib.use('Agg')

app = Flask(__name__)


def save_json(file_list):
    save_array_data = []
    for file in file_list:
        file_name = file["file_name"]
        txt_data = file["data"]
        each_array_data = {"file_name": file_name, "content": []}
        channel_list = txt_data.split("[LC Chromatogram(")
        del channel_list[0]
        for channel in channel_list:
            name = re.search(r'(AD1|A-Ch2|A-Ch1)', channel).group(0)
            if "R.Time (min),Intensity" in channel:
                raw_data = channel.split("R.Time (min),Intensity\n")[
                    1].split("\n\n")[0]
                data = []
                for row in raw_data.splitlines():
                    if row:
                        data.append([row.split(",")[0], row.split(",")[1]])
                channel_data = {"name": name, "data": data}
                each_array_data["content"].append(channel_data)
            else:
                raw_data = channel.split("R.Time (min)\tIntensity\n")[
                    1].split("\n\n")[0]
                data = []
                for row in raw_data.splitlines():
                    if row:
                        data.append([row.split("\t")[0], row.split("\t")[1]])
                channel_data = {"name": name, "data": data}
                each_array_data["content"].append(channel_data)
        save_array_data.append(each_array_data)

    with open("data/data.json", "w") as f:
        json.dump(save_array_data, f, indent=2)


class Note:
    def __init__(self, data):
        self.fig = plt.figure()
        self.data = data

    def mix(self, num, param):
        param_list = {"a": [], "b": [], "c": 0, "d": 0, "time": 0}
        data = self.data[num-1]["data"]
        for each in data:
            if each["name"] == "A-Ch1":
                t1 = each["df"].iloc[:, 0]
                y1 = each["df"].iloc[:, 1]
                param_list["time"] = int(each["df"].iloc[-1]["Time"])
                param_list["a"].append(
                    int(each["df"]["Intensity"].min()))
                param_list["b"].append(
                    int(each["df"]["Intensity"].max()))
            elif each["name"] == "A-Ch2":
                t2 = each["df"].iloc[:, 0]
                y2 = each["df"].iloc[:, 1]
                param_list["a"].append(
                    int(each["df"]["Intensity"].min()))
                param_list["b"].append(
                    int(each["df"]["Intensity"].max()))
            elif each["name"] == "AD1":
                t3 = each["df"].iloc[:, 0]
                y3 = each["df"].iloc[:, 1]
                param_list["c"] = int(each["df"]["Intensity"].min())
                param_list["d"] = int(each["df"]["Intensity"].max())
        if not param:
            param = {"a": min(param_list["a"]), "b": max(
                param_list["b"]), "c": param_list["c"], "d": param_list["d"], "time": param_list["time"]}
        ax = self.fig.add_subplot(3, 1, num)
        if 't3' in locals():  # RIがあった場合
            ax_2 = ax.twinx()
            ax.plot(t1, y1, color="gray", linewidth=0.8)
            ax_2.plot(t3, y3, color="black", linewidth=0.8)
            ax.set_ylim([param["a"], param["b"]])
            ax_2.set_ylim([param["c"], param["d"]])
            ax.set_xlim([0, param["time"]])
            ax_2.set_xlim([0, param["time"]])
        else:
            ax.plot(t1, y1, color="black", linewidth=0.8)
            ax.plot(t2, y2, color="gray", linewidth=0.8)
            ax.set_ylim([param["a"], param["b"]])
            ax.set_xlim([0, param["time"]])
        ax.set_title(self.data[num-1]["title"])
        self.fig.tight_layout()
        return param


def drow_graph(param):
    with open("data/data.json", "r") as f:
        all_data = json.load(f)
    df_data_list = []
    for each_data in all_data:
        title = each_data["file_name"]
        each_df = []
        for channel in each_data["content"]:
            df = pd.DataFrame(data=channel["data"], columns=[
                'Time', 'Intensity']).astype(float)
            name = channel["name"]
            each_df.append({"df": df, "name": name})

        data = {"title": title, "data": each_df}
        df_data_list.append(data)
    note = Note(df_data_list)
    return_param = []
    for i in range(len(all_data)):
        if param:
            return_each_param = note.mix(i+1, param[i])
        else:
            return_each_param = note.mix(i+1, False)
        return_param.append(return_each_param)

    note.fig.savefig("data/test.pdf")
    canvas = FigureCanvasAgg(note.fig)
    png_output = BytesIO()
    canvas.print_png(png_output)
    data = png_output.getvalue()

    img_data = urllib.parse.quote(data)

    return render_template('graph.html', img_data=img_data, param=return_param, size=len(all_data))


def save_pdf():
    response = make_response(open("data/test.pdf", "rb").read())
    response.headers['Content-Disposition'] = 'attachment; filename=test.pdf'
    response.mimetype = "application/pdf"
    return response


def save_txt(data_file):
    with open("data/data_file.txt", mode='w') as f:
        f.write(data_file.read().decode("shift_jis"))


@ app.route('/')
def index():
    return render_template('index.html')


@ app.route('/help')
def help():
    return render_template('help.html')


@ app.route('/save', methods=["POST"])
def save():
    return save_pdf()


@ app.route('/drowgraph', methods=["POST"])
def drowgraph_view():
    request_file_list = request.files.getlist("data_file")
    try:
        if len(request_file_list) > 0:
            # 最初の読み込み時
            if len(request_file_list) > 3:
                return render_template("index.html", message="一度に読み込めるファイルは3つまでです")
            elif request_file_list[0].filename == "":
                return render_template("index.html", message="ファイルを選択してください")
            elif len(request_file_list) > 0:
                file_content_list = []
                for file in request_file_list:
                    # 一旦1ファイル分だけ保存（直接開くと改行とかめんどい）
                    save_txt(file)
                    with open("data/data_file.txt", mode="r") as r:
                        file_content = r.read()
                    # 1ファイル分だけ読み込んで変数に格納
                    file_content_list.append(
                        {"data": file_content, "file_name": file.filename.split(".")[0]})
                save_json(file_content_list)

                param = []
        else:
            # 2回目以降
            param = []
            for i in range(int(request.form.get("size"))):
                time = int(request.form.get("time"+str(i)))
                a = int(request.form.get("a"+str(i)))
                b = int(request.form.get("b"+str(i)))
                c = int(request.form.get("c"+str(i)))
                d = int(request.form.get("d"+str(i)))
                param.append({"time": time, "a": a, "b": b, "c": c, "d": d})

        response = drow_graph(param)
        return response
    except ValueError:
        return render_template("index.html", message="クロマトグラムのデータが入ってないファイルがあります")


if __name__ == "__main__":
    app.run()
