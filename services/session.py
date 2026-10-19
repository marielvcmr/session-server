import secrets

import bcrypt
import grpc

import session_pb2 as pb
import session_pb2_grpc as rpc
from config import SESSION_MINUTES
from dbComponent.dbComponent import dbConnection
from services.mappers import to_user


class SessionService(rpc.SessionServiceServicer):

    def Login(self, request, context):
        with dbConnection() as conn:
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
        with dbConnection() as conn:
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
        with dbConnection() as conn:
            conn.execute("DELETE FROM sessions WHERE token = %s", (request.token,))
        print("[Logout]")
        return pb.LogoutResponse(ok=True)
