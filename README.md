# Jenkins failed build warning light #

This Python script polls a Jenkins View and starts an alarm on the C.H.I.P. (http://getchip.com) when any build is Failed or Unstable. An Extreme Feedback device for Jenkins!

Works well with the Jenkins build monitor: https://wiki.jenkins-ci.org/display/JENKINS/Build+Monitor+Plugin

Based on: http://www.instructables.com/id/Pocket-Chip-How-to-Make-Blinking-a-Led/?ALLSTEPS

## Demo: ##
[![Demo of the extreme feedback Jenkins flashing light](http://img.youtube.com/vi/jDgX5bndHAk/0.jpg)](http://www.youtube.com/watch?v=jDgX5bndHAk "Demo of the extreme feedback Jenkins flashing light")

## Wiring diagram: ##
I hooked up a [small relay](https://www.aliexpress.com/item/1-Road-Channel-Relay-Module-Without-Light-Coupling-for-Arduino-PIC-ARM-DSP-AVR-Raspberry-Pi/32348359671.html) toggling a flashing, rotating warning light. Hook it up to Vcc, Ground, XIO-P4.

## How to use it: ##
```shell
sudo ntpdate pool.ntp.org
sudo apt-get update
sudo apt-get install git build-essential python-dev python-pip -y

git clone git://github.com/xtacocorex/CHIP_IO.git
cd CHIP_IO
sudo python setup.py install
cd ..
sudo rm -rf CHIP_IO

git clone git://github.com/joepweijers/jenkins-failed-build-warning-light.git
cd jenkins-failed-build-warning-light
pip install -r requirements.txt
sudo python jenkins-failed-build-warning-light.py http://jenkins.example.com/view/YourView
```
