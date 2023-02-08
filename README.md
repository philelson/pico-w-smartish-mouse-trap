# Summary

PICO W - Simple program for humane traps.

Designed around reed switches which are open by default with SW controlled
Pull Up resistors.
When the trap is armed (door is open) the magnet closes the switch (pulled low). 
When the trap is tripped and the switch opens (goes high) the rising edge triggers
an IRQ which dispatches an MQTT with the state of all the traps attached to this
PICO.

You can then use Node Red, Home Assistant etc to notify you of trap state changes

## Credit

Couple of awesome libraries that make this a piece of cake to code!

1. MQTT Library: https://github.com/RuiSantosdotme/ESP-MicroPython/blob/master/code/MQTT/umqttsimple.py
2. PICO Zero library: https://picozero.readthedocs.io/en/latest/gettingstarted.html


# Settings

Rename secrets.py.sample to secrets.py and enter wifi credentials
Rename config.py.sample to config.py and update MQTT settings etc

Traps, are simple GPIO pins configured to trigger an IRQ. Wire your pins up and simply add the pins GPIO numbers to the `traps` array in config.py. For instance the below is for 4 traps. 

```
traps = (16, 17, 18, 19)
```

# Uploading

1. config.py
2. picozero.py
3. secrets.py
4. umqttsimple.py
5. template.json
6. main.py

# Debugging

Data is logged to the terminal to provide debugging
Assuming mosquite MQTT the below will allow you to monitor incoming data changes (one for each temp and humidity topic)

```bash
mosquitto_sub -h {host} -t "{topic}" -u {username} -P {password}
```

# MQTT Payload Example

```json
{
        "name": "home.house.original.loft.traps.mouseTraps.set[0].initial",
        "client": "OutsideGarage",
        "version": "0.0.1",
        "resources": "60672",
        "traps":  [
                {"id":16, "value":"closed"},
                {"id":17, "value":"closed"},
                {"id":18, "value":"closed"},
                {"id":19, "value":"closed"}
        ]

}
```