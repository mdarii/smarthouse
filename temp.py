from machine import Pin
from machine
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
import ds18x20
import onewire


gc.enable()
gc.collect()

client_id = ubinascii.hexlify(unique_id()).decode()

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

def mqtt_conect(mqtt_conf):
    print('Connecting to Mqtt server')
    mqttclient = MQTTClient(client_id,server=mqtt_conf['server'],port=mqtt_conf['port'],user=mqtt_conf['user'],password=mqtt_conf['password'])
    try:
        mqttclient.connect()
        time.sleep_ms(10)
        print("Mqqt connected")
        return mqttclient, False
    except:
        print("Mqqt isn't connected, retry in 60 seconds ")
        return False, time.time()

def get_temp:
  ds = ds18x20.DS18X20(ow)
  roms = ds.scan()
  ds.convert_temp()
  time.sleep_ms(750)
  for rom in roms:
    print(ds.read_temp(rom))

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
        mqtt_client, last_try = mqtt_conect(config['mqtt'])


try:

  machine.deepsleep(300000)
except:
  print("something wrong")
  machine.deepsleep(300000)