import matplotlib.pyplot as plt
import io


def get_pie_plot(word_list):
    words = []
    counts = []
    for key, value in word_list.items():
        words.append(key)
        counts.append(value)
    plt.pie(counts, labels=words)
    plt.title('Wordcloud')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.clf()
    return buf


def get_peers_plot(peers):
    plt.barh(peers['players'], peers['games'], label='games played overall')
    plt.barh(peers['players'], peers['won'], label='win percentage')

    for i in range(len(peers['players'])):
        plt.text(peers['games'][i] * 0.9, peers['players'][i], peers['games'][i], ha='center', color='black')
        plt.text(peers['won'][i] * 0.9, peers['players'][i], peers['won_percent'][i], ha='center', color='black')
    plt.title('Peers')
    plt.xlabel('Players')
    plt.ylabel('Games played')
    plt.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.clf()
    return buf
