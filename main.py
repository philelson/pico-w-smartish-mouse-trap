import config
import gc
import machine
import network
import secrets
import time
from time import sleep
from picozero import pico_led
from umqttsimple import MQTTClient
from machine import Pin
from trap import Trap

# Cache for template, to save reloading
rawPayloadContents = None

# Array of traps setup via config to allow flexible allocation of 1..26 potentially
traps = [];

# MQTT client, once intialised
mqttClient = None;

# Version of this program
version = '0.0.1'

# 
# Functions
#
def connect(ssid, password):
    pico_led.on()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    connectionAttemptLimit = config.wifi_connection_attempts
    connectionAttempts = 0
    while wlan.isconnected() == False:
        pico_led.off()
        print(f'Waiting for connection on {ssid}...')
        sleep(0.5)
        pico_led.on()
        sleep(0.5)
        connectionAttempts += 1
        if connectionAttempts >= connectionAttemptLimit: return False
    ip = wlan.ifconfig()[0]
    print(f'Connected to {ssid} on {ip}')
    return ip

def mqttConnect(mqtt_client_id, mqtt_server, mqtt_port, mqtt_username, mqtt_password):
    client = MQTTClient(mqtt_client_id, mqtt_server, mqtt_port, mqtt_username, mqtt_password)
    client.connect()
    print('Connected to %s MQTT Broker'%(config.mqtt_server))
    return client

def restartMachine():
    print('Failed to connected to services. Restarting...')
    time.sleep(5)
    machine.reset()
    
def startupSummary(version: str):
    print(f'version: {version}')

    print('MQTT config')
    print(f'--> client id: {config.mqtt_client_id}')
    print(f'--> username: {config.mqtt_username}')
    print(f'--> server: {config.mqtt_server}')
    print(f'--> port: {config.mqtt_port}')
    print(f'--> topic: {config.topic}')
    
def ledFlash():
    pico_led.on()
    sleep(0.1)
    pico_led.off()

def getPayload(pin, initial = False) -> str:
    global version
    global rawPayloadContents
    global traps
    topic = config.topic
    
    if rawPayloadContents is None:
         file = open(config.payload_template)
         rawPayloadContents = file.read()
         file.close()
         
    # Dynamically build JSON payload for trap status
    payload = '';
    for trap in traps:
        if traps[0] is trap: payload = payload+" [\n"
        
        trapStatus = "open"
        if trap.pinInstance.value() is 1: trapStatus = "closed"

        payload = payload+"\t\t"+'{"id":'+str(trap.pinId)+', "value":"'+trapStatus+'"}'
        
        if traps[-1] is not trap: payload = payload+",\n"
        else: payload = payload+"\n\t]\n"
        
    if initial is True:
        topic = topic + '.initial'        
        
    return rawPayloadContents.format(
        version = version,
        trap_data = payload,
        node_name = topic,
        client = config.mqtt_client_id,
        resources = gc.mem_free()
    )
  
def trapTriggered(pin, initial = False):
    global traps
    global mqttClient
    topic = config.topic

    payloadWrapper = '{}';
    for trap in traps:
        if trap.pinInstance is pin:
            print(f"Trap {trap.pinId} triggered")
            
    payload = getPayload(pin, initial)
    print(payload)
    if initial is True:
        topic = topic + '.initial'
        
    mqttClient.publish(topic, payload)
    ledFlash()
    

def initTriggers():
    global traps
    
    for trapPin in config.traps:
        trapPinInstance = Pin(trapPin, Pin.IN, pull=Pin.PULL_UP)
        trapPinInstance.irq(trigger=Pin.IRQ_RISING, handler=trapTriggered)
        
        trapInstance = Trap()
        trapInstance.pinId = trapPin
        trapInstance.pinInstance = trapPinInstance

        traps.append(trapInstance)
        print(f'Added trap on pin {trapInstance.pinId}')

    print('Triggers initialised')

#
# Main Program
# 
try:
    pico_led.on()
    version = '0.0.1'
    startupSummary(version)
    ip = connect(secrets.ssid, secrets.password)
    if False == ip:
        ip = connect(secrets.ssid2, secrets.password2)
    elif False == ip:
        print(f'Unable to connect to {secrets.ssid} or {secrets.ssid2}')
    print(f'--> IP address: {ip}')
    mqttClient = mqttConnect(config.mqtt_client_id, config.mqtt_server, config.mqtt_port, config.mqtt_username, config.mqtt_password)

    initTriggers()
    trapTriggered(traps[-1].pinInstance, True)
    pico_led.off()
    
except KeyboardInterrupt as e:
    print(repr(e))
    restartMachine()
except OSError as e:
    print(repr(e))
    restartMachine()