# OpenChemLab

OpenChemLab is a monorepo for browser-based chemistry tools aimed at students, teachers, and researchers who should not be blocked by operating system limits or expensive vendor software.

The goal is simple: make practical chemistry software available from the browser.

## Current Components

### LCMS Spectrogram

Path: [`lcms-spectrogram/`](lcms-spectrogram/)

LCMS Spectrogram is the first application in this repository. It provides:

- `.mzML` upload support
- optional Thermo `.raw` conversion through a separately installed ThermoRawFileParser
- TIC, XIC, spectrum, and LC-MS map visualizations
- small chemistry helpers for charge-state `m/z`, isotope spacing, and ppm error
- an OpenChemLab landing page at `/` with the LC-MS workspace at `/lcms`

Project-specific setup and deployment instructions live in [lcms-spectrogram/README.md](lcms-spectrogram/README.md).

## Repository Structure

```text
OpenChemLab/
├── README.md
├── LICENSE
└── lcms-spectrogram/
    ├── backend/
    ├── frontend/
    ├── Dockerfile
    ├── docker-compose.yml
    └── README.md
```

As more tools are added, each component can keep its own runtime, tests, and deployment instructions while the root repository remains the shared home.

## Docker Strategy

For the current repository shape, the app-level Docker setup is the right choice.

Why:

- only one deployable application exists today
- `lcms-spectrogram` can already be built and run independently
- keeping Docker next to the app makes the component easier to move, test, and document

Recommended approach going forward:

1. Keep a `Dockerfile` inside each deployable component.
2. Keep component-specific `docker-compose.yml` files while apps are still independent.
3. Add a root-level `compose.yaml` later only when you actually need shared orchestration.

Examples of when a root-level Docker setup becomes worth it:

- you add a shared reverse proxy for several apps
- you add a shared database, queue, auth service, or storage layer
- you want one command to bring up multiple OpenChemLab components together

Until then, changing the current Docker setup to something more general would mostly add abstraction without giving you much benefit.

## Development

Clone the monorepo:

```bash
git clone <your-openchemlab-repo-url>
cd OpenChemLab
```

Then move into the component you want to work on. For example:

```bash
cd lcms-spectrogram
```

## Licensing

This repository includes a root [LICENSE](LICENSE).

Important note for `lcms-spectrogram`:

- the repository itself is licensed at the root
- optional Thermo RAW conversion depends on ThermoRawFileParser and Thermo RawFileReader terms
- that third-party conversion stack has additional conditions beyond the root project license

See [lcms-spectrogram/THIRD_PARTY_NOTICES.md](lcms-spectrogram/THIRD_PARTY_NOTICES.md) for the Thermo-specific notes.

## Roadmap Direction

If OpenChemLab grows into several tools, a good next structure would be:

```text
OpenChemLab/
├── apps/
│   ├── lcms-spectrogram/
│   ├── another-tool/
│   └── ...
├── infra/
│   ├── compose/
│   ├── nginx/
│   └── scripts/
└── README.md
```
