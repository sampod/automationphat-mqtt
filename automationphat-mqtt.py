#!/usr/bin/env python3

import schedule
import sys
import configparser
import time
import signal
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import numbers
from pathlib import PurePath

import automationhat
time.sleep(0.1) # short pause after ads1015 class creation recommended

if automationhat.is_automation_hat():
    automationhat.light.power.write(1)
    automationhat.enable_auto_lights(True)

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
        client.subscribe(relay_ctltopic2)
        client.subscribe(relay2_ctltopic1)
        client.subscribe(relay2_ctltopic2)
        client.subscribe(relay3_ctltopic1)
        client.subscribe(relay3_ctltopic2)
        client.subscribe(out1_ctltopic)
        client.subscribe(out2_ctltopic)
        client.subscribe(out3_ctltopic)
        client.subscribe(out1_ctltopic2)
        client.subscribe(out2_ctltopic2)
        client.subscribe(out3_ctltopic2)
        if automationhat.is_automation_hat():
            automationhat.light.comms.on()

    else:
        client.bad_connection_flag=True
        client.connected_flag=False
        if automationhat.is_automation_hat():
            automationhat.light.comms.off()

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
relay_ctltopic=mqtttopic + "13/control/#"
relay_ctltopic2=mqtttopic + "relay1/control/#"
relay2_ctltopic1=mqtttopic + "19/control/#"
relay2_ctltopic2=mqtttopic + "relay2/control/#"
relay3_ctltopic1=mqtttopic + "16/control/#"
relay3_ctltopic2=mqtttopic + "relay3/control/#"
out1_ctltopic=mqtttopic + "5/control/#"
out2_ctltopic=mqtttopic + "12/control/#"
out3_ctltopic=mqtttopic + "6/control/#"
out1_ctltopic2=mqtttopic + "output1/control/#"
out2_ctltopic2=mqtttopic + "output2/control/#"
out3_ctltopic2=mqtttopic + "output3/control/#"
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
        relay1topic=mqtttopic + "relay1"
        relay2topic=mqtttopic + "relay2"
        relay3topic=mqtttopic + "relay3"
        out1topic=mqtttopic + "output1"
        out2topic=mqtttopic + "output2"
        out3topic=mqtttopic + "output3"
        client.publish(relay1topic, automationhat.relay.one.read())
        client.publish(relay2topic, automationhat.relay.two.read())
        client.publish(relay3topic, automationhat.relay.three.read())
        client.publish(out1topic, automationhat.output.one.read())
        client.publish(out2topic, automationhat.output.two.read())
        client.publish(out3topic, automationhat.output.three.read())
        time.sleep(1)
# process messages if received
        if len(messages)>0:
            m=messages.pop(0)
            msgpath = PurePath(m[0])
            relpath = msgpath.relative_to(mqtttopic)
            print("received ",m)
            if m[1] == "0" or m[1]=="1":
                print("Controlling GPIO:",relpath.parts[0]," to:",int(m[1]))
                if relpath.parts[0] == "relay1":
                    automationhat.relay.one.write(int(m[1]))
                elif relpath.parts[0] == "relay2":
                    if automationhat.is_automation_hat():
                        automationhat.relay.two.write(int(m[1]))
                elif relpath.parts[0] == "relay3":
                    if automationhat.is_automation_hat():
                        automationhat.relay.three.write(int(m[1]))
                elif relpath.parts[0] == "output1":
                    automationhat.output.one.write(int(m[1]))
                elif relpath.parts[0] == "output2":
                    automationhat.output.two.write(int(m[1]))
                elif relpath.parts[0] == "output3":
                    automationhat.output.three.write(int(m[1]))
                else:
                    GPIO.output(int(relpath.parts[0]),int(m[1])) #set
            else:
                print("Invalid control string - try 0 or 1")
# keep scheduled processes running
        schedule.run_pending()
    except KeyboardInterrupt:
        GPIO.cleanup()       # clean up GPIO on CTRL+C exit
