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

		# Heater Pulse control variables
		self.pulse_active = False
		self.pulse_end_time = 0
		self.pulse_armed = False

		# TEST & SIMULATION VARIABLES
		self._fake_temp = 85
		self.led = machine.Pin(2, machine.Pin.OUT)
		self.admin_override = False
		
		self.simulate_temp = False  # Turn on simulation mode for software-only testing
		self.sim_temp = 160         # Starting simulated temp
		self.sim_heating_rate = 1.0  # Degrees F per second when heater on
		self.sim_cooling_rate = 0.5  # Degrees F per second when heater off
		self.sim_last_update = time.time()

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

	# Heat mode with overshoot compensation - steam and coffee modes
	async def control_temp_heat(self, target_temp):
		temp = self.last_temp
		# Thresholds
		window = 5 # 5 Degree F window for control
		# Determine if we are in steam mode or coffee mode
		if target_temp >= 250:
			# Steam mode control
			overshoot_comp = 26
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
			if self.simulate_temp == True:
				print(f"[CONTROL HEAT] Heating to {target_temp}F")
				overshoot_comp = 0
				if temp >= target_temp - overshoot_comp:
					self.heater_off()
				elif temp <= target_temp - window:
					self.heater_on()
			else:	
				overshoot_comp = 22
				if temp >= target_temp - overshoot_comp:
					self.heater_off()
				elif temp <= target_temp - window:
					self.heater_on()

	# BANG BANG Control for Coffee and Steam steady state modes
	def control_temp_ready(self, target_temp):
		temp = self.last_temp
		now = time.time()
		tight_window = 4

		if temp >= target_temp:
			self.pulse_armed = True

		print(f"[CONTROL] Temp={temp:.1f}F | Target={target_temp}F | PulseActive={self.pulse_active} | PulseArmed={self.pulse_armed}")
		# Coffee Mode
		if target_temp <= 250:
			if temp > target_temp - tight_window:
				self.pulse_armed = True
				self.heater_off()
				self.pulse_active = False

			elif temp <= target_temp - tight_window:
				if self.pulse_armed and not self.pulse_active:
					print("Starting coffee pulse")
					self.heater_on()
					self.pulse_active = True
					self.pulse_end_time = now + 15 # Pulse for 15 seconds
					self.pulse_armed = False  # Disarm until temp rises again

			if self.pulse_active and now >= self.pulse_end_time:
				self.heater_off()
				self.pulse_active = False

		# Steam Mode
		else:
			if temp >= 260:
				self.pulse_armed = True
				self.heater_off()
				self.pulse_active = False

			elif temp <= 260:
				if self.pulse_armed and not self.pulse_active:
					print("Starting steam pulse")
					self.heater_on()
					self.pulse_active = True
					self.pulse_end_time = now + 10
					self.pulse_armed = False

			if self.pulse_active and now >= self.pulse_end_time:
				self.heater_off()
				self.pulse_active = False

	# ---------- TEMP SENSOR ----------

	def get_temp(self, target=None):
		return self.last_temp

	async def temp_poll_loop(self):
		while True:
			if self.simulate_temp:
				self.update_simulated_temp()
			else:
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

	# ---------- Simulated Temperature Update ----------
	def update_simulated_temp(self):
		now = time.time()
		delta_t = now - self.sim_last_update
		self.sim_last_update = now

		if self.heater_pin.value():  # Heater is on
			self.sim_temp += self.sim_heating_rate * delta_t
		else:
			self.sim_temp -= self.sim_cooling_rate * delta_t

		# Bound temp (just to avoid runaway)
		self.sim_temp = max(70, min(300, self.sim_temp))

		self.last_temp = self.sim_temp