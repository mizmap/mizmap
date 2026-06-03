# Vendored .proto files

These come from [DCS-gRPC/rust-server](https://github.com/DCS-gRPC/rust-server).

- **Upstream commit:** `619a7190accceb4a16567329354fcc44f71a5752`
- **Date vendored:** 2026-05-25

To refresh, run `./scripts/regen_protos.sh` after pulling new upstream protos here.

The original tree lives under `protos/dcs/...` upstream; we preserve that layout here as `proto/dcs/...` so the import paths inside the `.proto` files Just Work.

## Known upstream quirks (re-test on a version bump)

- **`GetMagneticDeclination` sign is inverted.** DCS-gRPC 0.8.1 computes declination with its own IGRF model and returns it with the sign **flipped** relative to its own proto contract (which documents positive = easterly). Verified empirically against 8 globally distributed points (both hemispheres, both signs): magnitude correct to a few tenths, sign wrong at every one — e.g. real Las Vegas +11.5°E → `-12.1`, real São Paulo −21.5°W → `+20.7`, real Kandahar +2.9°E → `-2.29` (matching the in-game F10 compass rose "M +2.9"). `mizmap/grpc_client.py:fetch_declination` **negates** the value to compensate; without it the telemetry HUD heading and BRA tool read ~2×declination off the cockpit (~5° in Afghanistan). Upstream [issue #197](https://github.com/DCS-gRPC/rust-server/issues/197) proposes replacing the IGRF impl with DCS's native `magvar.get_mag_decl()` — that may fix the sign and make our negation wrong, so **re-test declination sign after any DCS-gRPC bump** (run `scripts/diag_decl_global.py` against a live mission).
