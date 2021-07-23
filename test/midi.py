import socket
import serial
import time
import struct
import re
import argparse

# from MIDI import MIDIFile, Events
from mido import MidiFile
from sys import argv

def parse(file, speed, debug, nchan, force_custom_voices):
    c=MidiFile(file)

    # Channel detection
    if force_custom_voices:
      ignore_channels = True
      print("WARNING: forcing use of custom voicing")
    else:
      ignore_channels = (len(set([evt.channel for evt in c if evt.type == "note_on"])) == 1)
      if ignore_channels:
        print("WARNING: single midi channel detected; using custom voicing")


    OFF = (0,0)
    result = []
    lastType = None
    last_time = None
    t = 0
    active = [] if ignore_channels else [OFF]*nchan
  
    for evt in c:
      if evt.type != "note_on" and evt.type != "note_off":
        continue
      if debug:
        print(f"ch{evt.channel} note {evt.note} vel {evt.velocity} @{evt.time} ({time}s) {evt.type} - {active}")

      # evt.time is relative time - if we're advancing in time then push a snapshot of the notes
      if evt.time != 0:
        # TODO we need to ensure continuity between events, assign
        # voices/phrasing to prevent large jumps in note playback
        if ignore_channels:
          notes = active[:nchan]
          notes += [OFF] * (nchan - len(notes))
        else:
          notes = list(active)
        result.append((t, notes, evt.time))
        last_time = time
      t += (evt.time/speed)

      hz = int(getIntFrequency(evt.note))
      i = evt.channel % nchan # Prevent overflowa
      if evt.type == "note_on":
        e = (hz, 2*evt.velocity) # Max midi velocity is 127, not 255
        if ignore_channels:
          ins = False
          for (i, nv) in enumerate(active):
            if nv[0] == 0:
              active[i] = e
              ins = True
              break
          if not ins:
            active.append(e)
        elif active[i][0] == 0:
          active[i] = e 
      else:
        if ignore_channels:
          for (i, nv) in enumerate(active):
            if nv[0] == hz:
              active[i] = OFF
              break
          # Pack down, preserving currently active notes
          newActive = active[:nchan]
          tail = active[nchan:]
          for i in range(len(newActive)):
            if newActive[i][0] == 0 and len(tail) > 0:
              newActive[i] = tail.pop(0)
          active = newActive + tail
        elif active[i][0] == hz:
          active[i] = OFF

    # Snapshot end state
    if ignore_channels:
      notes = active[:nchan]
      notes += [OFF] * (nchan - len(notes))
    else:
      notes = list(active)
    result.append((t, notes, evt.time))
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
notesMIDI = [ # Starting at A0, index 21 (see getIntFrequency)
27.5, 29.14, 30.87, 32.7, 34.65, 36.71, 38.89, 41.2, 43.65, 46.25, 49, 51.91, 55, 58.27, 61.74, 65.41, 69.3, 73.42,
77.78, 82.41, 87.31, 92.5, 98, 103.83, 110, 116.54, 123.47, 130.81, 138.59, 146.83, 155.56, 164.81, 174.61, 185, 196,
207.65, 220, 233.08, 246.94, 261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392, 415.3, 440, 466.16, 493.88, 523.25,
554.37, 587.33, 622.25, 659.25, 698.46, 739.99, 783.99, 830.61, 880, 932.33, 987.77, 1046.5, 1108.73, 1174.66, 1244.51, 1318.51,
1396.91, 1479.98, 1567.98, 1661.22, 1760, 1864.66, 1975.53, 2093, 2217.46, 2349.32, 2489.02, 2637.02, 2793.83, 2959.96, 3135.96,
3322.44, 3520, 3729.31, 3951.07, 4186.01, 4434.92, 4698.63, 4978.03, 5274.04, 5587.65, 5919.91, 6271.93, 6644.88, 7040, 
7458.62, 7902.13 
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
    return notesMIDI[note - 21] * 2 # Double freq for motor control reasons

def writeNotes(ns):
  buf = struct.pack('=HHBBHHBB', 
    int(ns[0][0]), int(ns[1][0]), int(ns[0][1]), int(ns[1][1]), 
    int(ns[2][0]), int(ns[3][0]), int(ns[2][1]), int(ns[3][1]))
  s.write(buf)
  s.flush()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Parse and send MIDI to device orchestra")
    parser.add_argument("file", metavar='DEST', type=str, help="the file to play")
    parser.add_argument("--dev", type=str, default="/dev/ttyUSB0", help="target device (\"/dev/tty*\" or \"<ip>:<port>\")")
    parser.add_argument("--baud", type=int, default=1000000, help="baud rate if --dev is a serial device")
    parser.add_argument("--speed", type=float, help="Speed multiplier", default=1.0)
    parser.add_argument("--verbose", type=bool, default=False, help="Show debug text")
    parser.add_argument('--force-custom-voices', dest='force_custom_voices', action='store_true')
    parser.set_defaults(force_custom_voices=False)
    parser.add_argument("--nchan", type=int, default=4, help="Number of device channels")
    parser.add_argument("--loop", type=int, default=0, help="Number of times to loop (-1 loops forever")
    args = parser.parse_args()

    if ":" in args.dev:
      (ip, port) = [sp.trim() for sp in args.dev.split(":")] # e.g. (192.168.1.115, 8101)
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      if args.verbose:
        print(f"Connecting to {IP}:{PORT}")
      s.connect((ip, int(port)))
      s.write = s.send # Compatibility with serial sending
      # s.flush = lambda
    else:
      if args.verbose:
        print("Connecting to serial")
      s = serial.Serial(args.dev, 1000000)

    seq = parse(args.file, args.speed, args.verbose, args.nchan, args.force_custom_voices)
    try:
      i = 0
      while True:
        start = time.time()
        for (t, e, evtt) in seq:
          if args.verbose:
            print(evtt,t,e)
          next_tick = (start + t) # - time.time()
          while time.time() < next_tick:
            continue
          writeNotes(e)
        if i == args.loop:
          break
        i += 1
    finally:
      writeNotes([(0,0)]*args.nchan)
      s.close()

