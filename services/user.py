import bcrypt
import grpc
import psycopg

import session_pb2_grpc as rpc
from dbComponent.dbComponent import dbConnection
from services.mappers import to_user


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
            with dbConnection() as conn:
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
