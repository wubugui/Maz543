# MAZ native wheel render text evidence — 2026-10-02

This is a lossless plaintext publication package, not a model change. It holds
67 original text records (6,643,853 bytes) through readable
Python source files and ordinary JSON value/reference tables. It also preserves
the final source manifest separately, byte for byte. Nothing here executes a
renderer unless someone explicitly chooses to execute an original render script.

## What the evidence establishes

- The full four-station / 72-glyph verification belongs to method commit
  66085d7f353b6a5ee6d441243f3e0618e2ac0b64. Render records identify actual HEAD
  bc5eced9a3c9470e2b0cff538821d701cada08de.
- The two successful views demonstrate station 0 only: each fresh process
  applied 18 qualified native Shrinkwrap modifiers and reparented one station.
  Complete four-station / 72-glyph eligibility checks and the original
  full-scene dependency guards remained. These views do not extend the full
  verification to a new four-station render replay.
- The original source SHA-256 before and after both successful runs was
  8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70.
  Source bytes remained unchanged. Both successful finally-restorations passed.
- Both views used exactly the same camera matrix, orthographic scale, lights
  settings and resolution. Original material/world/visibility/identity guards
  passed within each process. Pointer-derived material/shader fingerprints
  are not comparable across processes; no cross-process pixel-identity claim
  is made.
- All 16 whole-vehicle gates remain OPEN. Original materials, original geometry,
  occlusions and step interference remain. Camber remains zero; drums remain
  the original simplified proxies.
- The wheel, hub inflation line, nuts and tread visibly change orientation.
  Lettering is not clearly readable in either image, so the pair does not
  visually establish readable lettering movement. The interior drum remains
  occluded and has numerical witness evidence only.

## Attempts and qualifications

| Attempt | Process elapsed | Result |
| --- | ---: | --- |
| attempt-01 | 117.239 s | Internal planned deadline; 0 PNG; restoration unconfirmed |
| attempt-02 | 150.068 s | Unexpected SIGKILL before its deadline; cause UNKNOWN; 0 PNG; restoration unconfirmed |
| attempt-station0-neutral-01 | 112.018 s | One actual local PNG; successful station-0-only run |
| attempt-station0-spin-01 | 110.494 s | One actual local PNG; successful station-0-only run |

The failed-attempt records, partial logs and historical manifests are preserved
exactly. Later success does not rewrite the earlier failures or prove the cause
of the SIGKILL. Failure-specific diagnostic snapshots remain as original
relevant evidence; no unrelated host inventory is added.

## Images are references, not payloads

The final source manifest records these two original local images:

| Original relative path | Bytes | SHA-256 |
| --- | ---: | --- |
| attempt-station0-neutral-01/wheel-neutral.png | 1,178,213 | 7b173610175dbc2f894c1b8fc23708c0d1a090429701de1cb615938ffb8306a8 |
| attempt-station0-spin-01/wheel-spin-0p731.png | 1,178,538 | 1291eb1f34f4d40d15cb6fbf58c8995d572081f9324ecb5ba67e53d9cb1be8a2 |

The two views were delivered through the authorized channel. Returned delivery
copies contained 511 fewer PNG-encoding bytes each, while their decoded RGBA
pixel bytes matched their corresponding originals exactly. The manifest hashes
above identify the original local PNG encodings, not the returned encodings.
No channel identifier, link, or delivery receipt is included here.

Their combined 2,356,751 bytes are absent from this package. PNG, blend and GLB
bytes are never packed into JSON, text, or Git blobs. No new LFS upload exists;
this package does not claim that images are in Git or LFS. It contains no private
message destination, signed storage URL or delivery receipt.

## Read and restore

1. Read this README, STATION0-FINAL-MANIFEST.json and package-index.json first.
2. Original Python scripts are directly readable under sources/. The index
   explicitly maps every original script path to its stored source file.
   Equal source files share one exact copy; all original paths are restored.
3. Run the following command from this package, using an output path that does
   not exist:

   python -B package-wheel-render-evidence.py restore --package . --out /tmp/maz-render-restored-UNUSED

Restoration writes only the 67 original text records and the separate final
manifest. It verifies every byte count and SHA-256 and then independently checks
the three older failed-attempt manifests against their referenced records. It
never creates PNG/blend/GLB files, starts Blender, or changes a repository.
An existing restore destination is refused before anything is written.

To inspect or audit an original run, read the restored attempt's executed-runner.py,
executed-script.py, launch.json, reviewed-plan.json and process.json, together
with its log, terminal record and outcome/report. Those are the exact replay
sources and original launch records. Their absolute paths and prerequisites
are historical evidence, not a claim of portability or authorization to rerun
an engine. Text restoration is the only replay performed for this package.

## Representation and reproducibility

The unchanged codec pack-wheel-interface-evidence.py has SHA-256
2334d0734b5e6edbd289692be6d4c8da50daba4b3f770142400971c75091a11d and uses PLAIN_JSON_INTERFACE_TABLE_v1. Its
31 table shards total 3,335,069 bytes.
Entries are plain JSON scalar values, arrays of references, or objects with
named fields and references; references point backward. There is no zlib,
base64, binary string wrapper, or asset encoding.

For each original .json record, structured storage is selected only when
Python json.dumps(value, indent=2, ensure_ascii=True) plus LF, UTF-8 encoded,
reproduces its exact source bytes. Otherwise its original text is stored.
For text/log records, each line retains its original line ending and is split
only at literal |. Restoration joins each line's parts with |, then concatenates
all lines. Unknown lines remain unchanged. No normalization or approximation
occurs. package-index.json records the representation of every original path.

To rebuild in another unused directory from the original frozen source:

   python -B package-wheel-render-evidence.py build --source /path/to/maz-native-wheel-views-20261002 --out /tmp/maz-render-package-UNUSED --codec ./pack-wheel-interface-evidence.py

The builder pins the source manifest hash to
8c5928ae9b8b6731cab529fc5f92bb2858ccaa76c9b396221f0ae8d0f24180fd. It reads
only the 67 allowlisted original text files and that manifest. The PNG manifest
entries are preserved as references only; the builder never opens asset bytes.

VERIFICATION.json records a separate-process restoration and independent
byte-for-byte comparison against all originals, plus the old manifest checks.
PUBLICATION-FILES-MANIFEST.json inventories the complete publication package,
excluding itself. No publication or external delivery is performed by these tools.
