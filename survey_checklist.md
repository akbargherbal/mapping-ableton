# Control Survey Checklist

Running record of what has been surveyed. One checkbox per device/context, grouped by phase
(A–F), pulled from `survey_plan.md` §6/§7. All items start unchecked.

> **Source of truth:** the catalog (`dumps/control_catalog.json`) wins over this checklist.
> Before resuming, reconcile this file against the catalog's actual keys — never trust the
> checkboxes alone (AGENTS.md §1).

## Phase A — Native Audio Effects (47) → Track 3

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

## Phase B — Native MIDI Effects (15) → Track 1

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

## Phase C — Native Instruments (23) → Track 1

- [x] Analog
- [x] Collision
- [x] Drift
- [x] Drum Rack
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

## Phase D — Drums (2) → Track 1

- [x] Drum Rack (surveyed; Drums-category variant loaded via `query:Drums#Drum%20Rack`)
- [x] Drum Sampler (not present in Drums category; covered by Instruments survey via `query:Synths#Drum%20Sampler`)
- [x] _Note: remaining Drums entries are ~200 preset `.adg` kits that load INTO Drum Rack —
  not surveyed individually (documented in catalog, not in checklist)._

## Phase E — Plug-Ins (0)

- [x] Plug-Ins category — verified empty (Browser + `list_external_plugins` found none);
  record once as an empty category, no per-item survey.

## Phase F — Contexts (§5.4)

- [x] Arrangement View (full tree — timeline, loop brace, etc.)
- [x] Browser: Sounds tab + representative items inside
- [x] Browser: Instruments tab + representative items inside
- [x] Browser: Drums tab + representative items inside
- [x] Browser: Audio Effects tab + representative items inside
- [x] Browser: MIDI Effects tab + representative items inside
- [x] Browser: Plug-Ins tab (verify empty)
- [x] Master track
- [x] Return tracks
- [x] Group / folded tracks (logged as gap — group creation not reliably automatable; structural note recorded)
- [x] Clip Detail view
- [x] View menu sweep (other top-level views)
