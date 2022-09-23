import io
import csv
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns


plt.xticks(rotation=35)
sns.set()
sns.set_style("ticks")
sns.set_style("whitegrid")
dates_fmt = mdates.DateFormatter('%d %b')


def get_quizes_plot(quizes):
    fig, ax = plt.subplots()
    ax.xaxis.set_major_formatter(dates_fmt)
    for type_ in ('hars', 'madrs'):
        x = [datetime.strptime(quiz.created_at, '%Y-%m-%d %H-%M-%S') for quiz in quizes if quiz.type_ == type_]
        y = [quiz.result for quiz in quizes if quiz.type_ == type_]
        ax.plot(x, y, label=type_.upper())
    ax.legend()
    sns.despine()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf