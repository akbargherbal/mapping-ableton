# Survey Checklist — Ableton Live Control Catalog

One checkbox per device/context, grouped by phase A–F. The running
record of *what* has been surveyed. Device names and counts are pulled
from the real Browser via AbletonMCP (2026-08-07) — source of truth per
AGENTS.md §5.1. **The catalog (`dumps/control_catalog.json`) wins over
this checklist on resume: an item only counts as done if a matching
context exists in the catalog.**

## Phase A — Audio Effects (47)

- [x] Align Delay
- [x] Amp
- [x] Audio Effect Rack
- [x] Auto Filter
- [x] Auto Pan
- [x] Auto Shift
- [x] Beat Repeat
- [x] Cabinet
- [x] Channel EQ
- [x] Chorus-Ensemble
- [x] Compressor
- [x] Corpus
- [x] Delay
- [x] Drum Buss
- [x] Dynamic Tube
- [x] Echo
- [x] Envelope Follower
- [x] EQ Eight
- [x] EQ Three
- [x] Erosion
- [x] External Audio Effect
- [x] Filter Delay
- [x] Gate
- [x] Glue Compressor
- [x] Grain Delay
- [x] Hybrid Reverb
- [x] LFO
- [x] Limiter
- [x] Looper
- [x] Multiband Dynamics
- [x] Overdrive
- [x] Pedal
- [x] Phaser-Flanger
- [x] Redux
- [x] Resonators
- [x] Reverb
- [x] Roar
- [x] Saturator
- [x] Shaper
- [x] Shifter
- [x] Spectral Resonator
- [x] Spectral Time
- [x] Spectrum
- [x] Tuner
- [x] Utility
- [x] Vinyl Distortion
- [x] Vocoder

## Phase B — Instruments (23)

- [x] Analog
- [x] Collision
- [x] Drift
- [ ] Drum Rack (surveyed in Phase D)
- [x] Drum Sampler
- [x] DS Clang
- [x] DS Clap
- [x] DS Cymbal
- [x] DS FM
- [x] DS HH
- [x] DS Kick
- [x] DS Snare
- [x] DS Tom
- [x] Electric
- [x] External Instrument
- [x] Impulse
- [x] Instrument Rack
- [x] Meld
- [x] Operator
- [x] Sampler
- [x] Simpler
- [x] Tension
- [x] Wavetable

## Phase C — MIDI Effects (15)

- [x] Arpeggiator
- [x] CC Control
- [x] Chord
- [x] Envelope MIDI
- [x] Expression Control
- [x] MIDI Effect Rack
- [x] MIDI Monitor
- [x] MPE Control
- [x] Note Echo
- [x] Note Length
- [x] Pitch
- [x] Random
- [x] Scale
- [x] Shaper MIDI
- [x] Velocity

## Phase D — Drums

- [x] Drum Rack (the only device; ~150 kit presets `.adg` are out of scope as devices — noted, not surveyed)

## Phase E — Plug-Ins (VST/AU)

- [x] Plug-Ins category — confirm empty / no external plugins, log status (`OPAQUE`/none)

## Phase F — Everything else (§5.4)

- [x] Session View — full tree (transport, tempo, track mixer strips)
- [x] Arrangement View — full tree (timeline, loop brace)
- [x] Browser panel — six top-level tabs (`(control_type, name)` match, no automation_id): Sounds, Instruments, Drums, Audio Effects, MIDI Effects, Plug-Ins
- [x] Browser items INSIDE categories — sample representative few per category (do they carry automation_ids, or behave like the tabs?)
- [x] Master track
- [x] Return tracks (2 in session)
- [x] Group / folded tracks (structural diff vs normal mixer strip; create one to survey if none exists)
- [x] Clip Detail view (create a clip to render it if needed)
- [x] Other top-level views (check View menu — e.g. Overview in Live 12)

## Notes

- Survey order: Phase A → B → C → D → E → F (predictable, resumable).
- Write `dumps/control_catalog.json` after every item (AGENTS.md §7).
- On resume: reconcile this checklist against the catalog first; the
  catalog wins (§1).
