#!/bin/sh
set -e
python -m grpc_tools.protoc -I/proto --python_out=/app --grpc_python_out=/app \
    /proto/datastore.proto
exec python main.py
