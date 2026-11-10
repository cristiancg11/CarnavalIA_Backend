"""Client invocation test demonstrating binary RPC communication over HTTP/2 for CarnavalGIS."""
import os
import sys
import time

# Ensure project root is in Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc
from app.grpc_gen import carnival_gis_pb2, carnival_gis_pb2_grpc
from app.services.grpc_service import create_grpc_server


def run_grpc_client_test(port: int = 50052):
    """Start local gRPC test server, execute Unary and Streaming RPC calls, and verify responses."""
    print("=" * 70)
    print("CARNAVALIA gRPC CLIENT INVOCATION TEST (HTTP/2 BINARY TRANSPORT)")
    print("=" * 70)

    # 1. Start gRPC server on test port
    print(f"\n[1] Starting gRPC test server on localhost:{port}...")
    server = create_grpc_server(port=port)
    server.start()
    time.sleep(0.5)
    print("    -> Server successfully started and listening for HTTP/2 frames.")

    try:
        # 2. Establish gRPC channel and initialize stub
        print(f"\n[2] Connecting client channel to localhost:{port}...")
        with grpc.insecure_channel(f"localhost:{port}") as channel:
            stub = carnival_gis_pb2_grpc.CarnivalGISStub(channel)

            # -------------------------------------------------------------
            # TEST A: Unary RPC - GetNearestPOIs
            # -------------------------------------------------------------
            print("\n[3] Executing Unary RPC: GetNearestPOIs()...")
            # User near Plaza de Nariño searching for closest bathrooms
            geo_req = carnival_gis_pb2.GeoRequest(
                latitude=1.2148,
                longitude=-77.2780,
                category="bathroom",
                limit=3
            )
            start_time = time.perf_counter()
            response: carnival_gis_pb2.POIResponse = stub.GetNearestPOIs(geo_req)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            print(f"    -> RPC completed in {elapsed_ms:.2f} ms")
            print(f"    -> Total POIs returned: {response.total_found}")
            print(f"    -> Closest POI: {response.closest_poi.name}")
            print(f"    -> Category: {response.closest_poi.category}")
            print(f"    -> Address: {response.closest_poi.address}")
            print(f"    -> Distance: {response.closest_poi.distance_meters} meters ({response.closest_poi.proximity_label})")
            print(f"    -> Coordinates: [{response.closest_poi.latitude}, {response.closest_poi.longitude}]")

            assert response.total_found > 0, "Expected at least 1 POI returned"
            assert response.closest_poi.name != "", "Expected valid closest POI name"
            assert response.closest_poi.distance_meters >= 0.0, "Expected valid positive distance"

            print("\n    All POIs in Unary Response:")
            for idx, p in enumerate(response.pois, 1):
                print(f"      {idx}. {p.name} [{p.category}] - {p.distance_meters:.1f}m ({p.proximity_label}) | {p.address}")

            # -------------------------------------------------------------
            # TEST B: Server Streaming RPC - StreamTelemetry
            # -------------------------------------------------------------
            print("\n[4] Executing Server Streaming RPC: StreamTelemetry()...")
            empty_req = carnival_gis_pb2.Empty()
            start_stream_time = time.perf_counter()

            stream_iterator = stub.StreamTelemetry(empty_req)
            received_points = []

            for point in stream_iterator:
                received_points.append(point)
                print(
                    f"    -> Streamed Frame #{point.sequence_index:02d}: "
                    f"[{point.latitude:.4f}, {point.longitude:.4f}] - {point.landmark_name} ({point.street_reference})"
                )

            stream_elapsed_ms = (time.perf_counter() - start_stream_time) * 1000
            print(f"    -> Stream completed: {len(received_points)} waypoints in {stream_elapsed_ms:.2f} ms")

            assert len(received_points) == 12, f"Expected 12 Senda waypoints, got {len(received_points)}"
            assert received_points[0].sequence_index == 1, "First waypoint index must be 1"
            assert received_points[-1].sequence_index == 12, "Last waypoint index must be 12"

            print("\n" + "=" * 70)
            print("SUCCESS: ALL gRPC RPC TESTS (UNARY & STREAMING) PASSED FLAWLESSLY!")
            print("=" * 70)

    finally:
        # Cleanly stop test server
        server.stop(grace=0)
        print("\n[5] Test server stopped successfully.")


if __name__ == "__main__":
    test_port = int(sys.argv[1]) if len(sys.argv) > 1 else 50052
    run_grpc_client_test(port=test_port)
