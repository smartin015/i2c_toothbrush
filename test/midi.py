import socket
import serial
import time
import struct
import re

from MIDI import MIDIFile, Events
from sys import argv

IP = '192.168.1.115'
PORT = 8101

# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# print(f"Connecting to {IP}:{PORT}")
# s.connect((IP, PORT))
print("Connecting to serial")
s = serial.Serial("/dev/ttyUSB0", 115200)

tracks = [[],[],[],[]]
active = [None]*4

def parse(file, speed):
    c=MIDIFile(file)
    c.parse()
    # print(str(c))
    # Assume single track
    track = c[0]
    print("parsing track")
    track.parse()

    result = []
    lastType = None
    for evt in track:
      if type(evt) != Events.midi.MIDIEvent:
        continue
      if type(evt.message) != Events.messages.notes.NoteMessage:
        continue
      # TODO handle octaves
      # TODO handle velocity
      n = str(evt.message.note)
      note = (evt.time/(c.division*speed), n, evt.message.onOff)
      if evt.message.onOff == "ON":
        for i in range(4):
          if active[i] is None:
            active[i] = n
            tracks[i].append(note)
            break
      else:
        for i in range(4):
          if active[i] == n:
            tracks[i].append(note)
            active[i] = None
            break
        
    #print(tracks[0][0:10])
    #print(tracks[1][0:10])
    #print(tracks[2][0:10])
    #print(tracks[3][0:10])
    return result


# https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e
# MIT License
# Python to convert a string note (eg. "A4") to a frequency (eg. 440).
# Inspired by https://gist.github.com/stuartmemo/3766449
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
def getFrequency(note):
    m = re.search(r"^([A-G]\#?)(\d+)", note)
    (notename, octave) = (m[1], int(m[2]))
    if octave > 8:
      return 0
    keyNumber = notes.index(notename)
    freq = notes4[notes[keyNumber]]
    # print(notes[keyNumber], octave)

    octaveShift = octave - 4
    return freq * (2 ** octaveShift)

def writeFreqs(fs, vs):
  buf = struct.pack('=HHBBHHBB', 
    int(fs[0]), int(fs[1]), int(vs[0]), int(vs[1]), 
    int(fs[2]), int(fs[3]), int(vs[2]), int(vs[3]))
  s.write(buf) #send(buf)
  s.flush()

def writeHz(hz):
  # print(hz)
  writeFreqs(hz, [255 if x != 0 else 0 for x in hz])

parse(argv[1], float(argv[2]))
# TODO preprocess so that no events happen at the same time, and only one voice is heard

start = time.time()
idxs = [0]*4
currNotes = [0]*4

seq = []
for i in range(4):
  # print(tracks[i])
  seq += list(map(lambda e: e + tuple([i]), tracks[i]))
seq.sort(key=lambda e: e[0])

try:
  for e in seq:
    (t, note, onoff, tnum) = e
    next_tick = (start + t) # - time.time()
    while time.time() < next_tick:
      continue
    #if next_tick > 0.01:
    #  time.sleep(next_tick) # Not super accurate, but probably good enough

    if onoff == "ON":
      hz = getFrequency(note)
      currNotes[tnum] = hz
    else:
      currNotes[tnum] = 0
    writeHz(currNotes)
finally:
  writeHz([0, 0, 0, 0])
  s.close()
