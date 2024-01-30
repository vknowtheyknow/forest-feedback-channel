from datetime import datetime
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import os
import json
import sys
sys.path.append('.')
sys.path.append('..')

import config

def get_service_logs(path):
    data = []
    log_files = sorted([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
    no_of_logs = len(log_files)
    data = []
    for fl in range(len(log_files)):
        if fl%1000 == 0:
            print(f'{fl}/{no_of_logs}')
        try:
            if log_files[fl].split('.')[1] == 'txt':
                f = open(path+log_files[fl])
                line = f.read().split('\n')[:-1]
                f.close()
            else:
                f = open(path+log_files[fl])
                line = json.load(f)
                f.close()
        except:
            print('Error open', path+log_files[fl])
            continue
        if log_files[fl].split('.')[1] == 'txt':
            for l in line:
                # print(l)
                ll = json.loads(l)
                ts = datetime.fromtimestamp(ll['time'])
                batt = ll['inputVoltage']   #from http request payload //camelCase
                data.append((ts,batt))
            continue
        ts = datetime.fromtimestamp(float(log_files[fl].split('.')[0]))
        batt = line['input_voltage']
        data.append((ts,batt))
    return data

fig = plt.figure()
fig, (ax1, ax2, ax3) = plt.subplots(3)
fig.suptitle(f'UNDP{config.RPI_ID}_{datetime.now().strftime("%d-%m-%y")}')

data = get_service_logs('./service_packet_buffer/rx/rx/uploaded/')
data.extend(get_service_logs('./service_packet_buffer/rx/rx/uploaded/'))
ts,batt = zip(*data)
ax1.plot(ts,batt, ',')
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d %H:%M'))
# ax1.set_ylabel('Battery Voltage')
ax1.grid(True)
ax1.set_title(f'RX{config.RPI_ID}')
ax3.plot(ts,batt, ',', label = 'RX')

data = get_service_logs('./service_packet_buffer/rx/received/uploaded/')
data.extend(get_service_logs('./service_packet_buffer/rx/received/'))
ts,batt = zip(*data)
ax2.plot(ts,batt, ',')
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d %H:%M'))
ax2.set_ylabel('Battery Voltage')
ax2.grid(True)
ax2.set_title(f'TX{config.RPI_ID}')

ax3.plot(ts,batt, ',', label = 'TX')
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d %H:%M'))
# ax3.set_ylabel('Battery Voltage')
ax3.grid(True)
ax3.set_title(f'RX-TX{config.RPI_ID}')

fig.autofmt_xdate()
plt.legend()
plt.savefig(f'UNDP{config.RPI_ID}_{datetime.now().strftime("%d-%m-%y")}.pdf')
#plt.show()
