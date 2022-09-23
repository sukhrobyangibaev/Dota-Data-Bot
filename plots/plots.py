import matplotlib.pyplot as plt
import io


def get_pie_plot(word_list):
    words = []
    counts = []
    for key, value in word_list.items():
        words.append(key)
        counts.append(value)

    fig, ax = plt.subplots()
    ax.pie(counts, labels=words)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf
