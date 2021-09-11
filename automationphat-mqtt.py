#!/usr/bin/env python3

import schedule
import sys
import configparser
import time
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from pathlib import PurePath

import automationhat
time.sleep(0.1) # short pause after ads1015 class creation recommended

# initialize config
config = configparser.ConfigParser()
config.read("automationphat-mqtt.conf")
# read variables from config
sleeptime = config.getint('general', 'interval')
mqttaddress = config.get("mqtt", "address")
mqtttopic = config.get("mqtt", "automationphattopic")
mqtttopic1 = config.get("mqtt", "automationphattopic1")
mqtttopic2 = config.get("mqtt", "automationphattopic2")
mqtttopic3 = config.get("mqtt", "automationphattopic3")

# Global variables
global value1, value2

# MQTT-sending
# Send ADC input values to MQTT broker
def mqttsend(value1,value2,value3):
    client.publish(mqtttopic1,value1)
    print("mqtt value1 sent:", value1)
    client.publish(mqtttopic2,value2)
    print("mqtt value2 sent:", value2)
    client.publish(mqtttopic3,value3)
    print("mqtt value3 sent:", value3)

# Append message instantly to messages variable upon receiving
def on_message(client, userdata, message):
   msg=str(message.payload.decode("utf-8"))
   topic=message.topic
   messages.append([topic,msg])

# Subscribe to interesting MQTT topics on connect
def on_connect(client, userdata, flags, rc):

    if rc==0:
        client.connected_flag=True
        client.subscribe(relay_ctltopic)
        client.subscribe(out1_ctltopic)
        client.subscribe(out2_ctltopic)
        client.subscribe(out3_ctltopic)
    else:
        client.bad_connection_flag=True
        client.connected_flag=False

# Send digital input pulses instantly to MQTT broker
def pulsecallback(channel):
    print ("State change detected on input 1, BCM:", channel)
    pubtopic = mqtttopic + str(channel)
    client.publish(pubtopic,GPIO.input(channel))

# Send ADC data to MQTT broker
def adcsend():
    value1 = automationhat.analog.one.read()
    value2 = automationhat.analog.two.read()
    value3 = automationhat.analog.three.read()
    mqttsend(value1,value2,value3)

# Schedule ADC data sending
schedule.every(sleeptime).minutes.do(adcsend)

# GPIO initialisations
GPIO.setmode(GPIO.BCM)
GPIO.setup(5,GPIO.OUT)
GPIO.setup(6,GPIO.OUT)
GPIO.setup(12,GPIO.OUT)
GPIO.setup(16,GPIO.OUT)
GPIO.setup(26,GPIO.IN)
GPIO.setup(20,GPIO.IN)
GPIO.setup(21,GPIO.IN)
# Setup interruption for above GPIO inputs
GPIO.add_event_detect(26, GPIO.BOTH, callback=pulsecallback)
GPIO.add_event_detect(20, GPIO.BOTH, callback=pulsecallback)
GPIO.add_event_detect(21, GPIO.BOTH, callback=pulsecallback)
##MQTT initialisations
messages=[]
relay_ctltopic=mqtttopic + "16/control/#"
out1_ctltopic=mqtttopic + "5/control/#"
out2_ctltopic=mqtttopic + "12/control/#"
out3_ctltopic=mqtttopic + "6/control/#"
client= mqtt.Client("GPIO-client-001")  #create client object client1.on_publish = on_publis
client.on_message=on_message
client.on_connect=on_connect
client.connected_flag=False
client.connect(mqttaddress)#connect


print("""
Press CTRL+C to exit.
""")

# start MQTT loop
client.loop_start()
while True:
    try:
        relaytopic=mqtttopic + "16"
        out1topic=mqtttopic + "5"
        out2topic=mqtttopic + "12"
        out3topic=mqtttopic + "6"
        client.publish(relaytopic,GPIO.input(16))
        client.publish(out1topic,GPIO.input(5))
        client.publish(out2topic,GPIO.input(12))
        client.publish(out3topic,GPIO.input(6))
        time.sleep(1)
# process messages if received
        if len(messages)>0:
            m=messages.pop(0)
            msgpath = PurePath(m[0])
            relpath = msgpath.relative_to(mqtttopic)
            print("received ",m)
            print("Controlling GPIO:",relpath.parts[0]," to:",int(m[1]))
            GPIO.output(int(relpath.parts[0]),int(m[1])) #set
# keep scheduled processes running
        schedule.run_pending()
    except KeyboardInterrupt:
        GPIO.cleanup()       # clean up GPIO on CTRL+C exit
