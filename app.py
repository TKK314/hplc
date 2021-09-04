from io import BytesIO
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
            raw_data = channel.split("R.Time (min),Intensity\n")[
                1].split("\n\n")[0]
            data = []
            for row in raw_data.splitlines():
                if row:
                    data.append([row.split(",")[0], row.split(",")[1]])
            channel_data = {"name": name, "data": data}
            each_array_data["content"].append(channel_data)
        save_array_data.append(each_array_data)
    with open("data/data.json", "w") as f:
        json.dump(save_array_data, f, indent=2)


class Note:
    def __init__(self, data):
        self.fig = plt.figure()
        self.data = data

    def mix(self, num, time, a, b):
        t1 = self.data[num-1]["data"][0].iloc[:, 0]
        t2 = self.data[num-1]["data"][1].iloc[:, 0]
        y1 = self.data[num-1]["data"][0].iloc[:, 1]
        y2 = self.data[num-1]["data"][1].iloc[:, 1]

        ax = self.fig.add_subplot(3, 1, num)
        ax.plot(t1, y1, color="black", linewidth=0.8)
        ax.plot(t2, y2, color="gray", linewidth=0.8)
        ax.set_ylim([a, b])
        ax.set_xlim([0, time])
        ax.set_title(self.data[num-1]["title"])
        self.fig.tight_layout()


def drow_graph(param):
    with open("data/data.json", "r") as f:
        all_data = json.load(f)
    df_data_list = []
    for each_data in all_data:
        title = each_data["file_name"]
        df1 = pd.DataFrame(data=each_data["content"][0]["data"], columns=[
                           'Time', 'Intensity']).astype(float)
        df2 = pd.DataFrame(data=each_data["content"][1]["data"], columns=[
                           'Time', 'Intensity']).astype(float)
        data = {"title": title, "data": [df1, df2]}
        time = int(df1.iloc[-1]["Time"])
        a = int(min(df1["Intensity"].min(), df2["Intensity"].min()))
        b = int(max(df1["Intensity"].max(), df2["Intensity"].max()))
        param.append({"time": time, "a": a, "b": b})
        # 最初はparamが[]であるため必要な分がきちんと追加される
        # 2回目以降は4つめ以降に追加されるから参照されなくなる
        df_data_list.append(data)
    note = Note(df_data_list)
    for i in range(len(all_data)):
        note.mix(i+1, param[i]["time"], param[i]["a"], param[i]["b"])

    note.fig.savefig("data/test.pdf")
    canvas = FigureCanvasAgg(note.fig)
    png_output = BytesIO()
    canvas.print_png(png_output)
    data = png_output.getvalue()

    img_data = urllib.parse.quote(data)
    return render_template('graph.html', img_data=img_data, param=param, size=len(all_data))


def save_pdf():
    response = make_response(open("data/test.pdf", "rb").read())
    response.headers['Content-Disposition'] = 'attachment; filename=test.pdf'
    response.mimetype = "application/pdf"
    return response


def save_txt(data_file):
    with open("data/data_file.txt", mode='w') as f:
        f.write(data_file.read().decode("shift_jis"))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/help')
def help():
    return render_template('help.html')


@app.route('/save', methods=["POST"])
def save():
    return save_pdf()


@app.route('/drowgraph', methods=["POST"])
def drowgraph_view():
    request_file_list = request.files.getlist("data_file")

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
            param.append({"time": time, "a": a, "b": b})
    response = drow_graph(param)

    return response


if __name__ == "__main__":
    app.run()
