import tinyweb
import ujson

app = tinyweb.webserver()

def setup_routes(hw, state_machine):
	@app.route('/')
	async def index(req, resp):
		await resp.send_file('pages/index.html')

	@app.route('/status')
	async def status(req, resp):
		data = {
			'temp': hw.get_temp(),
			'state': state_machine.state,
			'target_temp': state_machine.target_temp
		}
		json_str = ujson.dumps(data)
		headers = 'HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n'
		await resp.writer.awrite(headers + json_str)

	@app.route('/heat')
	async def heat(req, resp):
		hw.shared_state['brew_request'] = True
		await resp.send("Heating started")

	@app.route('/pump')
	async def pump(req, resp):
		hw.shared_state['pump_request'] = True
		await resp.send("Pump activated")

	@app.route('/steam')
	async def steam(req, resp):
		hw.shared_state['steam_request'] = True
		await resp.send("Steam mode activated")

	@app.route('/cancel')
	async def cancel(req, resp):
		hw.shared_state['idle_request'] = True
		await resp.send("System cancelled")

	@app.route('/steam_done')
	async def steam_done(req, resp):
		hw.shared_state['steam_done'] = True
		await resp.send("Steam complete")

	#DEBUG ROUTES for testing and debugging
	@app.route('/debug')
	async def debug(req, resp):
		data = {
			'state': state_machine.state,
			'temp': hw.get_temp(),
			'shared_state': hw.shared_state,
			'target_temp': state_machine.target_temp,
			'heater_on': hw.heater_pin.value(),
			'pump_on': hw.pump_pin.value()
		}
		json_str = ujson.dumps(data)
		headers = 'HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n'
		await resp.writer.awrite(headers + json_str)

	# ADMIN ROUTES for manual control
	@app.route('/admin/pump_on')
	async def admin_pump_on(req, resp):
		hw.admin_override = True
		hw.pump_pin.on()
		hw.set_led(True)
		await resp.send("Pump manually turned on")

	@app.route('/admin/pump_off')
	async def admin_pump_off(req, resp):
		hw.pump_pin.off()
		hw.set_led(False)
		await resp.send("Pump manually turned off")

	@app.route('/admin/boiler_on')
	async def admin_boiler_on(req, resp):
		hw.admin_override = True
		hw.heater_pin.on()
		hw.set_led(True)
		await resp.send("Boiler manually turned on")

	@app.route('/admin/boiler_off')
	async def admin_boiler_off(req, resp):
		hw.heater_pin.off()
		hw.set_led(False)
		await resp.send("Boiler manually turned off")

	# Optional: a button to clear override
	@app.route('/admin/override_off')
	async def admin_override_off(req, resp):
		hw.admin_override = False
		await resp.send("Admin override disabled")



def run_server(hw, state_machine):
	setup_routes(hw, state_machine)
	print('RUNNING SERVER')
	return app.run(host='0.0.0.0', port=80)