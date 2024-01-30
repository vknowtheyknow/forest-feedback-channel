import pexpect
import sys
sys.path.append('.')
sys.path.append('..')
import config

CAM_SSID = config.CAM_SSID
CAM_PSK = config.CAM_PSK

index = 1
child = pexpect.spawn("wpa_cli -i wlan0")
child.expect(">", timeout=10)
child.sendline("disconnect")
child.expect("OK", timeout=5)
child.sendline("select_network 0")
try:
    child.expect("OK", timeout=5)
    print('Network selected')
except:
    child.sendline("add_network")
    child.expect(">", timeout=5)
    print('Network added')
child.sendline(f'set_network 0 ssid "{CAM_SSID}"')
child.expect("OK", timeout=5)
child.sendline(f'set_network 0 psk "{CAM_PSK}"')
child.expect("OK", timeout=5)
    
count = 0
while(index != 0 and count < 10):
    try:
        count += 1
        print("Connecting Wifi")
        child.sendline("select_network 0")
        index = child.expect("<3>CTRL-EVENT-CONNECTED", timeout=15)
        if index != 0:
            continue
        print("Wifi connected")
        # child.sendline("scan_results") 

    except Exception as e:
        print('Timeout waiting for Wifi connecting')