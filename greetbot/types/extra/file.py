import base64
import io
from functools import lru_cache
from typing import Self, Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema, CoreSchema


class Base64File(str):
    max_size_bytes: int | None = None  # Максимальный размер файла в байтах (None для безлимита)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize,
                info_arg=False,
                return_schema=core_schema.str_schema(),
            ),
        )

    @classmethod
    def _validate(cls, v: str) -> Self:
        try:
            decoded = base64.b64decode(v, validate=True)
            # Проверка размера файла
            if cls.max_size_bytes is not None and len(decoded) > cls.max_size_bytes:
                raise ValueError(f"File size exceeds the maximum limit of {cls.max_size_bytes / 1024} KB")
        except ValueError as e:
            raise ValueError(f"Invalid base64 string or file issue: {e}")
        return cls(v)

    @classmethod
    def _serialize(cls, v: Self) -> str:
        return str(v)

    @lru_cache
    def to_bytes(self) -> bytes:
        return base64.b64decode(self)

    @lru_cache
    def to_bytesio(self) -> io.BytesIO:
        buffer = io.BytesIO(self.to_bytes())
        return buffer

    @classmethod
    def from_bytes(cls, b: bytes) -> Self:
        encoded = base64.b64encode(b).decode()
        return cls(encoded)

