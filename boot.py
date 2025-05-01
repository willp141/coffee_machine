######################################################
#   Author: Will Pryor
#   Project: Coffee Machine
#   Date: 9/8/2024
#   Description: Boot sequence to connect to Wi-Fi
######################################################

import network # type: ignore
import machine # type: ignore
import mip # type: ignore

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('thesinkingSub', 'itsonthefridge')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

do_connect()
mip.install("logging")
print("Boot Complete")