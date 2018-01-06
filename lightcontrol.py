from machine import Pin
import network
import ujson
import time
import os
from sys import exit
import gc
from umqtt.robust import MQTTClient

gc.enable()
gc.collect()

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
    mqttclient = MQTTClient(config['mqtt']['client_id'], server=config['mqtt']['server'], port=config['mqtt']['port'], user=config['mqtt']['user'], password=config['mqtt']['password'])
    mqttclient.set_callback(sub_cb)
    mqttclient.DEBUG = True
    mqttclient.connect()
    for topic in config['mqtt']['topics']:
        mqttclient.subscribe(topic=topic)

print('Check for messages')
mqttclient.check_msg()
