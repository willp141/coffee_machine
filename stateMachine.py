import uasyncio as asyncio
import time

class CoffeeState:
    IDLE = 'IDLE'
    HEAT = 'HEAT'
    READY_COFFEE = 'READY_COFFEE'
    PUMP = 'PUMP'
    READY_STEAM = 'READY_STEAM'
    ERROR = 'ERROR'

class CoffeeMachineState:
    def __init__(self, hardware):
        print('Initializing State Machine')
        self.state = CoffeeState.IDLE
        self.hw = hardware  # hardware interface class
        self.mode = 'coffee'  # or 'steam'
        self.target_temp = 199  # default to coffee temp (199F)

    async def run(self):
        print('Running State Machine')
        prev_state = None
        while True:
            try:
                if self.state != prev_state:
                    print(f"[STATE] → {self.state}")
                    prev_state = self.state

                if self.state == CoffeeState.IDLE:
                    await self.idle()
                elif self.state == CoffeeState.HEAT:
                    await self.heat()
                elif self.state == CoffeeState.READY_COFFEE:
                    await self.ready_coffee()
                elif self.state == CoffeeState.PUMP:
                    await self.pump()
                elif self.state == CoffeeState.READY_STEAM:
                    await self.ready_steam()
                elif self.state == CoffeeState.ERROR:
                    await self.error()
            except Exception as e:
                print(f"Exception: {e}")
                self.state = CoffeeState.ERROR
            await asyncio.sleep(0.1)

    # ---------------- STATES ----------------

    async def idle(self):
        if self.hw.admin_override:
            return
        
        self.hw.heater_off()
        self.hw.pump_off()

        if self.hw.requested_brew():
            self.mode = 'coffee'
            self.target_temp = 199  # Default coffee temp (199F)
            self.state = CoffeeState.HEAT

        elif self.hw.requested_steam():
            self.mode = 'steam'
            self.target_temp = 275  # Default steam temp (275F)
            self.state = CoffeeState.HEAT
        
        self.hw.clear_requests()

    async def heat(self):
        self.hw.control_temp(self.target_temp)
        current_temp = self.hw.get_temp(self.target_temp)

        if self.hw.requested_idle():
            self.state = CoffeeState.IDLE
        elif current_temp >= self.target_temp:
            if self.mode == 'coffee':
                self.state = CoffeeState.READY_COFFEE
            else:
                self.state = CoffeeState.READY_STEAM

        self.hw.clear_requests()

    async def ready_coffee(self):
        self.hw.control_temp(self.target_temp)

        current_temp = self.hw.get_temp(self.target_temp)

        if self.hw.requested_idle():
            self.state = CoffeeState.IDLE
        elif current_temp > self.target_temp + self.hw.temp_window:
            # Stay in READY_COFFEE, don't allow pump
            pass
        elif self.hw.requested_pump():
            print("Starting pump")
            self.state = CoffeeState.PUMP
        elif self.hw.requested_steam():
            self.mode = 'steam'
            self.target_temp = 135
            self.state = CoffeeState.HEAT

        self.hw.clear_requests()


    async def ready_steam(self):
        self.hw.control_temp(self.target_temp)

        timeout = 5 * 60  # 5 minutes
        start_time = time.time()

        while self.state == CoffeeState.READY_STEAM:
            self.hw.control_temp(self.target_temp)

            if self.hw.requested_idle():
                print("Cancel requested → IDLE")
                self.state = CoffeeState.IDLE
                break
            elif self.hw.steam_done():
                print("Steam complete → IDLE")
                self.state = CoffeeState.IDLE
                break
            elif time.time() - start_time > timeout:
                print("Timeout in READY_STEAM → IDLE")
                self.state = CoffeeState.IDLE
                break

            await asyncio.sleep(1)

        self.hw.clear_requests()

    async def pump(self):
        await self.hw.run_pump(duration=25)
        self.state = CoffeeState.READY_COFFEE

    async def error(self):
        self.hw.heater_off()
        self.hw.pump_off()
        self.hw.indicate_error()
        await asyncio.sleep(1)
