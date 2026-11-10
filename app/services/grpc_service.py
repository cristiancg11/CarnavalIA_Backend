"""High-performance gRPC service implementation for Carnival GIS and real-time telemetry streaming."""
from concurrent import futures
import logging
from typing import Optional
import grpc

from app.grpc_gen import carnival_gis_pb2, carnival_gis_pb2_grpc
from app.services.oop import (
    BaseGISService,
    HaversineGISService,
    POIManager,
    TelemetryStreamer,
)

logger = logging.getLogger(__name__)


class CarnivalGISServicer(carnival_gis_pb2_grpc.CarnivalGISServicer):
    """Implementation of the CarnivalGIS gRPC protocol buffer service.

    Utilizes Object-Oriented Dependency Injection to delegate domain calculations
    to POIManager and TelemetryStreamer.
    """

    def __init__(
        self,
        poi_manager: Optional[POIManager] = None,
        telemetry_streamer: Optional[TelemetryStreamer] = None,
        gis_service: Optional[BaseGISService] = None
    ) -> None:
        """Initialize servicer with injected domain managers or default implementations.

        Args:
            poi_manager: Injected manager for point of interest spatial queries.
            telemetry_streamer: Injected streamer for sequential route telemetry.
            gis_service: Injected base GIS service.
        """
        self._gis_service = gis_service or HaversineGISService()
        self._poi_manager = poi_manager or POIManager(self._gis_service)
        self._telemetry_streamer = telemetry_streamer or TelemetryStreamer(self._gis_service)

    @property
    def poi_manager(self) -> POIManager:
        """Injected POIManager instance."""
        return self._poi_manager

    @property
    def telemetry_streamer(self) -> TelemetryStreamer:
        """Injected TelemetryStreamer instance."""
        return self._telemetry_streamer

    def GetNearestPOIs(
        self,
        request: carnival_gis_pb2.GeoRequest,
        context: grpc.ServicerContext
    ) -> carnival_gis_pb2.POIResponse:
        """Unary RPC: Calculate Haversine proximity and return sorted points of interest.

        Args:
            request: GeoRequest with user latitude, longitude, optional category, and limit.
            context: gRPC execution context.

        Returns:
            POIResponse containing repeated POIs, closest POI, and count.
        """
        user_lat = request.latitude if request.latitude != 0.0 else 1.2148
        user_lng = request.longitude if request.longitude != 0.0 else -77.2780
        category = request.category if request.category else None
        limit = request.limit if request.limit > 0 else 10

        nearest_records = self._poi_manager.find_nearest_pois(
            user_lat=user_lat,
            user_lng=user_lng,
            category=category,
            limit=limit
        )

        poi_proto_list = []
        for rec in nearest_records:
            coords = rec.get("coordinates", [0.0, 0.0])
            poi_proto_list.append(
                carnival_gis_pb2.POI(
                    name=rec.get("name", ""),
                    category=rec.get("category", ""),
                    latitude=coords[0],
                    longitude=coords[1],
                    address=rec.get("address", ""),
                    description=rec.get("description", ""),
                    distance_meters=rec.get("distance_meters", 0.0),
                    proximity_label=rec.get("proximity_label", ""),
                )
            )

        closest_proto = poi_proto_list[0] if poi_proto_list else None

        return carnival_gis_pb2.POIResponse(
            pois=poi_proto_list,
            closest_poi=closest_proto,
            total_found=len(poi_proto_list),
            user_location=f"[{user_lat}, {user_lng}]",
        )

    def StreamTelemetry(
        self,
        request: carnival_gis_pb2.Empty,
        context: grpc.ServicerContext
    ):
        """Server-streaming RPC: Stream sequential Senda del Carnaval waypoints.

        Args:
            request: Empty parameter request.
            context: gRPC execution context.

        Yields:
            TelemetryPoint messages representing the parade route progression.
        """
        for pt in self._telemetry_streamer.stream_telemetry():
            # Abort if client cancelled connection
            if not context.is_active():
                break
            yield carnival_gis_pb2.TelemetryPoint(
                sequence_index=pt["sequence_index"],
                latitude=pt["latitude"],
                longitude=pt["longitude"],
                landmark_name=pt["landmark_name"],
                street_reference=pt["street_reference"],
                timestamp=pt["timestamp"],
            )


def create_grpc_server(
    port: int = 50051,
    max_workers: int = 10,
    servicer: Optional[CarnivalGISServicer] = None
) -> grpc.Server:
    """Factory creating and configuring a gRPC Server instance with HTTP/2 binary transport.

    Args:
        port: Listening TCP port for the gRPC server.
        max_workers: Thread pool capacity for incoming RPC requests.
        servicer: Optional custom CarnivalGISServicer instance.

    Returns:
        Configured and bound grpc.Server instance ready for start().
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    active_servicer = servicer or CarnivalGISServicer()
    carnival_gis_pb2_grpc.add_CarnivalGISServicer_to_server(active_servicer, server)
    server.add_insecure_port(f"[::]:{port}")
    logger.info(f"[gRPC] CarnivalGIS server configured and bound to port {port}")
    return server


def serve(port: int = 50051) -> None:
    """Start standalone gRPC server loop."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    server = create_grpc_server(port=port)
    server.start()
    print(f"[gRPC] CarnivalGIS Server running on [::]:{port} (HTTP/2 binary protocol)...")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("[gRPC] Stopping CarnivalGIS server...")
        server.stop(0)


if __name__ == "__main__":
    serve()

