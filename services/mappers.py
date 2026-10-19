import session_pb2 as pb


def to_user(row):
    """Convierte una fila de la tabla users en el mensaje User del .proto."""
    return pb.User(
        id=row["id"], username=row["username"], display_name=row["display_name"]
    )
