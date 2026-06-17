#!/bin/sh
set -e
python -m grpc_tools.protoc -I/proto --python_out=/app --grpc_python_out=/app \
    /proto/api_consumer.proto \
    /proto/datastore.proto \
    /proto/business_logic.proto
exec python main.py
