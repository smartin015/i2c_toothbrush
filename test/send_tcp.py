import socket
import struct
import time

IP = '192.168.1.115'
PORT = 8101

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(f"Connecting to {IP}:{PORT}")
s.connect((IP, PORT))


# https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e
# MIT License
# Python to convert a string note (eg. "A4") to a frequency (eg. 440).
# Inspired by https://gist.github.com/stuartmemo/3766449
def gf(note):
    note = note.upper()
    notes = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
    notes4 = {
      'A': 440,
      'A#': 466.16,
      'B': 493.88,
      'C': 261.63,
      'C#': 277.18,
      'D': 293.66,
      'D#': 311.13,
      'E': 329.63,
      'F': 349.23,
      'F#': 369.99,
      'G': 392.00,
      'G#': 415.30,
    }
    octave = int(note[2]) if len(note) == 3 else int(note[1])
    keyNumber = notes.index(note[0:-1]);
    freq = notes4[notes[keyNumber]]
    print(notes[keyNumber], octave)

    octaveShift = octave - 4
    return freq * (2 ** octaveShift)


def writeFreqs(fs, vs, duration = 0.5):
  buf = struct.pack('=HHBBHHBB', 
    int(fs[0]), int(fs[1]), int(vs[0]), int(vs[1]), 
    int(fs[2]), int(fs[3]), int(vs[2]), int(vs[3]))
  s.send(buf)
  time.sleep(duration)

KEY = 220
try: 
  while True:
    print("write A major")
    writeFreqs([gf("A4"), gf("c#5"), gf("e5"), gf("a6")], [255]*4)
    writeFreqs([gf("B4"), gf("d5")]*2, [255]*4)
    writeFreqs([gf("C#5"), gf("e5")]*2, [255]*4, 0.25)
    writeFreqs([gf("d5"), gf("f#5")]*2, [255]*4, 0.25)
    writeFreqs([gf("e5"), gf("g#5")]*2, [255]*4)
    writeFreqs([gf("f#5"), gf("a6")]*2, [255]*4)
    writeFreqs([gf("g#5"), gf("b6")]*2, [255]*4)
    writeFreqs([gf("a5"), gf("c#6")]*2, [255]*4)
    print("write 440")
    writeFreqs([440, 440, 440, 440], [20]*4)

finally:
  s.close()
