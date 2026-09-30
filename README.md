# mml

A small Music Macro Language dialect, a compiler from it to Standard MIDI Files, and a
renderer that plays the MIDI through FluidSynth.

    python3 mml2mid.py songs/keynote.mml keynote.mid
    python3 render.py songs/keynote.mml keynote.wav /usr/share/sounds/sf2/FluidR3_GM.sf2

The dialect is documented at the top of `songs/keynote.mml`. One token has one meaning:
`o` octave, `l` default length, `< >` octave down and up, `c d+ e-` notes, `r` rest,
`nNN` raw MIDI note, `{c e g}2` chords, `[ ... ]N` repeats, `v` velocity, `@N` program
change, `!tag,value` a MIDI cue point with text `tag:value`, and `$NAME = ...` macros.
Header lines set `#tempo`, `#transpose`, `#ppq` and `#humanize`; `@track` lines take
`ch`, `prog`, `v`, `rev`, `cho`, `pan` and `vol`.

`render.py` also checks each melody note that lands on a beat, or lasts one, against the
chord the arpeggio track plays that bar, and lists the ones outside it.

The songs:

- `keynote.mml`, `keynote-minor.mml`: a product-reveal style tune, in D major and B minor.
- `keynote-reveal.mml`: the two joined, minor for three quarters, then a climb into major.
  Its cue points mark the sections; converted with midi2psm, it drives the keynote demo
  in [nugget](https://github.com/pcsx-redux/nugget).
- `abyss.mml`, `abyss-march-in-collapse.mml`: a slow orchestral piece in D minor, with and
  without a separate march movement.
