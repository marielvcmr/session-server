from concurrent import futures

import grpc

import session_pb2_grpc as rpc
from config import SERVER_HOST, SERVER_PORT
from services.session import SessionService
from services.user import UserService


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rpc.add_UserServiceServicer_to_server(UserService(), server)
    rpc.add_SessionServiceServicer_to_server(SessionService(), server)
    server.add_insecure_port(f"{SERVER_HOST}:{SERVER_PORT}")  # 0.0.0.0 = acepta conexiones de otras máquinas
    server.start()
    print(f"SessionService escuchando en {SERVER_HOST}:{SERVER_PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
