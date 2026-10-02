# Publication verification

The 30-file worker delivery remains byte-exact; its manifest lists the other
29 files. The applied six script paths have been independently checked against
the execution source map. `parent-review.json` records the additional review.

`checks/lint.json` is original oxlint output including trailing spaces and a
blank terminal line. Only that raw evidence path is excluded from the whitespace
check; it is not normalized. All other staged text passes `git diff --check`.
The native successful run and both guard reports were not regenerated for this
publication; the parent independently replayed the final guard outside the repo
and verified its two reports are byte-identical.
