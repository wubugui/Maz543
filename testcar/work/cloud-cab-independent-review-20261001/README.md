# Independent door-scope review and checker regression

The independent review used Blender 4.5.13 and the exact published Master SHA
8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70.
`independent-review.json` and `independent-review-script.py` preserve the original
executed output and script. The script was run before the checker was edited.
Its old checker is frozen as `auditor-before-fix.py` from a8721fe. The original
historical script still references its old cloud/tmp paths and a live checker;
it is not the stable regression entry point after the fix. Use
`scripts/test-cab-dependency-guards.py` with `auditor-before-fix.py` for that.

Original script SHA256: 23715858d86403e447c6de1909173b6b926d3f3487917db02018e95121218f01
Original output SHA256: 5828ad1713d676227fae4192fefb359da4f7a7172b88f0b7ab3eabf041a03d06
Old checker SHA256: cd5bc72f30e60663668611798e5d7c9e384d969f3e60b63588940d561d1ccc8c

The independent run enumerated alternative trigonometric extrema for all 11484
pairs, reproducing every saved gap exactly. All 435 relevant actual objects had
OBJECT parenting and no rigid-body/pose/external Curve/Text Object inputs.
Four actual hinges have unit rotation/scale bases and EMPTY parents. The exact
source remains unchanged. Scope remains 44 door objects against 261 selected cab
objects, at frame zero with the button released and other controls fixed.

A separate real fixture exposed a general checker defect: FONT.follow_curve
was not traversed. At fixed frame zero, rotating its independent input hinge by
0.7 radians moved 34 text vertices by up to 2.765747175m while the old audit
reported no issue. This pointer is absent from the exact published Master, so
the defect is not evidence that the recorded source result is false.

The fixed checker rejects data Object pointers, unsupported parenting, rigid/
pose inputs and external libraries, including on hinges. It validates the
complete pair-index product, name ordering, angle domains and sampled evidence.
`guard-regression.json` records the actual small-fixture test of the fix, including
old-accept/new-reject on the moving text and six deliberately corrupted evidence
cases. It never loaded or saved the project blend. Its log retains a nonfatal
extension-cache write warning from the read-only default config directory.

`independent-review-replay.py` adapts only root/checker/output paths of the old
review script, fixes the old checker input, and writes a distinct replay output.
This path-adapted replay is syntax-checked, not rerun as another independent
review. Run it from this directory with the exact Blender version if needed.
Do not overwrite the original failed-fixture evidence or call any of these
limited checks whole-vehicle acceptance. All 16 gates remain OPEN.

The 20-micrometre pad is a chosen numerical guard, not a derived all-angle bound
on Blender floating-point error. The observed finite-pose error is not a
substitute for such a bound. A later single full-source dependency-only rerun
should confirm the hardened checker introduces no false rejection; that rerun
has not been performed in this checkpoint.
