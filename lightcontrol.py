from machine import Pin
import network
import ujson
import time
import os
from sys import exit
import gc
from umqtt.simple import MQTTClient

gc.enable()
gc.collect()

alarm_led = Pin(10, mode=Pin.OUT)

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
    print(topic)
    print(msg)

def mqtt_conect(mqtt_conf,alarm_led):
    print('Connecting to Mqtt server')
    mqttclient = MQTTClient(mqtt_conf['client_id'],server=mqtt_conf['server'],port=mqtt_conf['port'],user=mqtt_conf['user'],password=mqtt_conf['password'])
    mqttclient.set_callback(sub_cb)
    try:
        mqttclient.connect()
        time.sleep_ms(10)
        alarm_led.off()
        if mqtt_conf['topics']:
            for topic in mqtt_conf['topics']:
                mqttclient.subscribe(topic=topic)
        print("Mqqt connected")
        return mqttclient, False
    except:
        alarm_led.on()
        print("Mqqt isn't connected, retry in 60 seconds ")
        return False, time.time()

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

if config['mqtt']:
        mqtt_client, last_try = mqtt_conect(config['mqtt'],alarm_led)

while True:
    if mqtt_client:
        print('Check for messages')
        try:
            mqtt_client.check_msg()
        except:
            mqtt_client = False
            alarm_led.on()
    elif time.time() >= (last_try+60):
        mqtt_client, last_try = mqtt_conect(config['mqtt'],alarm_led)
    time.sleep_ms(100)
