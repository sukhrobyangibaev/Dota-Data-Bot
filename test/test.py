# 想像力상상력想像力—— —— — - games 501, winrate 63%
# me sleeping - games 490, winrate 64%
# Довольный - games 429, winrate 65%
# demon1999- - games 332, winrate 65%
# 3412ztqezwiujqzwaedo-0k - games 267, winrate 50%
# iwlufmbkv - games 237, winrate 54%
# jlhtc - games 223, winrate 60%
# Switchback - games 219, winrate 47%
# MOM LOOK I CAN PLAY UNDYING) - games 217, winrate 53%
# tv/Shergarat (Vladimir) - games 205, winrate 53%

import matplotlib.pyplot as plt

players = ['想像力상상력想像力—— —— —', 'me sleeping', 'Довольный', 'demon1999']
games = [501, 490, 429, 332]
winrate = [63, 64, 65, 65]

ax = plt.subplot()
# plt.bar()
ax.bar(players, games, color='b')
ax.bar(players, winrate, color='g')
for i in range(len(players)):
    ax.text(players[i], games[i] + 5, "asd", ha='center', color='black')
    ax.text(players[i], winrate[i] + 5, "asd", ha='center', color='white')

plt.show()