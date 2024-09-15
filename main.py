################################################################################
#   Author: Will Pryor
#   Project: Coffee Machine
#   Date: 9/8/2024
#   Description: Initialize classes, start temp sensor, and run server.
################################################################################

# from server_functions import startServer, handle_request
from machineManager import CoffeeMachine
import asyncio
from asyncServer import AsyncServer
from TempUpdate import tempTimer
import machine # type: ignore
import os # type: ignore
import sdcard # type: ignore

# Initialize Classes
coffee_machine = CoffeeMachine()

cs = machine.Pin(16, machine.Pin.OUT)
cs.value(1)  # Deselect SD card (CS high)

# Initialize SPI bus for SD card
spi = machine.SPI(1, baudrate=50000, polarity=0, phase=0, sck=machine.Pin(5), mosi=machine.Pin(18), miso=machine.Pin(19))  # MISO

# Initialize the SD card and mount the filesystem
sd = sdcard.SDCard(spi, machine.Pin(16))  # CS pin connected to GPIO 16
vfs = os.VfsFat(sd)
os.mount(vfs, '/sd')


server = AsyncServer(
    coffee_machine.requestHandler, 
    coffee_machine.shared_data,
    coffee_machine.getState
)

updateTemp = tempTimer(
    coffee_machine.shared_data, 
    coffee_machine.getState, 
    coffee_machine.target_temp, 
    coffee_machine.temp_tolerance, 
    coffee_machine.boiler.on, 
    coffee_machine.boiler.off
)

async def main():
    asyncio.create_task(updateTemp.startTimer())
    await server.start_server()

asyncio.run(main())
