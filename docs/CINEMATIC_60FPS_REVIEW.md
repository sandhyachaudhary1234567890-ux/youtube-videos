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
