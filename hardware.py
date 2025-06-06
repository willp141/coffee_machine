import machine
import time
import uasyncio as asyncio
import ds18x20
import onewire
class CoffeeMachineHardware:
	def __init__(self):
		# GPIO setup
		self.heater_pin = machine.Pin(12, machine.Pin.OUT)
		self.pump_pin = machine.Pin(13, machine.Pin.OUT)
		self.shared_state = {
			'brew_request': False,
			'pump_request': False,
			'steam_request': False,
			'idle_request': False,
			'steam_done': False,
		}
		# Temp control parameters
		self.temp_window = 5  # degrees C around target

		# DS18B20 setup
		self.onewire_pin = machine.Pin(27)
		self.temp_sensor = ds18x20.DS18X20(onewire.OneWire(self.onewire_pin))
		roms = self.temp_sensor.scan()
		if roms:
			self.sensor_rom = roms[0]  # Use first sensor found
			print("DS18B20 detected:", self.sensor_rom)
		else:
			self.sensor_rom = None
			print("No DS18B20 sensor found!")
		self.last_temp = 85  # Fallback / fake default

		# TEST VARIABLES
		self._fake_temp = 85
		self.led = machine.Pin(2, machine.Pin.OUT)
		self.admin_override = False

	# ---------- TEST LED ----------
	def set_led(self, state: bool):
		self.led.value(1 if state else 0)

	# ---------- HEATER CONTROL ----------
	def heater_on(self):
		if not self.admin_override:
			self.heater_pin.on()
			# TEST LED
			self.set_led(True)

	def heater_off(self):
		if not self.admin_override:
			self.heater_pin.off()
			# TEST LED
			self.set_led(False)

	def control_temp(self, target_temp):
		temp = self.get_temp(target_temp)
		if temp < target_temp - self.temp_window:
			self.heater_on()
		elif temp > target_temp + self.temp_window:
			self.heater_off()

	# ---------- TEMP SENSOR ----------

	def get_temp(self, target=None):
		# if target is not None:
		# 	if self._fake_temp < target:
		# 		self._fake_temp += 0.2
		# 	elif self._fake_temp > target:
		# 		self._fake_temp -= 0.3
		# # Always return current temp
		# return self._fake_temp
		# return self.temp_sensor.read()  # implement this later
		return self.last_temp

	async def temp_poll_loop(self):
		while True:
			if self.sensor_rom:
				try:
					self.temp_sensor.convert_temp()
					await asyncio.sleep_ms(750)  # Wait for conversion
					# Read temperature in Celsius and convert to Fahrenheit
					temp_c = self.temp_sensor.read_temp(self.sensor_rom)
					if isinstance(temp_c, (float, int)):
						self.last_temp = temp_c * 9 / 5 + 32  # Convert to Fahrenheit
				except Exception as e:
					print("Temp read failed:", e)
			await asyncio.sleep(2)

	# ---------- PUMP CONTROL ----------
	async def run_pump(self, duration):
		if not self.admin_override:
			self.pump_pin.on()
			self.set_led(True)
			await asyncio.sleep(duration)
			self.pump_pin.off()
			self.set_led(False)

	def pump_off(self):
		if not self.admin_override:
			self.pump_pin.off()
			self.set_led(False)

	# ---------- INPUT SIGNALS ----------
	def requested_brew(self):
		return self.shared_state['brew_request']

	def requested_pump(self):
		return self.shared_state['pump_request']

	def requested_steam(self):
		return self.shared_state['steam_request']

	def requested_idle(self):
		return self.shared_state['idle_request']

	def steam_done(self):
		return self.shared_state['steam_done']
	
	def clear_requests(self):
		for key in self.shared_state:
			self.shared_state[key] = False

	# ---------- Error Handling ----------
	def indicate_error(self):
		# Blink LED
		for _ in range(3):
			self.set_led(True)
			time.sleep(0.2)
			self.set_led(False)
			time.sleep(0.2)
		print("ERROR: Something went wrong!")