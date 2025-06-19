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

	# ---------- TEMP CONTROL ----------

	async def control_temp_heat(self, target_temp):
		temp = self.last_temp

		# Thresholds
		window = 5 # 5 Degree F window for control

		# Determine if we are in steam mode or coffee mode
		if target_temp >= 250:
			# Steam mode control
			overshoot_comp = 30

			if temp >= target_temp - overshoot_comp:
				# Enter pulse mode near target
				self.heater_on()
				await asyncio.sleep(5)
				self.heater_off()
				await asyncio.sleep(5)
			else:
				# Below target - overshoot compensation: full heater ON
				self.heater_on()

		else:
			# Coffee mode control
			overshoot_comp = 22

			if temp >= target_temp - overshoot_comp:
				self.heater_off()
			elif temp <= target_temp - window:
				self.heater_on()

	async def control_temp_ready(self, target_temp):
		temp = self.last_temp
		tight_window = 4  # Steady state control window

		if target_temp <= 250:
			# Coffee mode control
			if temp >= target_temp + tight_window:
				self.heater_off()
			elif temp <= target_temp - tight_window: # Burst Heating method instead of waiting for temp sensor to respond.
				self.heater_on()
				await asyncio.sleep(3)
				self.heater_off()
				await asyncio.sleep(5)
		elif target_temp > 250:
			# Steam mode bounce control
			if temp > 260:
				self.heater_off()
			elif temp <= 260:
				print("Steam heat pulse")
				asyncio.create_task(self.steam_pulse())

	async def steam_pulse(self):
		self.heater_on()
		await asyncio.sleep(10)
		self.heater_off()

	# ---------- TEMP SENSOR ----------

	def get_temp(self, target=None):
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
			self.heater_on()
			self.set_led(True)
			await asyncio.sleep(duration)
			self.pump_pin.off()
			self.heater_off()
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