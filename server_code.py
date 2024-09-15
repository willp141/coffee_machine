    # def web_page_server(self):
    #     """Generate the HTML for the current state including status indicators."""
    #     print(f"Web page server state is {self.Astate()}")

    #     buttons_html = self.render_buttons_server()
    #     # Boiler and pump status indicators
    #     boiler_status = "ON" if self.shared_data['heater_state'] else "OFF"
    #     pump_status = "ON" if self.shared_data['pump_state'] else "OFF"
    #     current_temp = self.shared_data['temperature']

    #     status_html = f"""
    #         <div style="margin: 20px; font-size: 18px;">
    #             <p>Boiler Status: <strong id="boiler_status" style="color: {'green' if boiler_status == 'ON' else 'red'};">{boiler_status}</strong></p>
    #             <p>Pump Status: <strong id="pump_status" style="color: {'green' if pump_status == 'ON' else 'red'};">{pump_status}</strong></p>
    #             <p>Current Temperature: <strong id="temperature">{current_temp}°C</strong></p>
    #         </div>
    #     """

    #     html = f"""
    #     <!DOCTYPE html>
    #     <html>
    #     <head>
    #         <meta charset="UTF-8">
    #         <title>Coffee Machine Control</title>
    #         <style>
    #             body {{ font-family: Arial, sans-serif; text-align: center; background-color: #f4f4f4; }}
    #             .button {{ display: inline-block; padding: 15px 25px; font-size: 20px; cursor: pointer; text-align: center; text-decoration: none; outline: none; color: #fff; background-color: #4CAF50; border: none; border-radius: 15px; margin: 10px; }}
    #             .button.off {{ background-color: #f44336; }}
    #             .status {{ margin: 20px; font-size: 18px; }}
    #         </style>
    #     </head>
    #     <body>
    #         <h1>Coffee Machine Control</h1>
    #         {buttons_html}
    #         {status_html}

    #         <!-- SSE JavaScript for live updates -->
    #         <script>
    #             // Ensure EventSource is only initialized once
    #             let eventSource = null;

                # if (!eventSource) {{
                #     eventSource = new EventSource('/events');
                #     console.log("SSE connection opened");

                #     eventSource.onmessage = function(event) {{
                #         const data = JSON.parse(event.data);
                #         console.log("Received update: ", data);

                #         // Update the UI with the new data
                #         document.getElementById('boiler_status').textContent = data.heater_state ? 'ON' : 'OFF';
                #         document.getElementById('pump_status').textContent = data.pump_state ? 'ON' : 'OFF';
                #     }};

                #     eventSource.onerror = function(error) {{
                #         console.error("Error with SSE connection:", error);
                #     }};
                # }}

    #             // Function for sending button press to server without page reload
    #             function makeCoffee() {{
    #                 fetch('/make_coffee')
    #                 .then(response => {{
    #                     console.log("Make coffee request sent.");
    #                 }}).catch(error => {{
    #                     console.error("Error sending make coffee request:", error);
    #                 }});
    #             }}
    #         </script>
    #     </body>
    #     </html>
    #     """
    #     return html