#!/bin/sh
sudo mkdir /media/eds1
sudo chown -R pi:pi /media/eds1
sudo mount /dev/sda1 /media/eds1 -o uid=pi,gid=pi
sudo umount /media/eds1
