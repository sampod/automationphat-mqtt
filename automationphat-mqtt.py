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

try:
    if automationhat.is_automation_hat():
        automationhat.light.power.write(1)
        automationhat.enable_auto_lights(True)
        has_ADC=1
except:
    print ("No ADC found")
    has_ADC=0

# initialize config
config = configparser.ConfigParser()
config.read("automationphat-mqtt.conf")
# read variables from config
sleeptime = config.getint('general', 'interval')
mqttaddress = config.get("mqtt", "address")
mqtttopic = config.get("mqtt", "automationphattopic")

# Global variables
global value1, value2

# MQTT-sending
# Send ADC input values to MQTT broker
def mqttsend(value1,value2,value3):
    voltage1topic=mqtttopic + "voltage1"
    voltage2topic=mqtttopic + "voltage2"
    voltage3topic=mqtttopic + "voltage3"
    client.publish(voltage1topic,value1)
    print("mqtt value1 sent:", value1)
    client.publish(voltage2topic,value2)
    print("mqtt value2 sent:", value2)
    client.publish(voltage3topic,value3)
    print("mqtt value3 sent:", value3)

# Append message instantly to messages variable upon receiving
def on_message(client, userdata, message):
   msg=str(message.payload.decode("utf-8"))
   topic=message.topic
   messages.append([topic,msg])

# Subscribe to interesting MQTT topics on connect
def on_connect(client, userdata, flags, rc):

    if rc==0:
        print("connected")
        client.connected_flag=True
        client.subscribe(relay_ctltopic2)
        client.subscribe(relay2_ctltopic2)
        client.subscribe(relay3_ctltopic2)
        client.subscribe(out1_ctltopic2)
        client.subscribe(out2_ctltopic2)
        client.subscribe(out3_ctltopic2)
        # enable lights if using automationhat
        if has_ADC == 1:
            automationhat.light.comms.on()
        # Schedule ADC data sending if ADC has been detected
        if has_ADC == 1:
            schedule.every(sleeptime).seconds.do(adcsend)
        # send input statuses on connect
        pulsecallback(26)
        pulsecallback(20)
        pulsecallback(21)

    else:
        print("connection error")
        client.bad_connection_flag=True
        client.connected_flag=False
        if automationhat.is_automation_hat():
            automationhat.light.comms.off()
        # cancel all tasks (currently only adcsend)
        schedule.clear()

def on_disconnect(client, userdata, rc):
    print("disconnected")
    client.connected_flag=False
    client.disconnect_flag=True
    # cancel all tasks (currently only adcsend)
    schedule.clear()

# Send digital input pulses instantly to MQTT broker
def pulsecallback(channel):
    print ("State change detected on input 1, BCM:", channel)
    print (channel)
    if channel == 26:
        pubtopic = mqtttopic + "input1"
        client.publish(pubtopic,GPIO.input(channel))
    elif channel == 20:
        pubtopic = mqtttopic + "input2"
        client.publish(pubtopic,GPIO.input(channel))
    elif channel == 21:
        pubtopic = mqtttopic + "input3"
        client.publish(pubtopic,GPIO.input(channel))
    else:
        print("iunknown channel")

# Send ADC data to MQTT broker
def adcsend():
    value1 = automationhat.analog.one.read()
    value2 = automationhat.analog.two.read()
    value3 = automationhat.analog.three.read()
    mqttsend(value1,value2,value3)


# GPIO initialisations
GPIO.setmode(GPIO.BCM)
# not needed when using automationhat library
# GPIO.setup(5,GPIO.OUT)
# GPIO.setup(6,GPIO.OUT)
# GPIO.setup(12,GPIO.OUT)
# GPIO.setup(16,GPIO.OUT)
GPIO.setup(26,GPIO.IN)
GPIO.setup(20,GPIO.IN)
GPIO.setup(21,GPIO.IN)
# Setup interruption for above GPIO inputs
GPIO.add_event_detect(26, GPIO.BOTH, callback=pulsecallback)
GPIO.add_event_detect(20, GPIO.BOTH, callback=pulsecallback)
GPIO.add_event_detect(21, GPIO.BOTH, callback=pulsecallback)
##MQTT initialisations
messages=[]
relay_ctltopic2=mqtttopic + "relay1/control/#"
relay2_ctltopic2=mqtttopic + "relay2/control/#"
relay3_ctltopic2=mqtttopic + "relay3/control/#"
out1_ctltopic2=mqtttopic + "output1/control/#"
out2_ctltopic2=mqtttopic + "output2/control/#"
out3_ctltopic2=mqtttopic + "output3/control/#"
client= mqtt.Client("GPIO-client-001")  #create client object client1.on_publish = on_publis
client.on_message=on_message
client.on_connect=on_connect
client.on_disconnect=on_disconnect
client.connected_flag=False
client.connect(mqttaddress)#connect


print("""
Press CTRL+C to exit.
""")

# start MQTT loop
client.loop_start()

# define sub topics
relay1topic=mqtttopic + "relay1"
relay2topic=mqtttopic + "relay2"
relay3topic=mqtttopic + "relay3"
out1topic=mqtttopic + "output1"
out2topic=mqtttopic + "output2"
out3topic=mqtttopic + "output3"

# read initial output states
client.publish(relay1topic, automationhat.relay.one.read())
client.publish(relay2topic, automationhat.relay.two.read())
client.publish(relay3topic, automationhat.relay.three.read())
client.publish(out1topic, automationhat.output.one.read())
client.publish(out2topic, automationhat.output.two.read())
client.publish(out3topic, automationhat.output.three.read())
mainsleeptime = 1

while True:
    try:
        time.sleep(mainsleeptime)
# process messages if received
        if len(messages)>0:
            m=messages.pop(0)
            msgpath = PurePath(m[0])
            relpath = msgpath.relative_to(mqtttopic)
            print("received ",m)
            if m[1] == "0" or m[1]=="1":
                print("Controlling :",relpath.parts[0]," to:",int(m[1]))
                if relpath.parts[0] == "relay1":
                    automationhat.relay.one.write(int(m[1]))
                    client.publish(relay1topic, automationhat.relay.one.read())
                elif relpath.parts[0] == "relay2":
                    if has_ADC == 1:
                        automationhat.relay.two.write(int(m[1]))
                        client.publish(relay2topic, automationhat.relay.two.read())
                elif relpath.parts[0] == "relay3":
                    if has_ADC == 1:
                        automationhat.relay.three.write(int(m[1]))
                        client.publish(relay3topic, automationhat.relay.three.read())
                elif relpath.parts[0] == "output1":
                    automationhat.output.one.write(int(m[1]))
                    client.publish(out1topic, automationhat.output.one.read())
                elif relpath.parts[0] == "output2":
                    automationhat.output.two.write(int(m[1]))
                    client.publish(out2topic, automationhat.output.two.read())
                elif relpath.parts[0] == "output3":
                    automationhat.output.three.write(int(m[1]))
                    client.publish(out3topic, automationhat.output.three.read())
                else:
                    Print ("Undefined control")
                mainsleeptime = 0.1
            else:
                print("Invalid control string - try 0 or 1")
        else: mainsleeptime = 1
# keep scheduled processes running
        schedule.run_pending()
    except KeyboardInterrupt:
        GPIO.cleanup()       # clean up GPIO on CTRL+C exit
        exit()
