import os
from random import sample
import matplotlib.pyplot as plt
import sys
import threading
import time
import usb.core, usb.util               # package pyusb
import usb.backend.libusb1 as libusb1   # package libusb1 needed for the backend
from collections import deque
from matplotlib.animation import FuncAnimation
from queue import Queue, Empty

# -----------------------
# USB device configuration settings
# -----------------------

# Set the PID and VID of your USB device
# Please note that you should reserve a formal VID value before productizing you USB device.
VID = 0xCAFE # VID as you have defined it in your device descriptor 
PID = 0x4000 # PID as you have defined it in your device descriptor

#TODO
EP = 0x81 # bulk IN endpoint

# -----------------------
# Plot config
# -----------------------
WINDOW_SECONDS = 10
MAX_POINTS = 5000

samples_q = Queue()

# -----------------------

def reader_thread():
    # Loop until a USB device has been found
    usb_device = None
    while not usb_device:
        usb_device = usb.core.find(idVendor=VID, idProduct=PID)
        if not usb_device:
            print("""No USB device found with VID 0x{:02X} and PID 0x{:02X} found!\n Are VID and PID correctly configured on host and device?\n Is your USB device connected?\n Did you configure the driver to WinUSB using Zadig?\n Are your VID and PID correct?\n""".format(VID, PID))
        else:
            print("USB device found: ")
            print(usb_device)
            break
        time.sleep(0)

    usb_device.set_configuration()
    cfg = usb_device.get_active_configuration()
    print("---CONFIGURATION---\n")
    print(cfg)
    intf = cfg[(0, 0)]
    print("---INTERFACE---\n")
    print(intf)
    ep_in = usb.util.find_descriptor(intf, bEndpointAddress=EP)
    print("---ENDPOINT IN---\n")
    print(ep_in)
   
    while True:
        print("Streaming for 5 seconds...")
        total = 0
        start = time.time()
        while time.time() - start < 5:
            try:
                data = usb_device.read(EP, ep_in.wMaxPacketSize, timeout=100)
                samples_q.put((time.time(), data))
               
                total += len(data)
            except:
                pass

        elapsed = time.time() - start
        print(f"Total bytes: {total}")
        print(f"Throughput: {total / elapsed:.2f} bytes/s")
        print(f"Throughput: {total * 8 / elapsed / 1e6:.3f} Mbit/s")

# -----------------------
# Main
# -----------------------

# Peform some sanity checks when starting the application
# Check if venv was correctly created, this will allow for the expected relative path
path_cwd = os.getcwd()
print("path_cwd: ", path_cwd)
path_venv = path_cwd + "\\venv"
if not os.path.isdir(path_venv):
    raise Exception("Make sure you have created a virtual environment and that it is called \"venv\".")
path_libusb1 = path_venv + "\\Lib\\site-packages\\usb1"
if not os.path.isdir(path_libusb1):
    raise Exception("Make sure you have have installed the package \"libusb1\".")
file_libusb1 = path_libusb1 + "\\libusb-1.0.dll"
if not os.path.isfile(file_libusb1):
    raise Exception("libusb-1.0.dll not found!")

# usb.core needs to have a usb backend loaded, this is why we needed the libusb1 package
usb_backend = libusb1.get_backend()
print("usb_backend: ", usb_backend)
backend = libusb1.get_backend(find_library=lambda x: file_libusb1)
usb_backend = libusb1.get_backend()
print("usb_backend: ", usb_backend)
if not usb_backend:
    raise Exception("Unable to load a usb backend.")

print("Starting reader_thread!")
threading.Thread(target=reader_thread, daemon=True).start()

# -----------------------
# Plotting
# -----------------------
xs = deque(maxlen=MAX_POINTS)
ys = deque(maxlen=MAX_POINTS)
t0 = time.time()

fig, ax = plt.subplots(nrows=1, ncols=1)
(line,) = ax.plot([], [], lw=2)
ax.set_title("PyUSB bulk realtime plot")
ax.set_xlabel("Time")
ax.set_ylabel("Value")

def update(_):
    got = False
    while True:
        try:
            t, v = samples_q.get_nowait()
        except Empty:
            break
        for value in v:
            xs.append(t - t0)
            ys.append(value)
        got = True

    if got and xs:
        line.set_data(xs, ys)
        xmax = xs[-1]
        xmin = max(0, xmax - WINDOW_SECONDS)
        ax.set_xlim(xmin, xmin + WINDOW_SECONDS)

        ymin, ymax = min(ys), max(ys)
        if ymin == ymax:
            ymin -= 1
            ymax += 1
        pad = 0.05 * (ymax - ymin)
        ax.set_ylim(ymin - pad, ymax + pad)

    return (line,)

ani = FuncAnimation(fig, update, interval=50, blit=False)
plt.show()

while (True):
    time.sleep(0) #Yield to scheduler