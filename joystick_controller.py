import Gamepad
import cobs.cobs
import rc_channels_pb2
import socket
import time

deadband = 0.07
if __name__ == "__main__":
    axis = {0:0, 1:0, 4:0, 5:0}
    msg = rc_channels_pb2.RCChannels()
    field = ["rc1", "rc2", "rc3", "rc4", "rc5", "rc6", "rc7", "rc8", "rc9",
             "rc10", "rc11", "rc12", "rc13", "rc14", "rc15", "rc16"]
    # 2000 = true, 1000 = false
    MAX_VALUE = 2000
    MIN_VALUE = 1000

    # UDP
    UDP_IP = "127.0.0.1"
    UDP_PORT = 5005

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        time.sleep(5)
        print("controller not connected ....")
        if Gamepad.available():
            gamepad = Gamepad.XboxONE()
            print("controller connected")
            break
    try:
        while True:
            eventType, control, value = gamepad.getNextEvent()
            if eventType == 'BUTTON':
                if control == 'A':
                    if value:
                        msg.rc1 = MAX_VALUE
                    else:
                        msg.rc1 = MIN_VALUE
                if control == 'B':
                    if value:
                        msg.rc2 = MAX_VALUE
                    else:
                        msg.rc2 = MIN_VALUE    
                if control == 'X':
                    if value:
                        msg.rc3 = MAX_VALUE
                    else:
                        msg.rc3 = MIN_VALUE
                if control == 'Y':
                    if value:
                        msg.rc4 = MAX_VALUE
                    else:
                        msg.rc4 = MIN_VALUE
                if control == 'LB':
                    if value:
                        msg.rc5 = MAX_VALUE
                    else:
                        msg.rc5 = MIN_VALUE
                if control == 'RB':
                    if value:
                        msg.rc6 = MAX_VALUE
                    else:
                        msg.rc6 = MIN_VALUE
                if control == 'LASB':
                    if value:
                        msg.rc9 = MAX_VALUE
                    else:
                        msg.rc9 = MIN_VALUE
                if control == 'RASB':
                    if value:
                        msg.rc10 = MAX_VALUE
                    else:
                        msg.rc10 = MIN_VALUE
            # 1000 to 2000 with 1500 being neutral
            if eventType == 'AXIS':
                if control == 'LAS -X':
                    speed = -value
                    msg.rc11 = int(1500 + (speed * 500))
                if control == 'LAS -Y':
                    steering = value
                    msg.rc12 = int(1500 + (steering * 500))
                if control == 'RAS -X':
                    speed = -value
                    msg.rc13 = int(1500 + (speed * 500))
                if control == 'RAS -Y':
                    steering = value
                    msg.rc14 = int(1500 + (steering * 500))
                if control == 'RT':
                    trigger = int(1500 + (value * 500))
                    msg.rc15 = trigger
                if control == 'LT':
                    trigger = int(1500 + (value * 500))
                    msg.rc16 = trigger
                if control == 'DPAD -X':
                    button = int(1500 + (value * 500))
                    msg.rc7 = button
                if control == 'DPAD -Y':
                    button = int(1500 + (value * 500))
                    msg.rc8 = button
            buffer = bytearray(cobs.cobs.encode(msg.SerializeToString())+bytes([0]))
            sock.sendto(buffer, (UDP_IP, UDP_PORT))
    except BaseException as e:
        # raise e
        default_value = 1500
        for field_name in field:
            setattr(msg, field_name, 1500)
        buffer = bytearray(cobs.cobs.encode(msg.SerializeToString())+bytes([0]))
        sock.sendto(buffer, (UDP_IP, UDP_PORT))