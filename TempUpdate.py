import uasyncio as asyncio # type: ignore
import onewire, ds18x20  # type: ignore
from machine import Pin # type: ignore
from machineManager import State

class tempTimer:
    def __init__(self, shared_data, getstate, boiler_on, boiler_off, check_state, get_temps):
        self.shared_data = shared_data
        self.period = 3 # reduce period from 5 - 3 second
        self.task = None
        self.tstate = getstate
        self.check_state = check_state
        self.get_temps = get_temps
        # Controls
        self.boileron = boiler_on
        self.boileroff = boiler_off

        # Initialize Sensor
        self.onewire_pin = Pin(27)  # GPIO pin connected to DS18B20 data line
        self.temp_sensor = ds18x20.DS18X20(onewire.OneWire(self.onewire_pin))
        self.sensor_rom = self.temp_sensor.scan()  # Scan for all connected sensors
        print(f"     Found DS18B20 sensors: {self.sensor_rom}")

        # Target temperature range
        self.target_temp = self.shared_data['target_temp']
        self.temp_tolerance = self.shared_data['temp_tolerance']
        print("     Init Temp: self.target_temp is: ", self.target_temp)
        print("     Init Temp: self.temp_tolerance is: ", self.temp_tolerance)

    async def startTimer(self):
        """Begin Updating Shared Data"""
        print("Starting Temp Updates")
        try:
            while True:
                await self.update_temperature()
                # await self.check_state() # New line of code to force recheck of temp and state every 1 second
                await asyncio.sleep(self.period)
        except asyncio.CancelledError:
            print("Temperature update task canceled.")
        
    async def update_temperature(self, timer=None):
        """Read temperature from DS18B20 sensor and update current temperature."""

        try:
            if self.sensor_rom:
                # Request temperature conversion
                self.temp_sensor.convert_temp()
                #time.sleep(0.75)  # Wait for the conversion to complete
                await asyncio.sleep(0.75)

                # Read temperature from the first sensor in the list (or iterate if multiple sensors)
                try:
                    self.shared_data['temperature'] = self.temp_sensor.read_temp(self.sensor_rom[0])

                except Exception as e:
                    print(f"Error reading temperature: {e}")
            current_state = self.tstate()
            current_target_temp, current_temp_tolerance = self.get_temps()

            print(f"     update_temparature: Current Boiler Temperature: {self.shared_data['temperature']}°C")
            print(f"     update_temparature: Current Shared State: {self.shared_data['shared_state']}")
            print(f"     update_temparature: Current tstate: {current_state}")
            print(f"     update_temparature: current_target_temp is: {current_target_temp}")
            print(f"     update_temparature: current_temp_tolerance is: {current_temp_tolerance}")

            # Control boiler heater based on temperature range
            if current_state == State.DEFAULT:
                print("     update_temparature: State 0 No action")
            elif current_state == State.AUTO or State.GET_READY or State.PUMP or State.STEAM:
                goal = (current_target_temp - current_temp_tolerance)
                print(f"     update_temparature: Goal temp: {goal}")
                if (self.shared_data['temperature'] < (current_target_temp - current_temp_tolerance)):
                    self.boileron()  # Turn on heater
                    self.shared_data['heater_state'] = True
                    print("     update_temparature: Temp Updated turned on heater")
                elif (self.shared_data['temperature'] >= (current_target_temp + current_temp_tolerance)):
                    self.boileroff()  # Turn off heater
                    self.shared_data['heater_state'] = False
                    print("     update_temparature: Temp Updated turned off heater")
                else:
                    print("     update_temparature: Temp Update left heater in current state")
            else:
                self.boileroff()  # Turn off heater
                self.shared_data['heater_state'] = False              
                print("     update_temparature: Temp Update read invalid state, turned heater off.")
        except KeyboardInterrupt:
            print("Keyboard interrupt received. Shutting down...")
            self.boileroff()  # Turn off heater
            self.shared_data['heater_state'] = False              
            print("     update_temparature: Turned heater off")
            # self.shutdown()  # Call the shutdown function to handle any cleanup, no longer defined>