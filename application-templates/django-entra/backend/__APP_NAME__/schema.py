from typing import List

from ninja import Schema


class UserSchema(Schema):
    username: str
    email: str
    first_name: str
    last_name: str
    roles: List[str]
    is_admin: bool
