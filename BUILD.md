# Build and release

## Requirements
- Python 3.10 or later
- No third-party Python packages

## Validate
```bash
python scripts/controlroom.py self-test
python scripts/controlroom.py validate .
```

## Package
```bash
python scripts/controlroom.py package --output dist/controlroom.zip
```

## Release model
- Pull requests target `dev`.
- Merges to `dev` may create `vX.Y.Z-beta.N` prereleases.
- Stable releases are created from `main` through GitHub Actions.
- Versions follow Semantic Versioning.
- Release notes use pull request titles and `changes/*.md` fragments.
- The release archive contains all paths in `MANIFEST.txt`.
