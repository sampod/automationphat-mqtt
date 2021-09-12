# automationphat-mqtt
Reads automationphat ADC inputs and GPIO IOs and sends it to MQTT server.  
Allows controlling outputs via MQTT.  
Requires pimoroni automationphat libraries.
Enables (easy?) integration to for example Home Assistant.  

Example home assistant configuration.yaml entry:
```
# Example configuration.yaml entry
sensor:
  - platform: mqtt
    name: Automationphat voltage 1
    state_topic: "automationphat/sensor/voltage1/state"
    unit_of_measurement: V
  - platform: mqtt
    name: Automationphat voltage 2
    state_topic: "automationphat/sensor/voltage2/state"
    unit_of_measurement: V
  - platform: mqtt
    name: Automationphat voltage 3
    state_topic: "automationphat/sensor/voltage3/state"
    unit_of_measurement: V

binary_sensor:
  - platform: mqtt
    name: Automationphat input 1
    state_topic: "automationphat/26"
    payload_on: 1
    payload_off: 0
  - platform: mqtt
    name: Automationphat input 2
    state_topic: "automationphat/20"
    payload_on: 1
    payload_off: 0
  - platform: mqtt
    name: Automationphat input 3
    state_topic: "automationphat/21"
    payload_on: 1
    payload_off: 0

switch:
  - platform: "mqtt"
    name: Automationphat Output1
    state_topic: "automationphat/5"
    payload_off: "0"
    payload_on: "1"
    command_topic: "automationphat/5/control"
  - platform: "mqtt"
    name: Automationphat Output2
    state_topic: "automationphat/12"
    payload_off: "0"
    payload_on: "1"
    command_topic: "automationphat/12/control"
  - platform: "mqtt"
    name: Automationphat Output3
    state_topic: "automationphat/6"
    payload_off: "0"
    payload_on: "1"
    command_topic: "automationphat/6/control"
  - platform: "mqtt"
    name: Automationphat Relay
    state_topic: "automationphat/16"
    payload_off: "0"
    payload_on: "1"
    command_topic: "automationphat/16/control"
```
