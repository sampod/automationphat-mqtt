#!/usr/bin/env python3

import configparser
import time
import paho.mqtt.client as mqtt

import automationhat
time.sleep(0.1) # short pause after ads1015 class creation recommended

# initialize config
config = configparser.ConfigParser()
config.read("automationphat-mqtt.conf")
# read variables from config
sleeptime = config.getint('general', 'interval')
mqttaddress = config.get("mqtt", "address")
mqtttopic1 = config.get("mqtt", "automationphattopic1")
mqtttopic2 = config.get("mqtt", "automationphattopic2")
mqtttopic3 = config.get("mqtt", "automationphattopic3")

# Global variables
global value1, value2

# MQTT-sending
# Calculate median for measured power values and send median and latest values
# and counter value to MQTT broker
def mqttsend():
    global value1, value2
    client =mqtt.Client("automationphat")
    try:
      client.connect(mqttaddress)
      client.publish(mqtttopic1,value1)
      print("mqtt value1 sent")
      client.publish(mqtttopic2,value2)
      print("mqtt value2 sent")
      client.publish(mqtttopic3,value3)
      print("mqtt value3 sent")
      client.loop(2)
      client.disconnect()
      client.loop(2)
    except:
      print("MQTT connetion error")


print("""
Press CTRL+C to exit.
""")

while True:
    value1 = automationhat.analog.one.read()
    print(value1)
    value2 = automationhat.analog.two.read()
    print(value2)
    value3 = automationhat.analog.three.read()
    print(value3)
    mqttsend()
    time.sleep(sleeptime)

