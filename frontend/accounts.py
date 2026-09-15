from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from python_service import python_service, User, UserProfile


@dataclass(frozen=True, slots=True)
class Account:
    id: int
    email: str
    username: str
    password: str


@dataclass(frozen=True, slots=True)
class AuthResult:
    ok: bool
    username: str
    password: str
    token: str


@dataclass(frozen=True, slots=True)
class LoginResult:
    ok: bool
    username: str
    password: str
    token: str
