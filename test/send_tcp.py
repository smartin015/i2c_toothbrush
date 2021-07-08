import socket
import struct
import time

IP = '192.168.1.115'
PORT = 8101

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(f"Connecting to {IP}:{PORT}")
s.connect((IP, PORT))

def writeFreqs(fs, vs):
  buf = struct.pack('=HHBBHHBB', 
    fs[0], fs[1], vs[0], vs[1], 
    fs[2], fs[3], vs[2], vs[3])
  s.send(buf)

try: 
  while True:
    print("write 220")
    writeFreqs([220, 220, 220, 220], [255]*4)
    time.sleep(0.5)
    print("write 440")
    writeFreqs([440, 440, 440, 440], [255]*4)
    time.sleep(0.5)

finally:
  s.close()
