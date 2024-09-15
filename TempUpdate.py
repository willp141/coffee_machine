import uasyncio as asyncio # type: ignore
import onewire, ds18x20  # type: ignore
from machine import Pin # type: ignore
from machineManager import State

class tempTimer:
    def __init__(self, shared_data, getstate,target_temp, temp_tolerance, boiler_on, boiler_off):
        self.shared_data = shared_data
        self.period = 5
        self.task = None
        self.tstate = getstate
        
        # Controls
        self.boileron = boiler_on
        self.boileroff = boiler_off

        # Initialize Sensor
        self.onewire_pin = Pin(27)  # GPIO pin connected to DS18B20 data line
        self.temp_sensor = ds18x20.DS18X20(onewire.OneWire(self.onewire_pin))
        self.sensor_rom = self.temp_sensor.scan()  # Scan for all connected sensors
        self.current_temperature = 0  # Initialize current temperature
        print(f"     Found DS18B20 sensors: {self.sensor_rom}")

        # Target temperature range
        self.target_temp = target_temp
        self.temp_tolerance = temp_tolerance

    async def startTimer(self):
        """Begin Updating Shared Data"""
        print("Starting Temp Updates")
        try:
            while True:
                await self.update_temperature()
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
                    print(f"Current Boiler Temperature: {self.shared_data['temperature']}°C")
                except Exception as e:
                    print(f"Error reading temperature: {e}")
            current_state = self.tstate()
            # Control boiler heater based on temperature range
            if current_state == State.DEFAULT:
                print("State 0 Temp Handler No action")
            elif current_state == State.AUTO or State.GET_READY or State.PUMP or State.STEAM:
                if (self.current_temperature < (self.target_temp - self.temp_tolerance)):
                    self.boileron()  # Turn on heater
                    self.shared_data['heater_state'] = True
                    print("Temp Updated turned on heater")
                elif (self.current_temperature > (self.target_temp + self.temp_tolerance)):
                    self.boileroff()  # Turn off heater
                    self.shared_data['heater_state'] = False
                    print("Temp Updated turned off heater")
                else:
                    print("Temp Update left heater in current state")
            else:
                self.boileroff()  # Turn off heater
                self.shared_data['heater_state'] = False              
                print("Temp Update read invalid state, turned heater off.")
        except KeyboardInterrupt:
            print("Keyboard interrupt received. Shutting down...")
            self.boileroff()  # Turn off heater
            self.shared_data['heater_state'] = False              
            print("Turned heater off")
            self.shutdown()  # Call the shutdown function to handle any cleanup