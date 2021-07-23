import socket
import serial
import time
import struct
import re

# from MIDI import MIDIFile, Events
from mido import MidiFile
from sys import argv

IP = '192.168.1.115'
PORT = 8101

# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# print(f"Connecting to {IP}:{PORT}")
# s.connect((IP, PORT))
print("Connecting to serial")
s = serial.Serial("/dev/ttyUSB0", 1000000)

active = []

def parse(file, speed):
    c=MidiFile(file)
    result = []
    lastType = None
    last_time = None
    t = 0
    for evt in c:
      if evt.type != "note_on" and evt.type != "note_off":
        continue
      # TODO handle octaves
      # TODO handle velocity
      n = str(evt.note)
      print(f"note {n} @{evt.time} ({time}s) {evt.type} - {active}")
      if evt.time != 0:
        # TODO we need to ensure continuity between events, assign
        # voices/phrasing to prevent large jumps in note playback
        notes = active[0:3]
        notes.sort()
        while len(notes) < 4:
          notes.append(0)
        result.append((t, notes, round(evt.time,2)))
        last_time = time
      t += (evt.time/speed)

      hz = int(getIntFrequency(int(n)))
      if evt.type == "note_on":
        active.append(hz)
      else:
        for i in range(len(active)):
          if active[i] == hz:
            del active[i]
            break
    notes = active[0:3]
    notes.sort()
    while len(notes) < 4:
      notes.append(0)
    result.append((t, notes, round(evt.time, 2)))
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
notesMIDI = [
27.5,
29.14,
30.87,
32.7,
34.65,
36.71,
38.89,
41.2,
43.65,
46.25,
49,
51.91,
55,
58.27,
61.74,
65.41,
69.3,
73.42,
77.78,
82.41,
87.31,
92.5,
98,
103.83,
110,
116.54,
123.47,
130.81,
138.59,
146.83,
155.56,
164.81,
174.61,
185,
196,
207.65,
220,
233.08,
246.94,
261.63,
277.18,
293.66,
311.13,
329.63,
349.23,
369.99,
392,
415.3,
440,
466.16,
493.88,
523.25,
554.37,
587.33,
622.25,
659.25,
698.46,
739.99,
783.99,
830.61,
880,
932.33,
987.77,
1046.5,
1108.73,
1174.66,
1244.51,
1318.51,
1396.91,
1479.98,
1567.98,
1661.22,
1760,
1864.66,
1975.53,
2093,
2217.46,
2349.32,
2489.02,
2637.02,
2793.83,
2959.96,
3135.96,
3322.44,
3520,
3729.31,
3951.07,
4186.01,
4434.92,
4698.63,
4978.03,
5274.04,
5587.65,
5919.91,
6271.93,
6644.88,
7040,
7458.62,
7902.13
]
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

def getIntFrequency(note):
    #a4offs = note - 69
    #keyNumber = a4offs % len(notes4)
    #octave = int((note - 21) / len(notes4)) # Add 1 for motor driver reasons ???
    #freq = notes4[notes[keyNumber]]
    #octaveShift = octave - 4
    # print(f"offs {a4offs} key {notes[keyNumber]} oct {octaveShift}")
    return notesMIDI[note - 21] * 2 # freq * (2 ** octaveShift)

    

def writeFreqs(fs, vs):
  buf = struct.pack('=HHBBHHBB', 
    int(fs[0]), int(fs[1]), int(vs[0]), int(vs[1]), 
    int(fs[2]), int(fs[3]), int(vs[2]), int(vs[3]))
  s.write(buf) #send(buf)
  s.flush()

def writeHz(hz):
  # print(hz)
  writeFreqs(hz, [255 if x != 0 else 0 for x in hz])

seq = parse(argv[1], float(argv[2]))
# TODO preprocess so that no events happen at the same time, and only one voice is heard

start = time.time()
idxs = [0]*4
currNotes = [0]*4

# Combine all 4 tracks into a single sequence sorted by time
#seq = []
#for i in range(4):
#  # print(tracks[i])
#  seq += list(map(lambda e: e + tuple([i]), tracks[i]))
# seq.sort(key=lambda e: e[0])

try:
  for (t, e, evtt) in seq:
    print((evtt,t,e))
    next_tick = (start + t) # - time.time()
    while time.time() < next_tick:
      continue
    writeHz(e)
finally:
  writeHz([0, 0, 0, 0])
  s.close()
