import os
import time

import grpc

import session_pb2 as pb  # trae las clases de los mensajes (LoginRequest, etc.).
import session_pb2_grpc as rpc  #  trae los stubs del cliente

TARGET = os.environ.get("SERVER", "localhost:50051")  #


def main():
    channel = grpc.insecure_channel(TARGET)  # conexion entre stub y skeleton?

    # objetos que convierten una llamada normal de Python, como sessions.Login(...), en una petición por la red. Hay uno por cada service del .proto

    users = rpc.UserServiceStub(channel)

    sessions = rpc.SessionServiceStub(channel)

    # create user
    username = f"test_{int(time.time())}"  # secs desde 1970
    user = users.CreateUser(
        pb.CreateUserRequest(
            username=username, password="secreto123", display_name="Usuario de prueba"
        )
    )
    print("1. CreateUser OK:", user.id, user.username)

    # login
    login = sessions.Login(pb.LoginRequest(username=username, password="secreto123"))
    print("2. Login OK, token:", login.token[:10] + "...", "expira:", login.expires_at)

    # validate session y logout
    valid = sessions.ValidateSession(pb.ValidateSessionRequest(token=login.token))
    print("3. ValidateSession OK:", valid.user.username)

    out = sessions.Logout(pb.LogoutRequest(token=login.token))
    print("4. Logout OK:", out.ok)

    try:
        sessions.ValidateSession(pb.ValidateSessionRequest(token=login.token))
        print("ERROR: el token sigue valido despues del logout")
    except grpc.RpcError as e:
        print("5. Token rechazado tras logout:", e.code().name)


if __name__ == "__main__":
    main()
