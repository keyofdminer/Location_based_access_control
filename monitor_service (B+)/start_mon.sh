#!/bin/bash

sudo service NetworkManager stop
sudo iw phy phy0 interface add mon0 type monitor
sudo ifconfig mon0 up
sudo iw dev mon0 set channel $1
#sudo ifconfig wlan0 down
