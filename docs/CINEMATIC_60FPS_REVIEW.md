# Cinematic 60fps review build

The existing MASTER is preserved. The new renderer writes a separate
`videos/Tum_Hi_Se_Baat_Kar_Raha_Hoon_10min_60FPS_REVIEW.mp4` only after all chunks finish.
Run from repository root: `python3 -u scripts/render_master_video_60fps.py`.
Dependencies: Pillow, NumPy, imageio-ffmpeg. Rendering is CPU intensive.

## Editorial direction
Story first: sharp hook, escalating evidence, a calm mental-health pause,
then practical action. Thematic plate pools, 131 planned shots, moving camera
planes and foreground atmosphere replace frozen backgrounds. Transition families:
short whip/slide blends, zoom-through, diagonal wipe and warm light leak.
These are original approximations, not copied creator assets. Generated JPGs are
illustrative, not authentic documentary footage. No licensed external video clips
have been downloaded or cleared. Face-cam imagery remains placeholder material.

## Reference research
- https://trydemotion.com/blog/editing-style-tutorial — documentary pacing,
  story-led cuts, J/L cuts and sound-led continuity.
- https://www.docfilmacademy.com/blog/6-steps-to-editing-an-engaging-documentary
  — fine cut, ambience, sound design and grading.
- https://artlist.io/blog/editing-techniques/ — sound bridges and J/L cuts.
These are written editing references, not a claim to have watched or analyzed
specific creators' videos frame by frame.

## Safeguards / review still required
- 1920x1080, 60 individually rendered frames/second; not frame duplication.
- Existing voice and music/SFX stems reused; no copied SFX tracks.
- Entire manifest Tele-MANAS placement explicitly mutes the bed. No added
  atmosphere or transition effects inside it; camera movement is gentle only.
- Existing source labels and narration are retained, NOT independently verified.
  Fact-bank accuracy must be checked before publication.
- Current implementation uses a clean photo camera plane and animated foreground
  particles, not segmented-subject depth maps. Counters are animated counts,
  not a fully implemented rolling odometer.
- Full runtime, frame count, sync, file size and perceptual quality remain pending
  until the long render finishes. Do not replace MASTER until reviewed.
- CRF26 does not guarantee a sub-75MB repository. No final size claim yet.

## Second editorial pass — 2026-10-23

Additional research: International Documentary Association, [Secrets of Sound
Design, Part 1](https://www.documentary.org/feature/heard-any-good-docs-latelythe-secrets-sound-design-part-1).
The article argues for planning the soundtrack, varying acoustic textures, and
using silence deliberately. Applied here as selective accents instead of a
whoosh on every edit. No claim of watching creators' videos or accessing their
project files.

Implemented:
- 77 of 131 shots use clean cuts; 20 whip, 13 burn, 11 wipe, 9 gentle fade,
  1 zoom transition. The counts may change if the manifest changes.
- 29 original, deterministic, band-limited transition sweeps, with 120ms audio
  anticipation, at least six seconds apart and avoiding existing cue-sheet events.
- No scheduled RGB glitches or opening white flash. Face-cam has restrained drift.
- Thematic atmosphere only: no arbitrary ticking clock on unrelated imagery.
- Directional multi-tap blur on whip transitions; caption width constrained.
- Camera path now uses smooth ease-in/ease-out with less wasted per-frame work.
- Shared audio filter fixes the reused voice sidechain by explicitly splitting it;
  voice replacement keeps the entire safe zone free of bed audio, too.
- Manifest start/end values are authoritative (some stored durations round by 1ms).
- Four automated tests cover schedule reproducibility and coverage, selective
  transitions, cue spacing and sample-level silence of the synthesized SFX stem.

A continuous 12-second excerpt from 02:34–02:46 is rendered separately by
`python3 scripts/render_cinematic_excerpt.py`. It is not the final 10-minute master.
Subtitles remain approximate segment-based timing, not word-aligned transcription.
Primary-source fact checking, real face-cam replacement, live-action B-roll sourcing,
full-runtime QC and final size verification are still outstanding.

### Completed validation for second pass
- `python3 -m unittest discover -s tests -v`: 4/4 passed.
- Rendered 393 boundary/transition/midpoint frames across all 131 shots; no errors.
- Actual 12-second excerpt decoded in full: 720 frames, 1920x1080 H.264,
  progressive yuv420p, 60 fps, AAC stereo. File size approximately 1.5 MiB.
- Shared full-master audio filter executed against the actual stems successfully.
- These checks do NOT establish word-perfect subtitle alignment or verify sources.
