# Equipment reference reconciliation, 2026-09-30

Status: research checkpoint, no equipment geometry promoted. Whole-vehicle gates remain OPEN.

## Variant and revision controls

The retained Tim Roberts walkaround is explicitly indexed as MAZ-543 SCUD-B TEL, with exact 543A identity unestablished. Four contact sheets and originals 171/174 were obtained by normal public Git LFS reads from migration commit `4f28bd4618ca7e272f6049b9f615821b8e0bb8f1`; all six matched their pointer SHA-256 values. The two originals show chassis internals and a crossmember, not an identifiable front-cover hinge. They cannot settle the r2 lid-axis question.

The [1977 technical description](https://djvu.online/file/zjMdLY3MFjmTL), printed pp.203/206/228–229, places the battery box behind the right cab and the ventilation equipment behind the left cab. It specifies four 24 V 12-СТ-70 batteries in parallel, totaling 280 Ah. The existing starting simulation retains 280 Ah; no electrical calibration is claimed.

A later [battery installation catalogue reproduction](https://1sonar.ru/acat/gruzovye_avtomobili/maz/maz_543__7310__1146/ustanovka_akkumulyatornyh_batarej-262.html) identifies box 543-3703002 but lists battery 6СТ-190ТР(ТМ). Its [actual linked assembly drawing](https://1sonar.ru/acat/data/maz/543/37.2.gif), 795×606 pixels, was retrieved and visually inspected. SHA-256: `2dbc806394a47c74de5b1c8c11dd76933866614b814348fec2581d0f58dd9a90`. It shows the enclosing box, separate batteries, retention hardware and ventilation assembly. It has no usable dimensional scale and does not establish original 1977 battery geometry. Do not combine its battery internals with the 1977 electrical description as though they were a single verified configuration.

The current bay is still a fitted enclosure. Name-based absence in the native inventory is insufficient by itself to prove an equipment item is absent. No invented battery/FVU internals have been inserted to fill this gap.

## Access and preservation

Raw third-party drawings remain in the local reference workspace with their watermarks; they have not been republished into the public repository. Autoopt's full catalogue requested CAPTCHA verification; Avtoall redirected to a VPN restriction; direct djvu HTML requested JavaScript/cookies. These checks were not bypassed and no network/security settings were changed. The public web reader could read the manual's OCR. The independent 1sonar catalogue served its own pages and referenced drawing normally.

Next inspection targets are the separately labelled 543/543A ventilation installation and 543A fuel mounting assembly, then reconciliation with retained bare-chassis photographs. Exact dimensions, production-year applicability, complete service motion and assembly clearances remain unverified.

## Additional drawings actually inspected

- [543/543A ventilation installation](https://1sonar.ru/acat/gruzovye_avtomobili/maz/maz_543__7310__1146/ustanovka_fvu_543__543a-21.html), [drawing 80.4](https://1sonar.ru/acat/data/maz/543/80.4.gif), 967×465, SHA-256 `2b34c7d13f2f84d392f2b8fd5dc472927c7428af5c3029ac8154d41462dc3455`: distinct filter, blower, elbow/ducting, brackets and actuation hardware. The later part table names FPT-200B and blower 434.87.003. The general 1977 description is not enough to certify those exact revisions or their dimensions.
- [543A tank installation](https://1sonar.ru/acat/gruzovye_avtomobili/maz/maz_543__7310__1146/ustanovka_toplivnyh_bakov_543a-61.html), [drawing 11.6](https://1sonar.ru/acat/data/maz/543/11.6.gif), 679×564, SHA-256 `1927b27ed5e1d2bbed1ae55bb1a83d5d6d0bd80bee7b6b1efc36030a5e855af0`: paired shaped tanks with a separate base, pads, hold-down members, bands and mounting hardware. Base 543A-1101600-11 is a distinct assembly, not the four dark wraparound bands in the present simplified fuel group.

The 1977 manual p.48 specifically describes the 543A tubular tank frame attached with **three** special brackets to the fender-bracket tie and engine-hood arches. Do not infer four chassis mounts from a two-dimensional exploded view or place supports wherever a simplified tank happens to sit.

Current source `lib/maz543.ts` openly labels the fuel geometry approximate: two rounded boxes and four dark bands, merged into seven native fuel objects. The native inventory locates the tank bodies at X=-0.775…0.895 m, Z=0.760…1.200 m. These are measured current-model coordinates, not original vehicle dimensions. Before modifying this assembly, establish the three actual mounting interfaces and reconcile tank placement with the retained 543A bare-chassis photographs. Merely adding pipes under the current boxes would conceal rather than resolve that installation uncertainty.

## Read-only native installation views

`render-equipment-installation-review.py` opened the current Master by SHA-256 and produced matching exterior and bay-cutaway views. The latter temporarily hides only its recorded bay/crown/access objects; no saved master is modified. The exterior visibly lacks a rear enclosure wall, and the cutaway exposes the sparse existing bay installation. Both show the current low, outboard simplified tanks. The retained `maz543a-5.jpg` rear-left bare-chassis photograph shows a closed, panelled rear enclosure. This establishes an exterior omission, not the hidden equipment dimensions or attachment coordinates. These are native Cycles CPU inspection renders; they are not web screenshots, photo-calibrated views, or visual acceptance.
