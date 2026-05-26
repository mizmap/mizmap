#!/usr/bin/env bash
# Regenerate Python gRPC stubs from vendored .proto files.
# Output goes into mizmap/proto_gen/.
set -euo pipefail

cd "$(dirname "$0")/.."

OUT_DIR="mizmap/proto_gen"
PROTO_DIR="proto"

# Clean previous generation, keep the package marker
find "$OUT_DIR" -mindepth 1 ! -name '__init__.py' -delete 2>/dev/null || true

# Collect all .proto files
mapfile -t PROTO_FILES < <(find "$PROTO_DIR" -name '*.proto' | sort)

if [ "${#PROTO_FILES[@]}" -eq 0 ]; then
    echo "No .proto files found under $PROTO_DIR" >&2
    exit 1
fi

echo "Generating stubs for ${#PROTO_FILES[@]} proto files..."

python -m grpc_tools.protoc \
    --proto_path="$PROTO_DIR" \
    --python_out="$OUT_DIR" \
    --grpc_python_out="$OUT_DIR" \
    --pyi_out="$OUT_DIR" \
    "${PROTO_FILES[@]}"

# grpc_tools emits files using absolute import paths (e.g. `from dcs.common.v0 import ...`).
# Make those imports work by ensuring every generated subdirectory has an __init__.py.
find "$OUT_DIR" -type d -exec touch {}/__init__.py \;

echo "Done. Stubs in $OUT_DIR."
