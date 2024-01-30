import pexpect

try:
    print('Disconnecting Wifi')
    child = pexpect.spawn("wpa_cli -i wlan0")
    child.expect(">", timeout=10)
    child.sendline("disconnect")
    child.expect("OK", timeout=5)
    print('Wifi disconnected')
except:
    print('Error disconnecting wifi')