"""Standalone launcher for CarnavalIA high-performance gRPC service."""
import os
import sys

# Ensure repository root is on Python module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.grpc_service import serve

if __name__ == "__main__":
    port = int(os.getenv("GRPC_PORT", 50051))
    serve(port=port)

