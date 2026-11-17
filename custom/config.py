from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


CUSTOMIZATION_FILE_PATH = Path("data/customization.json")
CUSTOMIZATION_DB_KEY = "custom_bot_config"


class MediaType(str, Enum):
    NONE = "none"
    PHOTO = "photo"
    VIDEO = "video"
    GIF = "gif"


class ButtonTargetType(str, Enum):
    BUILTIN = "builtin"
    PAGE = "page"
    URL = "url"
    WEBAPP = "webapp"


class StartScenario(str, Enum):
    DEFAULT = "default"
    FIRST_START_TUTORIAL = "first_start_tutorial"
    ALWAYS_TWO_MESSAGES = "always_two_messages"


@dataclass
class ButtonConfig:
    id: str
    is_builtin: bool = False
    target_type: ButtonTargetType = ButtonTargetType.BUILTIN
    target_value: str = ""
    text: dict[str, str] = field(default_factory=dict)
    emoji: str = ""
    enabled: bool = True
    row: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "is_builtin": self.is_builtin,
            "target_type": self.target_type.value if isinstance(self.target_type, Enum) else self.target_type,
            "target_value": self.target_value,
            "text": dict(self.text),
            "emoji": self.emoji,
            "enabled": self.enabled,
            "row": self.row,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ButtonConfig:
        target_type = data.get("target_type", ButtonTargetType.BUILTIN)
        if isinstance(target_type, str):
            try:
                target_type = ButtonTargetType(target_type)
            except ValueError:
                target_type = ButtonTargetType.BUILTIN
        return cls(
            id=data.get("id", ""),
            is_builtin=data.get("is_builtin", False),
            target_type=target_type,
            target_value=data.get("target_value", ""),
            text=dict(data.get("text", {})),
            emoji=data.get("emoji", ""),
            enabled=data.get("enabled", True),
            row=data.get("row", 0),
        )


@dataclass
class PageConfig:
    id: str
    title: str = ""
    media_type: MediaType = MediaType.NONE
    media_url: str = ""
    text: dict[str, str] = field(default_factory=dict)
    buttons: list[ButtonConfig] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "media_type": self.media_type.value if isinstance(self.media_type, Enum) else self.media_type,
            "media_url": self.media_url,
            "text": dict(self.text),
            "buttons": [b.to_dict() for b in self.buttons],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PageConfig:
        media_type = data.get("media_type", MediaType.NONE)
        if isinstance(media_type, str):
            try:
                media_type = MediaType(media_type)
            except ValueError:
                media_type = MediaType.NONE
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            media_type=media_type,
            media_url=data.get("media_url", ""),
            text=dict(data.get("text", {})),
            buttons=[ButtonConfig.from_dict(b) for b in data.get("buttons", [])],
        )


@dataclass
class NotificationConfig:
    enabled: bool = True
    text: dict[str, str] = field(default_factory=dict)
    media_type: MediaType = MediaType.NONE
    media_url: str = ""
    buttons: list[ButtonConfig] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "text": dict(self.text),
            "media_type": self.media_type.value if isinstance(self.media_type, Enum) else self.media_type,
            "media_url": self.media_url,
            "buttons": [b.to_dict() for b in self.buttons],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NotificationConfig:
        media_type = data.get("media_type", MediaType.NONE)
        if isinstance(media_type, str):
            try:
                media_type = MediaType(media_type)
            except ValueError:
                media_type = MediaType.NONE
        return cls(
            enabled=data.get("enabled", True),
            text=dict(data.get("text", {})),
            media_type=media_type,
            media_url=data.get("media_url", ""),
            buttons=[ButtonConfig.from_dict(b) for b in data.get("buttons", [])],
        )


@dataclass
class StartFlowMessage:
    text: dict[str, str] = field(default_factory=dict)
    media_type: MediaType = MediaType.NONE
    media_url: str = ""
    buttons: list[ButtonConfig] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": dict(self.text),
            "media_type": self.media_type.value if isinstance(self.media_type, Enum) else self.media_type,
            "media_url": self.media_url,
            "buttons": [b.to_dict() for b in self.buttons],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StartFlowMessage:
        media_type = data.get("media_type", MediaType.NONE)
        if isinstance(media_type, str):
            try:
                media_type = MediaType(media_type)
            except ValueError:
                media_type = MediaType.NONE
        return cls(
            text=dict(data.get("text", {})),
            media_type=media_type,
            media_url=data.get("media_url", ""),
            buttons=[ButtonConfig.from_dict(b) for b in data.get("buttons", [])],
        )


@dataclass
class StartFlowConfig:
    scenario: StartScenario = StartScenario.DEFAULT
    first_message: StartFlowMessage = field(default_factory=StartFlowMessage)
    second_message: StartFlowMessage = field(default_factory=StartFlowMessage)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario.value if isinstance(self.scenario, Enum) else self.scenario,
            "first_message": self.first_message.to_dict(),
            "second_message": self.second_message.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StartFlowConfig:
        scenario = data.get("scenario", StartScenario.DEFAULT)
        if isinstance(scenario, str):
            try:
                scenario = StartScenario(scenario)
            except ValueError:
                scenario = StartScenario.DEFAULT
        return cls(
            scenario=scenario,
            first_message=StartFlowMessage.from_dict(data.get("first_message", {})),
            second_message=StartFlowMessage.from_dict(data.get("second_message", {})),
        )


def _get_default_pages() -> dict[str, PageConfig]:
    main_page = PageConfig(
        id="main",
        title="Главная",
        media_type=MediaType.NONE,
        media_url="",
        text={
            "ru": "👋 Привет, {user_name}!\n\nДобро пожаловать в бота VPN сервиса.\n{subscription_status}",
            "en": "👋 Hello, {user_name}!\n\nWelcome to our VPN service bot.\n{subscription_status}",
        },
        buttons=[
            ButtonConfig(
                id="connect",
                is_builtin=True,
                target_type=ButtonTargetType.BUILTIN,
                target_value="connect",
                text={"ru": "🔗 Подключиться", "en": "🔗 Connect"},
                enabled=True,
                row=0,
            ),
            ButtonConfig(
                id="subscription",
                is_builtin=True,
                target_type=ButtonTargetType.PAGE,
                target_value="subscription",
                text={"ru": "💎 Подписка", "en": "💎 Subscription"},
                enabled=True,
                row=1,
            ),
            ButtonConfig(
                id="balance",
                is_builtin=True,
                target_type=ButtonTargetType.BUILTIN,
                target_value="balance",
                text={"ru": "💰 Баланс", "en": "💰 Balance"},
                enabled=True,
                row=1,
            ),
            ButtonConfig(
                id="support",
                is_builtin=True,
                target_type=ButtonTargetType.BUILTIN,
                target_value="support",
                text={"ru": "💬 Поддержка", "en": "💬 Support"},
                enabled=True,
                row=2,
            ),
        ],
    )

    subscription_page = PageConfig(
        id="subscription",
        title="Подписка",
        media_type=MediaType.NONE,
        media_url="",
        text={
            "ru": "📦 Управление подпиской\n\nВыберите нужный тариф или продлите активную подписку:",
            "en": "📦 Subscription management\n\nChoose a plan or renew your active subscription:",
        },
        buttons=[
            ButtonConfig(
                id="buy_sub",
                is_builtin=True,
                target_type=ButtonTargetType.BUILTIN,
                target_value="buy_subscription",
                text={"ru": "⚡ Купить подписку", "en": "⚡ Buy subscription"},
                enabled=True,
                row=0,
            ),
            ButtonConfig(
                id="back_to_main",
                is_builtin=True,
                target_type=ButtonTargetType.PAGE,
                target_value="main",
                text={"ru": "◀️ Назад в меню", "en": "◀️ Back to menu"},
                enabled=True,
                row=1,
            ),
        ],
    )

    return {"main": main_page, "subscription": subscription_page}


def _get_default_notifications() -> dict[str, NotificationConfig]:
    return {
        "subscription_expiring": NotificationConfig(
            enabled=True,
            text={
                "ru": "⏳ {user_name}, ваша подписка истекает через {days_left} дн.!\n\nПополните баланс или продлите её заранее, чтобы оставаться на связи.",
                "en": "⏳ {user_name}, your subscription expires in {days_left} days!\n\nPlease renew to stay connected.",
            },
            media_type=MediaType.NONE,
            buttons=[
                ButtonConfig(
                    id="renew_sub",
                    is_builtin=False,
                    target_type=ButtonTargetType.PAGE,
                    target_value="subscription",
                    text={"ru": "🔄 Продлить подписку", "en": "🔄 Renew subscription"},
                    enabled=True,
                )
            ],
        ),
        "webhook_device_added": NotificationConfig(
            enabled=True,
            text={
                "ru": "📱 К вашей подписке подключено новое устройство: {device_name}",
                "en": "📱 A new device was added to your subscription: {device_name}",
            },
            media_type=MediaType.NONE,
        ),
    }


@dataclass
class CustomizationConfig:
    enabled: bool = False
    needs_restart: bool = False
    realtime_mode: bool = False
    default_language: str = "ru"
    auto_detect_language: bool = True
    start_flow: StartFlowConfig = field(default_factory=StartFlowConfig)
    pages: dict[str, PageConfig] = field(default_factory=_get_default_pages)
    notifications: dict[str, NotificationConfig] = field(default_factory=_get_default_notifications)
    emoji_packs: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "needs_restart": self.needs_restart,
            "realtime_mode": self.realtime_mode,
            "default_language": self.default_language,
            "auto_detect_language": self.auto_detect_language,
            "start_flow": self.start_flow.to_dict(),
            "pages": {k: v.to_dict() for k, v in self.pages.items()},
            "notifications": {k: v.to_dict() for k, v in self.notifications.items()},
            "emoji_packs": list(self.emoji_packs),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CustomizationConfig:
        pages_raw = data.get("pages")
        pages = {k: PageConfig.from_dict(v) for k, v in pages_raw.items()} if pages_raw else _get_default_pages()

        notifs_raw = data.get("notifications")
        notifications = (
            {k: NotificationConfig.from_dict(v) for k, v in notifs_raw.items()}
            if notifs_raw
            else _get_default_notifications()
        )

        start_flow_raw = data.get("start_flow")
        start_flow = StartFlowConfig.from_dict(start_flow_raw) if start_flow_raw else StartFlowConfig()

        return cls(
            enabled=data.get("enabled", False),
            needs_restart=data.get("needs_restart", False),
            realtime_mode=data.get("realtime_mode", False),
            default_language=data.get("default_language", "ru"),
            auto_detect_language=data.get("auto_detect_language", True),
            start_flow=start_flow,
            pages=pages,
            notifications=notifications,
            emoji_packs=list(data.get("emoji_packs", [])),
        )

    @classmethod
    def from_json(cls, json_str: str) -> CustomizationConfig:
        data = json.loads(json_str)
        return cls.from_dict(data)
