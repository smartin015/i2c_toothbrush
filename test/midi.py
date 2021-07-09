import socket
import serial
import time
import struct

from MIDI import MIDIFile, Events
from sys import argv

IP = '192.168.1.115'
PORT = 8101

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(f"Connecting to {IP}:{PORT}")
s.connect((IP, PORT))
time.sleep(5)

def parse(file, speed):
    c=MIDIFile(file)
    c.parse()
    print(str(c))
    # Assume single track
    track = c[0]
    track.parse()

    result = []
    for evt in track:
      if type(evt) != Events.midi.MIDIEvent:
        continue
      if type(evt.message) != Events.messages.notes.NoteMessage:
        continue
      # TODO handle octaves
      # TODO handle velocity
      n = str(evt.message.note)
      result.append((evt.time/(c.division*speed), n, evt.message.onOff)) 
      # evt.time, evt.message)
    return result


# https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e
# MIT License
# Python to convert a string note (eg. "A4") to a frequency (eg. 440).
# Inspired by https://gist.github.com/stuartmemo/3766449
def getFrequency(note):
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

def writeHz(hz):
  if hz == 0:
    writeFreqs([0]*4, [0]*4, 0)
  else:
    writeFreqs([hz]*4, [255]*4, 0)

seq = parse(argv[1], float(argv[2]))
print(seq)
# TODO preprocess so that no events happen at the same time, and only one voice is heard


start = time.time() + seq[0][0]
try:
  for e in seq:
    (t, note, onoff) = e
    next_tick = (start + t) - time.time()
    print("Sleep", next_tick)
    if next_tick > 0.01:
      time.sleep(next_tick) # Not super accurate, but probably good enough

    if onoff == "ON":
      hz = getFrequency(note)
      print("play", note, "->", hz)
      writeHz(int(hz))
    else:
      print("ignore", note)
      hz = 0
finally:
  writeHz(0)
  s.close()
