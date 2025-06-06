################################################################################
#   Author: Will Pryor
#   Project: Coffee Machine
#   Date: 9/8/2024
#   Description: Initialize classes, start temp sensor, and run server.
################################################################################

import uasyncio as asyncio
from hardware import CoffeeMachineHardware
from stateMachine import CoffeeMachineState
from asyncServer import run_server

# Initialize hardware control and state machine
hw = CoffeeMachineHardware()
state_machine = CoffeeMachineState(hw)

# Main event loop
async def main():
	await asyncio.gather(
		asyncio.create_task(state_machine.run()),  # Start State Machine
		asyncio.create_task(hw.temp_poll_loop()),  # start Temp updater
		run_server(hw, state_machine) # Blocks forever
	)

# Start everything
if __name__ == '__main__':
	asyncio.run(main())
	

##### OLD CODE
    # from TempUpdate import tempTimer
    # import machine # type: ignore
    # import os # type: ignore
    # import sdcard # type: ignore
    # from audio import play_wav_file
    # from asyncAudio import play_wav_async
    # import time
    # import asyncio
    # from server_functions import startServer, handle_request
    # from machineManager import CoffeeMachine
    # from asyncServer import AsyncServer

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
    # asyncio.run(main())
