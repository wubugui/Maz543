# MAZ543A Textured front-four native source, lossless binary parts

This directory is the canonical Git representation of the saved, editable Blender candidate. GitHub contains128 ordered raw binary parts, not a directly stored single .blend file, LFS pointers, Base64 text files or a second backup format. Concatenating the checked parts restores the original100052636bytes exactly, with SHA-25648dbc4987780b8f3781aa6c815452d140c1f2bccfd10df0c3dbc7974d04fdeea.

The complete-file GitHub-plugin argument was133403516Base64 characters; the measured code-mode IPC frame was133403855bytes and exceeded its67108864-byte maximum. The expected single blob was independently queried through the plugin and returned404. GitHub's100MiB ordinary-file limit was not the failure: the model is95.417629MiB. The selected engineering remedy keeps every original native byte in768KiB-or-smaller binary parts, each sent with the plugin's standard Base64 API encoding. Only these128 exact new .bin paths have ordinary-Git attribute exceptions; existing LFS assets and global patterns remain intact.

Restore after retrieving this complete directory from the repository, using a new unused output path:

    python -B restore_native.py --output /path/to/new/MAZ543A_Textured_Front_Wheel_Parent_Study.blend

The restorer checks order, offsets, sizes, every part's SHA-256/Git SHA, and the full SHA-256 before creating an output. It checks the write again and atomically installs the verified file without overwriting an existing output. A missing, corrupt, reordered or unsafe part fails closed. Seven small integrity controls exercise success plus these failures and existing-output preservation. No Blender reconstruction or geometry regeneration is involved.

This is the fixed-frame front-four candidate previously built/fresh-opened in a0997f7d. It preserves all8518 original objects and adds4joint frames, retains original action key data, and has only finite frame0 geometry/property-motion qualification. The global timeline, steering/CV/installation and all16 vehicle gates remain OPEN. The visual attempt did not produce a completed PNG.

The initial publication is pending independent complete remote-byte retrieval, restoration in a clean directory, and native fresh-open verification. Do not treat local preparation or remote blob creation alone as complete delivery. The final verification record must be published through the GitHub plugin before starting the next work item.

The earlier8MiB first-part call returned user cancellation after prolonged pending; its expected blob was checked and was absent(404), with zero confirmed uploads. This completed/cancelled call is not treated as a successful write or a safety refusal. The approved same canonical raw-byte representation now uses128parts of768KiB or less. Upload progress must record each call start and confirmed outcome, and must not silently wait without status.
