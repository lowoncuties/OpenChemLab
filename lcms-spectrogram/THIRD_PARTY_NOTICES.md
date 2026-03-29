# Third-Party Notices

## ThermoRawFileParser

- Upstream project: <https://github.com/compomics/ThermoRawFileParser>
- Source license: Apache License 2.0
- Upstream source includes an additional Thermo RawFileReader license file used by the RAW conversion stack

## Thermo RawFileReader obligations relevant to this project

The upstream `THERMO_LICENSE` states that distributors must, among other things:

- display this notice in the software's About box:
  `RawFileReader reading tool. Copyright © 2016 by Thermo Fisher Scientific, Inc. All rights reserved.`
- require end users not to redistribute the software further
- avoid commercial exploitation without prior written consent from Thermo Fisher
- avoid combinations that would impose GPL-style redistribution terms on the Thermo software

Because of those conditions, Thermo-based RAW conversion is kept as an optional external install instead of bundled repository content.

## Scientific citation

If you use ThermoRawFileParser in a publication, the upstream project asks you to cite:

Hulstaert N, Shofstahl J, Sachsenberg T, Walzer M, Barsnes H, Martens L, Perez-Riverol Y. *ThermoRawFileParser: Modular, Scalable, and Cross-Platform RAW File Conversion*. Journal of Proteome Research. 2020;19(1):537-542. DOI: `10.1021/acs.jproteome.9b00328`. PMID: `31755270`.

## Practical interpretation

This is not legal advice.

- Hosting the web app for students is different from redistributing a Docker image or desktop binary to them.
- If you plan to redistribute binaries, Docker images, or a commercial hosted product with Thermo RAW conversion enabled, review the Thermo terms carefully with your institution or legal team.
- If you want the least restrictive deployment path, keep the default Docker target and support `.mzML` uploads plus the built-in demo dataset.
