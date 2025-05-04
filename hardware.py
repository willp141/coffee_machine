import machine
import time
import uasyncio as asyncio

class CoffeeMachineHardware:
	def __init__(self):
		# GPIO setup
		self.heater_pin = machine.Pin(12, machine.Pin.OUT)
		self.pump_pin = machine.Pin(13, machine.Pin.OUT)
		# self.temp_sensor = ...  # your DS18B20 or thermistor wrapper
		self.shared_state = {
			'brew_request': False,
			'pump_request': False,
			'steam_request': False,
			'idle_request': False,
			'steam_done': False,
		}
		# Temp control parameters
		self.temp_window = 5  # degrees C around target

		# TEST VARIABLES
		self._fake_temp = 85
		self.led = machine.Pin(2, machine.Pin.OUT)

	# ---------- TEST LED ----------
	def set_led(self, state: bool):
		self.led.value(1 if state else 0)

	# ---------- HEATER CONTROL ----------
	def heater_on(self):
		self.heater_pin.on()
		# TEST LED
		self.set_led(True)

	def heater_off(self):
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
		if target is not None and self._fake_temp < target:
			self._fake_temp += 0.2
		return self._fake_temp
		# return self.temp_sensor.read()  # implement this later

	# ---------- PUMP CONTROL ----------
	async def run_pump(self, duration):
		self.pump_pin.on()
		self.set_led(True)
		await asyncio.sleep(duration)
		self.pump_pin.off()
		self.set_led(False)

	def pump_off(self):
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