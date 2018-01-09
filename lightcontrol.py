from machine import Pin
import network
import ujson
import time
import os
from sys import exit
import gc
from umqtt.simple import MQTTClient
import ustruct
import ubinascii
from machine import unique_id

gc.enable()
gc.collect()

client_id = ubinascii.hexlify(machine.unique_id()).decode()
alarm_led = Pin(10, mode=Pin.OUT)
clockPin  = Pin(5, Pin.OUT)
latch_in_Pin  = Pin(4, Pin.OUT)
data_in_Pin  = Pin(16, Pin.IN)
latch_out_Pin  = Pin(0, Pin.OUT)
latch_out_Pin.on()
data_out_Pin  = Pin(2, Pin.OUT)
outputs_state = []
inputs_state = []

def check_file(file):
    try:
        os.stat(file)
        return True
    except:
        return False

def read_file(file):
    f = open(file,'r')
    data=f.read()
    f.close()
    return data

def do_connect(sta_if,conf):
    status = sta_if.status()
    if not sta_if.isconnected():
        print('connecting to network...')
        print(sta_if.active())
        sta_if.connect(conf['ssid'], conf['secret'])
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

def sub_cb(topic, msg):
    global current_outputs_state
    global outputs_state
    switch = topic.decode("utf-8").rsplit('/')[0]
    value = int(msg.decode("utf-8"))
    for key,sw in config['switches'].items():
      if sw == switch:
        outputs_state[int(key)] = value
    set_pin(outputs_state,config['switches'])
    current_outputs_state = [x for x in outputs_state]

def read_states(circ_count):
    s = []
    latch_in_Pin.off()
    time.sleep_ms(20)
    latch_in_Pin.on()
    for i in range(0,8*circ_count):
#        print(data_in_Pin.value())
        s.append(data_in_Pin.value())
        clockPin.on()
        time.sleep_ms(1)
        clockPin.off()
    return s

def set_pin(address,switches):
    global mqtt_client
    global outputs_state
    latch_out_Pin.off()
    data_out_Pin.off()
    clockPin.off()
    for x in range(len(address),0, -1):
        clockPin.off()
        data_out_Pin.value(address[x-1])
        clockPin.on()
        data_out_Pin.off()
        clockPin.off()
    latch_out_Pin.on()
    if mqtt_client:
        for x in range(len(address),0, -1):
            topic = switches[str(x-1)]+"/feeds/lights/state"
            try:
                mqtt_client.publish(topic=topic, msg=str(address[x-1]))
            except:
                print('Ops')
    outputs_state = [x for x in address]

def mqtt_conect(mqtt_conf,alarm_led,switches):
    print('Connecting to Mqtt server')
    mqttclient = MQTTClient(client_id,server=mqtt_conf['server'],port=mqtt_conf['port'],user=mqtt_conf['user'],password=mqtt_conf['password'])
    mqttclient.set_callback(sub_cb)
    try:
        mqttclient.connect()
        time.sleep_ms(10)
        alarm_led.off()
        if mqtt_conf['topics']:
            for switch in switches:
              topic = switch + '/feeds/lights/command'
              print(topic)
              mqttclient.subscribe(topic=topic)
        print("Mqqt connected")
        return mqttclient, False
    except:
        alarm_led.on()
        print("Mqqt isn't connected, retry in 60 seconds ")
        return False, time.time()

def negation(out,pos):
    if out[pos] == 1:
        out[pos] = 0
    else:
        out[pos] = 1
    return out

if check_file('config.json'):
    config=ujson.loads(read_file('config.json'))
else:
    print("Configuration file doesn't exists")
    exit()

if config['wifi']:
    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    sta_if.active(True)
    do_connect(sta_if,config['wifi'])

if config['inputs']:
    inputs = config['inputs']
else:
    inputs = 1
inputs_state = [0] * 8 * inputs

if config['outputs']:
    outputs = config['outputs']
else:
    outputs = 1
outputs_state = [0] * 8 * outputs
current_outputs_state = [0] * 8 * outputs


if config['mqtt']:
        mqtt_client, last_try = mqtt_conect(config['mqtt'],alarm_led,config['switches'].values())

while True:
#  try:
    if mqtt_client:
        print('Check for messages')
        try:
            mqtt_client.check_msg()
        except:
            mqtt_client = False
            alarm_led.on()
    elif time.time() >= (last_try+60):
        mqtt_client, last_try = mqtt_conect(config['mqtt'],alarm_led,config['switches'].values())
    current_inputs_state = read_states(inputs)
    for i in range(len(current_inputs_state),0,-1):
        if current_inputs_state[i-1] != inputs_state[i-1] and current_inputs_state[i-1] == 1:
            for x in config['buttons'][str(i-1)]['switches']:
                current_outputs_state = negation([x for x in outputs_state],x)
    inputs_state = current_inputs_state
    if outputs_state == current_outputs_state:
      print('No changes')
      pass
    else:
      print('Changes')
      set_pin(current_outputs_state,config['switches'])
    time.sleep_ms(1000)
#  except:
#    print('Ops')
