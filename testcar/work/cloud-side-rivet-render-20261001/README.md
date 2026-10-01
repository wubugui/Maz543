# Native same-camera head attachment inspection

Actual Blender4.5.13 Cycles CPU2 renders,1200×900,32 samples with native denoising.
The pinned original Master and the already published140-head in-memory replay
are shown using exactly the same camera, lighting and diagnostic finishes.
The central subject is retained head60 on the lower side-sill row. The original
head form and skin geometry are not redesigned for the images.

Both final image pixel arrays were viewed. The original shows the head standing
away from its supporting plane and a displaced shadow. The trial shows the same
head translated toward the skin and a contact-area shadow. Measurement comes
from the independently verified native vertex result, not from image pixels.
A neighbouring head is partially outside the close-up; this is not a full-body
or full-component framing claim.

Gold heads and green skin are temporary inspection material overrides. Other
geometry is hidden from these isolated renders only. No `.blend` was saved and
no production/browser object was changed. These are native renders, not browser
screenshots. The full vehicle, source materials, ten unsupported heads and six
retained closed contact pairs are not visually accepted by these close-ups.

## Actual files and publication boundary

- before: SHA256 `27bcb092edef9b30d630a5a1016dd9cf88ea7483e888f62529de70700024d0eb`,1094170 bytes
- after: SHA256 `3b0aed9f5f571803dd8ec23ab03841a89e0b97260c22aefa2d110a79296c9843`,1090464 bytes

PNG bytes remain outside this Git checkout for authorized progress delivery.
They are **not newly uploaded Git LFS entities**; no pointer or encoded substitute
is committed. This commit contains the native rendering script, geometry/image
provenance, pixel-review record and actual terminal process logs. Proper image
LFS publication still requires the unresolved official upload route.

Before/after successful processes took70.980s and75.238s; this is not an isolated
performance benchmark. Both begin/end script hashes match. The native source
SHA is unchanged and render setup leaves each evaluated displayed mesh's
positions, triangles and transforms unchanged.

## Retained unsuccessful first images

`iteration-01-overexposed/` retains the initial render script, metadata, logs and
explicit failure record. Its original powers/inherited scene settings produced
excessive brightness; captions were partly occluded. Those PNGs remain locally
retained and are not presented as successful views. Iteration02 explicitly sets
AgX/exposure/gamma, disables the inherited compositor/sequencer, lowers only the
diagnostic lamps and brings labels forward. It retains the exact camera and
vehicle geometry.

The initial process wrapper hashed the file at process end; after-render metadata
therefore captured an updated on-disk script SHA while the old script was already
loaded in Blender. This is explicitly corrected by the retained executed script
and failure record, not silently treated as a verified invocation hash. Final
invocations bind and check the script SHA before and after execution.

## Reproduce

From the repository, with the exact published source materialized:

    blender --background --factory-startup --disable-autoexec --threads 2 \
      --python-exit-code 1 --python /absolute/path/testcar/scripts/render-side-rivet-native-attachment.py \
      -- --mode before --output-root /absolute/new/inspection-directory
    blender --background --factory-startup --disable-autoexec --threads 2 \
      --python-exit-code 1 --python /absolute/path/testcar/scripts/render-side-rivet-native-attachment.py \
      -- --mode after --output-root /absolute/new/inspection-directory

Each render is bounded externally at180 seconds in the recorded invocation.
Existing image filenames are refused rather than overwritten. The after process
replays and verifies the native attachment changes before rendering. All16
whole-vehicle gates remain OPEN.
