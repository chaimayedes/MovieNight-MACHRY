#!/bin/sh
set -e
python -m grpc_tools.protoc -I/proto --python_out=/app --grpc_python_out=/app \
    /proto/business_logic.proto
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
