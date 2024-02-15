from beanie import Document


class AdminUser(Document):
    id: int  # type: ignore[assignment]

    class Settings:
        name = "admins"
