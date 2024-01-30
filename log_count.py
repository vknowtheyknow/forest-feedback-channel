import sys
filename = sys.argv[1]
#filename = input()
f = open(filename)
txt = f.read()
f.close()
lines = txt.split('\n')[5:]
board = []
for i in range(4):
    board.append({
        'name': '#'+str(i),
        'RSSI': []
    })
for i in range(len(lines)):
    if lines[i][:6] == '[Board':
        rssi = lines[i+1].split(' ')
        board[int(lines[i][6])]['RSSI'].append(int(rssi[2]))
print('# \tPkt received\tRSSI min\tRSSI arv\tRSSI max')
for b in board:
    #print('-'*50)
    print(b['name'], end='\t')
    if not b['RSSI']:
        print('lost')
        continue
    print(f"{len(b['RSSI']):12}\t{min(b['RSSI']):8}\t{sum(b['RSSI'])/len(b['RSSI']):8.3f}\t{max(b['RSSI']):8}")
