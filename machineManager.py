######################################################
#   Author: Will Pryor
#   Project: Coffee Machine
#   Date: 9/8/2024
#   Description: Functionality Moved to machineManager
######################################################

from machine import Pin # type: ignore
import time
import asyncio

class State:
    DEFAULT = 0
    AUTO = 1
    GET_READY = 2
    PUMP = 3
    STEAM = 4

class CoffeeMachine:
    def __init__(self):
        print("Machine Class Initializing")
        print("     Setting State to Default")
        self.state = State.DEFAULT
        print("     Buttons and Variables Initializing")
        self.buttons = {
            'mAUTOMATIC_BUTTON': False,
            'mHEAT_WAIT_BUTTON': False,
            'mIM_READY_BUTTON': False,
            'mWANT_STEAM_BUTTON': False,
            'mDEFAULT_BUTTON': False,
            'mGO_TO_WAIT': False,
            'mCANCEL_BUTTON': False,
            'mPUMP_State': False,
            'mBOILER_State': False
        }

        # Shared data between the server and the coffee machine logic
        self.shared_data = {
            'temperature': 75,  # Example temperature
            'pump_state': False,  # Pump is initially off
            'heater_state': False,  # Heater is initially off
            'target_temp': 95, # If this updated, also need to update in default state handler
            'temp_tolerance': 5, # If this updated, also need to update in default state handler
            'mpump_on_time': 5,
            'shared_state': 0
        }
        
        print("     Buttons Initialized")
        self.sse_clients = []  # Store connected SSE clients
        print("     SSE Clients Initialized")
        print("     GPIO Pins Initializing")
        self.pump = Pin(13, Pin.OUT)  # GPIO Pin for PUMP 
        self.boiler = Pin(12, Pin.OUT)  # GPIO Pin for BOILER
        
        print("     GPIO Pins Initialized")

        # # Target temperature range
        self.target_temp = 95
        self.temp_tolerance = 5

        print("Machine Class Initialized")

    def getState(self):
        current_state = self.state
        # print(f"     Get State function returns {current_state}")
        return current_state

    def update_button(self, button_name, button_state):
        """ Update button states and check transitions """
        if button_name in self.buttons:
            self.buttons[button_name] = button_state
            self.check_state()

    def check_state(self):
        """ Check current state and handle transitions """
        if self.state == State.DEFAULT:
            self.handle_default_state()
        elif self.state == State.AUTO:
            self.handle_auto_state()
        elif self.state == State.GET_READY:
            self.handle_heat_wait_state()
        elif self.state == State.PUMP:
            self.handle_run_pump_state()
        elif self.state == State.STEAM:
            self.handle_steam_state()
        return

    def handle_default_state(self):
        """ State 0: DEFAULT """
        self.shared_data['shared_state'] = State.DEFAULT
        # Reset defaults if returning from steam state
        if self.shared_data['target_temp'] == 120:
            self.shared_data['target_temp'] = 95
            self.shared_data['temp_tolerance'] = 5

        # Check buttons
        if self.buttons['mAUTOMATIC_BUTTON']:
            self.state = State.AUTO
            self.buttons['mAUTOMATIC_BUTTON'] = False
            self.buttons['mPUMP_State'] = False
            self.buttons['mBOILER_State'] = False
        elif self.buttons['mHEAT_WAIT_BUTTON']:
            self.state = State.GET_READY
            self.buttons['mHEAT_WAIT_BUTTON'] = False
            self.buttons['mPUMP_State'] = False
            self.buttons['mBOILER_State'] = False

        # Handle pump toggle - TEST CODE
        if self.buttons['mPUMP_State']:
            if self.shared_data['pump_state']:  # Pump is currently ON, turn it OFF
                self.pump.off()
                self.shared_data['pump_state'] = False
                self.buttons['mPUMP_State'] = False  # Reset button after toggling
                print("Pump turned OFF")
            else:  # Pump is currently OFF, turn it ON
                self.pump.on()
                self.shared_data['pump_state'] = True
                self.buttons['mPUMP_State'] = False  # Reset button after toggling
                print("Pump turned ON")
        
        # Handle boiler toggle - TEST CODE
        if self.buttons['mBOILER_State']:
            if self.shared_data['heater_state']:  # Boiler is currently ON, turn it OFF
                self.boiler.off()
                self.shared_data['heater_state'] = False
                self.buttons['mBOILER_State'] = False  # Reset button after toggling
                print("Boiler turned OFF")
            else:  # Boiler is currently OFF, turn it ON
                self.boiler.on()
                self.shared_data['heater_state'] = True
                self.buttons['mBOILER_State'] = False  # Reset button after toggling
                print("Boiler turned ON")

    def handle_auto_state(self):
        """ State 1: Heat water to coffee temp """
        self.shared_data['shared_state'] = State.AUTO
        # self.target_temp = 95
        # if self.shared_data['temperature'] >= 95:  # Hardcoded coffee temp. Replaced with line below

        if self.shared_data['temperature'] >= (self.shared_data['target_temp']-self.shared_data['temp_tolerance']):  # 95°C is the coffee temp
            self.state = State.PUMP
        elif self.buttons['mCANCEL_BUTTON']:
            self.boiler.off()
            self.pump.off()
            self.shared_data['heater_state'] = False
            self.shared_data['pump_state'] = False
            self.buttons['mCANCEL_BUTTON'] = False
            self.state = State.DEFAULT
           
    def handle_heat_wait_state(self):
        """ State 2: Heat to coffee temp and maintain """
        self.shared_data['shared_state'] = State.GET_READY
        # Add a time out to turn machine off after 5 minutes
        # self.target_temp = 95 # Commented out hard coded temp
        if self.buttons['mIM_READY_BUTTON']:
            self.state = State.PUMP
            self.buttons['mIM_READY_BUTTON'] = False
        elif self.buttons['mWANT_STEAM_BUTTON']:
            self.state = State.STEAM
            self.buttons['mWANT_STEAM_BUTTON'] = False
        elif self.buttons['mCANCEL_BUTTON']:
            self.boiler.off()
            self.pump.off()
            self.shared_data['heater_state'] = False
            self.shared_data['pump_state'] = False
            self.buttons['mCANCEL_BUTTON'] = False
            self.state = State.DEFAULT

    async def handle_run_pump_state(self):
        """ State 3: Run pump for X seconds """
        self.shared_data['shared_state'] = State.PUMP
        # self.target_temp = 95
        self.pump.on()
        self.shared_data['pump_state'] = True
        # time.sleep(self.shared_data['mpump_on_time']) # Changed to be asynchronous below.
        await asyncio.sleep(self.shared_data['mpump_on_time'])
        self.pump.off()
        self.shared_data['pump_state'] = False
        self.state = State.GET_READY  # Go back to HEAT_WAIT after running pump

        # Add support for cancel button
        if self.buttons['mCANCEL_BUTTON']:
            self.boiler.off()
            self.pump.off()
            self.shared_data['heater_state'] = False
            self.shared_data['pump_state'] = False
            self.buttons['mCANCEL_BUTTON'] = False
            self.state = State.DEFAULT


    def handle_steam_state(self):
        """ State 4: Heat to steam temp """
        self.shared_data['shared_state'] = State.STEAM
        # Add time out here to send back to default if at temp for 5 mins
        # self.target_temp = 120
        self.shared_data['target_temp'] = 120
        self.shared_data['temp_tolerance'] = 5

        if self.buttons['mDEFAULT_BUTTON']:
            self.boiler.off()
            self.pump.off()
            self.shared_data['heater_state'] = False
            self.shared_data['pump_state'] = False
            self.buttons['mDEFAULT_BUTTON'] = False
            self.state = State.DEFAULT         
        elif self.buttons['mGO_TO_WAIT']:
            self.state = State.GET_READY
            self.buttons['mGO_TO_WAIT'] = False

    def requestHandler(self, request):
        """ Request handler for state transitions """
        # Update button states based on incoming requests
        if 'GET /make_coffee' in request:
            print("Make Coffee Request Recieved")
            self.update_button('mAUTOMATIC_BUTTON', True)
        elif 'GET /heat_wait' in request:
            print("Get Ready and Wait Request Recieved")
            self.update_button('mHEAT_WAIT_BUTTON', True)
        elif 'GET /cancel' in request:
            print("Cancel Request Recieved")
            self.update_button('mCANCEL_BUTTON', True)
        elif 'GET /im_ready' in request:
            print("Im Ready event recieved. Start pump.")
            self.update_button('mIM_READY_BUTTON', True)
        elif 'GET /want_steam' in request:
            print("Want Steam event recieved.")
            self.update_button('mWANT_STEAM_BUTTON', True)
        elif 'GET /another_coffee' in request:
            print("User wants another coffee. Go to wait.")
            self.update_button('mGO_TO_WAIT', True)
        elif 'GET /go_to_default' in request:
            self.update_button('mDEFAULT_BUTTON', True)
        elif 'GET /pump_test' in request:
            self.update_button('mPUMP_State', True)
        elif 'GET /boiler_test' in request:
            self.update_button('mBOILER_State', True)
        elif '/update' in request:
            try:
                # Split the request to get the query string
                # The request format is expected to be: "GET /update?param=value HTTP/1.1"
                if '?' in request:
                    _, query_string = request.split('?', 1)
                    query_string, _ = query_string.split(' ', 1)  # Remove the HTTP part
                    params = query_string.split('&')

                    for param in params:
                        key, value = param.split('=')
                        # Check if the key exists in shared_data and update the value
                        if key in self.shared_data:
                            self.shared_data[key] = int(value)
                            print(f"Updated {key} to {value}")
                    return '200 OK', 'text/plain', 'Updated successfully'
                else:
                    print("No query string found in the request.")
                    return '400 Bad Request', 'text/plain', 'Missing query parameters'
            except Exception as e:
                print(f"Error updating parameters: {e}")
                return '400 Bad Request', 'text/plain', 'Error updating parameters'