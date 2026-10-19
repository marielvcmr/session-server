import os
import secrets
from concurrent import futures

import bcrypt
import grpc
import psycopg
from psycopg.rows import dict_row

import session_pb2 as pb
import session_pb2_grpc as rpc

DB_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/session_service"
)
PORT = os.environ.get("PORT", "50051")
SESSION_MINUTES = 30


def db():
    """Abre una conexión nueva a PostgreSQL (una por llamada, simple y suficiente)."""
    return psycopg.connect(DB_URL, row_factory=dict_row, autocommit=True)


def to_user(row):
    return pb.User(
        id=row["id"], username=row["username"], display_name=row["display_name"]
    )


class UserService(rpc.UserServiceServicer):

    def CreateUser(self, request, context):
        username = request.username.strip().lower()
        display_name = request.display_name.strip()
        if not username or not display_name or len(request.password) < 6:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Usuario, nombre y contraseña (mínimo 6 caracteres) son obligatorios",
            )

        password_hash = bcrypt.hashpw(
            request.password.encode(), bcrypt.gensalt()
        ).decode()
        try:
            with db() as conn:
                row = conn.execute(
                    "INSERT INTO users (username, display_name, password_hash) "
                    "VALUES (%s, %s, %s) RETURNING id, username, display_name",
                    (username, display_name, password_hash),
                ).fetchone()
        except psycopg.errors.UniqueViolation:
            context.abort(
                grpc.StatusCode.ALREADY_EXISTS, f"El usuario '{username}' ya existe"
            )

        print(f"[CreateUser] {username}")
        return to_user(row)


class SessionService(rpc.SessionServiceServicer):

    def Login(self, request, context):
        with db() as conn:
            row = conn.execute(
                "SELECT id, username, display_name, password_hash FROM users WHERE username = %s",
                (request.username.strip().lower(),),
            ).fetchone()
            if row is None or not bcrypt.checkpw(
                request.password.encode(), row["password_hash"].encode()
            ):
                context.abort(
                    grpc.StatusCode.UNAUTHENTICATED, "Usuario o contraseña incorrectos"
                )

            token = secrets.token_urlsafe(32)
            session = conn.execute(
                "INSERT INTO sessions (token, user_id, expires_at) "
                "VALUES (%s, %s, now() + make_interval(mins => %s)) RETURNING expires_at",
                (token, row["id"], SESSION_MINUTES),
            ).fetchone()

        print(f"[Login] {row['username']}")
        return pb.LoginResponse(
            token=token,
            expires_at=int(session["expires_at"].timestamp()),
            user=to_user(row),
        )

    def ValidateSession(self, request, context):
        with db() as conn:
            row = conn.execute(
                "SELECT u.id, u.username, u.display_name, s.expires_at "
                "FROM sessions s JOIN users u ON u.id = s.user_id "
                "WHERE s.token = %s AND s.expires_at > now()",
                (request.token,),
            ).fetchone()
        if row is None:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Sesión inválida o expirada")

        print(f"[ValidateSession] {row['username']}")
        return pb.ValidateSessionResponse(
            user=to_user(row), expires_at=int(row["expires_at"].timestamp())
        )

    def Logout(self, request, context):
        with db() as conn:
            conn.execute("DELETE FROM sessions WHERE token = %s", (request.token,))
        print("[Logout]")
        return pb.LogoutResponse(ok=True)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rpc.add_UserServiceServicer_to_server(UserService(), server)
    rpc.add_SessionServiceServicer_to_server(SessionService(), server)
    server.add_insecure_port(
        f"0.0.0.0:{50051}"
    )  # 0.0.0.0 = acepta conexiones de otras máquinas
    server.start()
    print(f"SessionService escuchando en el puerto {PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
