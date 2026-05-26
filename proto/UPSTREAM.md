# Vendored .proto files

These come from [DCS-gRPC/rust-server](https://github.com/DCS-gRPC/rust-server).

- **Upstream commit:** `619a7190accceb4a16567329354fcc44f71a5752`
- **Date vendored:** 2026-05-25

To refresh, run `./scripts/regen_protos.sh` after pulling new upstream protos here.

The original tree lives under `protos/dcs/...` upstream; we preserve that layout here as `proto/dcs/...` so the import paths inside the `.proto` files Just Work.
