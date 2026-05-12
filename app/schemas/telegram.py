from pydantic import BaseModel, ConfigDict, Field


class TelegramUser(BaseModel):
    id: int
    is_bot: bool = False
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


class TelegramContact(BaseModel):
    phone_number: str
    first_name: str | None = None
    last_name: str | None = None
    user_id: int | None = None


class TelegramVoice(BaseModel):
    file_id: str
    file_unique_id: str | None = None
    duration: int | None = None
    mime_type: str | None = None
    file_size: int | None = None


class TelegramMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message_id: int
    from_user: TelegramUser | None = Field(default=None, alias="from")
    chat: dict
    date: int
    text: str | None = None
    contact: TelegramContact | None = None
    voice: TelegramVoice | None = None


class TelegramCallbackQuery(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    from_user: TelegramUser = Field(alias="from")
    message: TelegramMessage | None = None
    data: str | None = None


class TelegramUpdate(BaseModel):
    update_id: int
    message: TelegramMessage | None = None
    callback_query: TelegramCallbackQuery | None = None
