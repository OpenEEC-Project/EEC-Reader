#!/usr/bin/env python3.10
import serial
import serial.tools.list_ports
import time
import sys

# --- Argument Parsing ---
if len(sys.argv) < 2:
    print("Usage: python script.py <output_filename> [--trim=32k|56k]")
    sys.exit(1)

output_filename = sys.argv[1]
trim_arg = None
if len(sys.argv) > 2:
    trim_arg = sys.argv[2].lower()

# --- Handle Optional Trimming ---
trim_size = None
if trim_arg:
    if trim_arg == "--trim=56k":
        trim_size = 56 * 1024
    elif trim_arg == "--trim=32k":
        trim_size = 32 * 1024
    else:
        print("Invalid trim argument. Use --trim=32k or --trim=56k")
        sys.exit(1)
else:
    # Interactive fallback if no trim arg given
    print("Select output size:")
    print("1. Full (no trimming)")
    print("2. Trim to 56 KB")
    print("3. Trim to 32 KB")
    choice = input("Enter choice (1/2/3): ").strip()
    if choice == '2':
        trim_size = 56 * 1024
    elif choice == '3':
        trim_size = 32 * 1024

# --- Serial Setup ---
pid = "0403"
hid = "6001"
comm_port = None
ports = list(serial.tools.list_ports.comports())

for p in ports:
    if pid and hid in p.hwid:
        comm_port = p.device
        print("Using device:", comm_port)

if not comm_port:
    print("FTDI device not found.")
    sys.exit(1)

ser = serial.Serial(
    comm_port,
    baudrate=921600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)
ser.isOpen()

# --- Handshake ---
ser.write(b'\x56\x56')
time.sleep(0.02)
out = b''
while ser.inWaiting() > 0:
    out += ser.read(3)

if b'\x05\x0e\x46' in out:
    print("Burn2 Connected!")

# --- Prepare & Read ---
ser.set_buffer_size(rx_size=64000, tx_size=64000)
ser.flushInput()
ser.flushOutput()
ser.write(b'\x4A\x34\x7E')
time.sleep(0.01)

for _ in range(250):
    ser.write(b'\x43')
    time.sleep(0.01)

raw_data = ser.read(64000).strip(b'\x00')

# --- Remove Checksum Bytes ---
cleaned_data = bytearray()
for i in range(0, len(raw_data), 258):
    chunk = raw_data[i:i+258]
    cleaned_data.extend(chunk[:256])

# --- Optional Trimming ---
if trim_size is not None:
    cleaned_data = cleaned_data[:trim_size]

# --- Write Output ---
with open(output_filename, "wb", buffering=64000) as binary:
    binary.write(cleaned_data)

print(f"Done. Output written to {output_filename}")
