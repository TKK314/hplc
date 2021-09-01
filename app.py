from matplotlib.backends.backend_pdf import PdfPages
from io import BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.pyplot as plt
from datetime import datetime, date
import re
from flask import Flask, render_template, request, redirect, flash, send_file, make_response, send_from_directory
from flask.helpers import make_response
from werkzeug.utils import secure_filename
import pandas as pd
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)


def transform(txt_data):
    pulify1 = re.split("\r\n\r\n", txt_data.split(
        'R.Time (min),Intensity')[1])[0]
    pulify2 = re.split("\r\n\r\n", txt_data.split(
        'R.Time (min),Intensity')[2])[0]
    da1 = []
    da2 = []

    for row in pulify1.splitlines():
        if row:
            da1.append([row.split(",")[0], row.split(",")[1]])
    for row in pulify2.splitlines():
        if row:
            da2.append([row.split(",")[0], row.split(",")[1]])

    df1 = pd.DataFrame(data=da1, columns=['Time', 'Intensity']).astype(float)
    df2 = pd.DataFrame(data=da2, columns=['Time', 'Intensity']).astype(float)
    data = [df1, df2]
    time, a, b = 35, -10000, 4000000
    fig = plt.figure()
    t1 = data[0].iloc[:, 0]
    t2 = data[1].iloc[:, 0]
    y1 = data[0].iloc[:, 1]
    y2 = data[1].iloc[:, 1]

    ax = fig.add_subplot(3, 1, 1)
    ax.plot(t1, y1, color="black", linewidth=0.8)
    ax.plot(t2, y2, color="gray", linewidth=0.8)
    ax.set_ylim([a, b])
    ax.set_xlim([0, time])
    fig.tight_layout()
    fig.savefig("test.pdf")

    response = make_response(open("test.pdf", "rb").read())
    response.headers['Content-Disposition'] = 'attachment; filename=test.pdf'
    response.mimetype = "application/pdf"
    return response


# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/transform', methods=["POST"])
def transform_view():
    app.logger.debug("________________________________________")
    request_file = request.files["data_file"]
    if not request_file:
        return "NO FILE"

    file_contents = request_file.read().decode('shift_jis')
    response = transform(file_contents)

    return response


if __name__ == "__main__":
    app.run()
