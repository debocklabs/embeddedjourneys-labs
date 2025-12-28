# README

This code goes with the corresponding [EmbeddedJourneys blog post](https://embeddedjourneys.com/blog/first-time-usb-data-stream-on-pico/) about setting up a first USB data stream. The host program visualizes a cosine wave with a period of 2 seconds which is generated on the USB device, analogous to what is shown in the gif at the end of the blog post.  

This folder contains the following 2 subfolders:

## firmware
Contains the source code for the USB device, which is intended to run on a Raspberry Pi Pico 2W (A Pico 2 should work as well though)

## Host
Contains the python code to visualize the data streamed from the USB device. 

Please note that I have been using a Python environment in visual studio community. I have been running Python 3.13. Just for this code to run, you'll need to add an environment with Name *venv* and as base interpreter you could choose the Python 3.13. In the Host folder, you'll find a requirements.txt file that should be selected in "Install packages from file" so you get the correct dependencies in that environment. Cf. green arrows in the image below.

![add-environment](add-environment.jpg)