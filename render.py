#!/usr/bin/env python3
"""Harmony check of the lead against the bar's chord, then render through FluidSynth + GM soundfont."""
import sys, wave
import numpy as np
import fluidsynth
import mml2mid

data, notes, tempo = mml2mid.build(sys.argv[1])
PPQ, WHOLE = mml2mid.PPQ, mml2mid.WHOLE
BAR = WHOLE

# chord per bar, read off the arp track itself (the pitch classes it plays that bar)
chords = {}
for trk, t, dur, n in notes:
    if trk == 'arp':
        chords.setdefault(t // BAR, set()).add(n % 12)
strong, off = 0, []
for trk, t, dur, n in notes:
    if trk not in ('lead', 'counter'):
        continue
    if t % PPQ == 0 or dur >= PPQ:  # on a beat, or held a beat or more
        strong += 1
        if t // BAR in chords and n % 12 not in chords[t // BAR]:
            off.append((trk, t // BAR + 1, (t % BAR) / PPQ + 1, n))
print(f'strong/long melody notes: {strong}, outside the bar chord: {len(off)}')
for o in off:
    print('  %-7s bar %2d beat %.2f  midi %d' % o)

# render: drive the synth event by event
SR = 44100
fs = fluidsynth.Synth(samplerate=SR, gain=0.35)
sf = fs.sfload(sys.argv[3] if len(sys.argv) > 3 else '/usr/share/sounds/sf2/default-GM.sf2')
assert sf != -1, 'soundfont failed to load'
# a big dark hall: large room, fairly damped highs, full width
print('set_reverb ->', fs.set_reverb(roomsize=0.92, damping=0.35, width=1.0, level=0.9))
import struct
evs = []  # (tick, order, kind, a, b, c)
chan = {}
# re-read programs from the MIDI we built, simplest: parse our own chunks
pos = 14
while pos < len(data):
    ln = struct.unpack('>I', data[pos + 4:pos + 8])[0]
    trk = data[pos + 8:pos + 8 + ln]; pos += 8 + ln
    i, t = 0, 0
    while i < len(trk):
        d = 0
        while True:
            b = trk[i]; i += 1; d = (d << 7) | (b & 0x7f)
            if not b & 0x80: break
        t += d
        st = trk[i]
        if st == 0xff:
            l = trk[i + 2]; i += 3 + l; continue
        kind = st & 0xf0; ch = st & 0x0f
        if kind == 0xc0:
            evs.append((t, 0, 'prog', ch, trk[i + 1], 0)); i += 2
        elif kind == 0xb0:
            evs.append((t, 0, 'cc', ch, trk[i + 1], trk[i + 2])); i += 3
        else:
            evs.append((t, 1 if kind == 0x80 else 2, 'on' if kind == 0x90 else 'off', ch, trk[i + 1], trk[i + 2])); i += 3
for ch in range(16):
    fs.program_select(ch, sf, 128 if ch == 9 else 0, 0)
evs.sort()
spt = 60.0 / tempo / PPQ
out, now = [], 0
for t, _, kind, ch, a, b in evs:
    tgt = int(round(t * spt * SR))
    if tgt > now:
        out.append(fs.get_samples(tgt - now)); now = tgt
    if kind == 'prog':
        fs.program_select(ch, sf, 128 if ch == 9 else 0, a)
    elif kind == 'cc':
        fs.cc(ch, a, b)
    elif kind == 'on':
        fs.noteon(ch, a, b)
    else:
        fs.noteoff(ch, a)
out.append(fs.get_samples(int(2.5 * SR)))  # let the last chord ring
pcm = np.concatenate(out).astype(np.float32)
peak = np.abs(pcm).max()
pcm = (pcm / peak * 0.89 * 32767).astype(np.int16)
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(f'rendered {len(pcm) / 2 / SR:.2f} s, pre-normalise peak {peak:.0f}')
