import pexpect
import sys
sys.path.append('.')
sys.path.append('..')
import config

CAMERA_MAC = config.CAM_MAC_ADDRESS

index = 1
count = 0
while(index != 0 and count < 10):
    try:
        count += 1
        child = pexpect.spawn("gatttool -I")
        print("Connect to camera (bluetooth - deactivate WiFi)")
        child.sendline(f"connect {CAMERA_MAC}")
        index = child.expect("Connection successful", timeout=5)
        if index != 0:
            continue
        print("Camera's bluetooth connected")
        child.sendline("char-write-req 0x002e 4750494f32")
        index = child.expect("Characteristic value was written successfully", timeout=5)
        print("Camera's Wifi turned off (deactivate)")
        child.sendline("exit")

    except Exception as e: 
        print('Timeout waiting for bluetooth connecting')