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
from audio import play_wav_file
from asyncAudio import play_wav_async
import time

import tinyweb


# Create web server application
app = tinyweb.webserver()

# Index page
@app.route('/')
async def index(req, resp):
    await resp.start_html()
    await resp.send_file('pages/index.html')

# Initialize Classes
# coffee_machine = CoffeeMachine()

# server = AsyncServer(
#     coffee_machine.requestHandler, 
#     coffee_machine.shared_data,
#     coffee_machine.getState
# )

# updateTemp = tempTimer(
#     coffee_machine.shared_data, 
#     coffee_machine.getState, 
#     coffee_machine.boiler.on, 
#     coffee_machine.boiler.off,
#     coffee_machine.check_state,
#     coffee_machine.getTemps
# )

# # Audio Test Branch
# def main():
#     # Play the WAV file    
#     # Ensure file exists before attempting playback
#     play_wav()
#     print("Played File")

# main()




# # asyncio Audio branch
# async def main():
#     await play_wav_async()

# asyncio.run(main())


# Main Code Branch
def run():
    print("starting webserver")
    app.run(host='127.0.0.1', port=8081)

# asyncio.run(main())

if __name__ == '__main__':
    run()
