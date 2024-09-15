import uasyncio as asyncio # type: ignore
import usocket as socket # type: ignore
import json
from machineManager import State

class AsyncServer:
    def __init__(self, request_handler, shared_data, getstate):
        """
        Initialize the server with a request handler and shared data.
        """
        self.request_handler = request_handler  # The function to handle HTTP requests
        self.shared_data = shared_data          # Shared data between server and machine
        self.Astate = getstate

    async def start_server(self):
        """
        Start the HTTP server and listen for incoming connections.
        """
        print('Starting server...')
        # Use uasyncio's start_server to handle connections asynchronously
        await asyncio.start_server(self.handle_client, '0.0.0.0', 80)
        print('Server is running...')

        while True:
            await asyncio.sleep(3600)  # Keep the event loop running indefinitely

    async def handle_client(self, reader, writer):
        """
        Handle individual client connections, process requests or SSE.
        """
        try:
            request = await reader.read(1024)
            request = request.decode()
            # print(f"Request: {request}")

            if "/events" in request:
                await self.handle_sse(writer)
            else:
                print("HTTP request received")
                # Handle the request using the provided request handler
                response = self.request_handler(request)
                response = self.web_page_server()
                print("Declared response")

                await writer.awrite('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n' + response)
                await writer.drain()  # Ensure all data is sent to the client
                print("Sent HTTP Response")

        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            await writer.aclose()
            print("Connection closed")

    async def handle_sse(self, writer):
        """
        Handle Server-Sent Events (SSE) for clients that request updates.
        """
        print("Handling SSE")
        try:
            # Send SSE headers
            await writer.awrite('HTTP/1.1 200 OK\r\n')
            await writer.awrite('Content-Type: text/event-stream\r\n')
            await writer.awrite('Cache-Control: no-cache\r\n')
            await writer.awrite('Connection: keep-alive\r\n\r\n')
            # print("Sent SSE Headers")

            while True:
                # Send updates to the client from shared data
                data = self.shared_data.copy()
                # print("Sending SSE Update")
                await writer.awrite(f"data: {json.dumps(data)}\n\n")
                print("Sent SSE Stream")
                # print("Sent SSE Update")
                await asyncio.sleep(5)  # Adjust the frequency of updates as needed

        except (OSError, KeyboardInterrupt) as e:
            print(f"SSE connection closed or interrupted: {e}")
        finally:
            await writer.aclose()
            print("SSE connection fully closed.")

    def web_page_server(self):
        """Generate the HTML for the current state including status indicators."""
        print(f"Web page server state is {self.Astate()}")

        buttons_html = self.render_buttons_server()
        # Boiler and pump status indicators
        boiler_status = "ON" if self.shared_data['heater_state'] else "OFF"
        pump_status = "ON" if self.shared_data['pump_state'] else "OFF"
        current_temp = self.shared_data['temperature']

        status_html = f"""
            <div style="margin: 20px; font-size: 18px;">
                <p>Boiler Status: <strong id="boiler_status" style="color: {'green' if boiler_status == 'ON' else 'red'};">{boiler_status}</strong></p>
                <p>Pump Status: <strong id="pump_status" style="color: {'green' if pump_status == 'ON' else 'red'};">{pump_status}</strong></p>
                <p>Current Temperature: <strong id="temperature">{current_temp}°C</strong></p>
            </div>
        """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Coffee Machine Control</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; background-color: #f4f4f4; }}
                .button {{ display: inline-block; padding: 15px 25px; font-size: 20px; cursor: pointer; text-align: center; text-decoration: none; outline: none; color: #fff; background-color: #4CAF50; border: none; border-radius: 15px; margin: 10px; }}
                .button.off {{ background-color: #f44336; }}
                .status {{ margin: 20px; font-size: 18px; }}
            </style>
        </head>
        <body>
            <h1>Coffee Machine Control</h1>
            {buttons_html}
            {status_html}

            <!-- SSE JavaScript for live updates -->
            <script>
                // Ensure EventSource is only initialized once
                let eventSource = null;

                if (!eventSource) {{
                    eventSource = new EventSource('/events');
                    console.log("SSE connection opened");

                    eventSource.onmessage = function(event) {{
                        const data = JSON.parse(event.data);
                        console.log("Received JSON update: ", data);

                        // Update the UI with the new data
                        document.getElementById('boiler_status').textContent = data.heater_state ? 'ON' : 'OFF';
                        document.getElementById('boiler_status').style.color = data.heater_state ? 'green' : 'red';
                        document.getElementById('pump_status').textContent = data.pump_state ? 'ON' : 'OFF';
                        document.getElementById('pump_status').style.color = data.pump_state ? 'green' : 'red';
                        document.getElementById('temperature').textContent = data.temperature + "°C";
                    }};

                    eventSource.onerror = function(error) {{
                        console.error("Error with SSE connection:", error);
                    }};
                }}

                // Button actions
                function makeCoffee() {{ sendRequest('/make_coffee'); }}
                function heatWait() {{ sendRequest('/heat_wait'); }}
                function ready() {{ sendRequest('/im_ready'); }}
                function wantSteam() {{ sendRequest('/want_steam'); }}
                function pumpTest() {{ sendRequest('/pump_test'); }}
                function boilerTest() {{ sendRequest('/boiler_test'); }}
                function cancel() {{ sendRequest('/cancel'); }}
                function anotherCoffee() {{ sendRequest('/another_coffee'); }}
                function goToWait() {{ sendRequest('/go_to_wait'); }}

                 // Generic function to handle HTTP requests
                function sendRequest(endpoint) {{
                    fetch(endpoint)
                    .then(response => {{
                        console.log(`Endpoint request sent.`);
                    }}).catch(error => {{
                        console.error(`Error sending endpoint request:`, error);
                    }});
                }}
            </script>
        </body>
        </html>
        """
        return html

    def render_buttons_server(self):
        """Render buttons and state indicators based on the current state."""
        buttons_html = ""
        current_state = self.Astate()
        # Render buttons based on the current state
        if current_state == State.DEFAULT:
            buttons_html += '<a class="button" href="/make_coffee">Make Me a Coffee</a>'
            buttons_html += '<a class="button" href="/heat_wait">Heat & Wait</a>'

            buttons_html += '<a class="button" href="/pump_test">Pump ON/OFF</a>'
            buttons_html += '<a class="button" href="/boiler_test">Boiler ON/OFF</a>'
        elif current_state == State.AUTO:
            buttons_html += '<p>Heating water to coffee temperature...</p>'
            buttons_html += '<a class="button" href="/cancel">Cancel</a>'
        elif current_state == State.GET_READY:
            buttons_html += '<a class="button" href="/im_ready">I\'m Ready</a>'
            buttons_html += '<a class="button" href="/want_steam">I Want Steam</a>'
            buttons_html += '<a class="button" href="/cancel">Done</a>'
        elif current_state == State.PUMP:
            buttons_html += '<p>Running pump for coffee... will take 5 seconds</p>'
        elif current_state == State.STEAM:
            buttons_html += '<a class="button" href="/another_coffee">Another Coffee</a>'
            buttons_html += '<a class="button" href="/go_to_wait">Done</a>'

        # Combine status indicators and buttons
        return buttons_html