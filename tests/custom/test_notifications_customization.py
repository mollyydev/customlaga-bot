
from custom.config import (
    ButtonConfig,
    ButtonTargetType,
    CustomizationConfig,
    MediaType,
    NotificationConfig,
)
from custom.services.notification_service import format_custom_notification


def test_notification_disabled():
    config = CustomizationConfig(enabled=False)
    res = format_custom_notification(
        config,
        notification_type='subscription_expiring',
        language='ru',
        context={'days_left': 3, 'user_name': 'Ivan'},
    )
    assert res is None


def test_notification_customized():
    config = CustomizationConfig(enabled=True)
    config.notifications['subscription_expiring'] = NotificationConfig(
        enabled=True,
        text={
            'ru': 'Внимание, {user_name}! Подписка истекает через {days_left} дн.',
            'en': 'Warning, {user_name}! Subscription expires in {days_left} days.',
        },
        media_type=MediaType.PHOTO,
        media_url='assets/expiring.jpg',
        buttons=[
            ButtonConfig(
                id='renew_btn',
                is_builtin=False,
                target_type=ButtonTargetType.PAGE,
                target_value='subscription',
                text={'ru': 'Продлить подписку', 'en': 'Renew now'},
                enabled=True,
            )
        ],
    )

    res_ru = format_custom_notification(
        config,
        notification_type='subscription_expiring',
        language='ru',
        context={'days_left': 2, 'user_name': 'Ivan'},
    )
    assert res_ru is not None
    assert 'Внимание, Ivan! Подписка истекает через 2 дн.' in res_ru['text']
    assert res_ru['media_type'] == MediaType.PHOTO
    assert res_ru['media_url'] == 'assets/expiring.jpg'
    assert len(res_ru['buttons']) == 1
    assert res_ru['buttons'][0]['text']['ru'] == 'Продлить подписку'

    # English version
    res_en = format_custom_notification(
        config,
        notification_type='subscription_expiring',
        language='en',
        context={'days_left': 2, 'user_name': 'Ivan'},
    )
    assert 'Warning, Ivan! Subscription expires in 2 days.' in res_en['text']


def test_notification_not_configured_falls_back():
    config = CustomizationConfig(enabled=True)
    # Not configuring 'balance_low'
    res = format_custom_notification(
        config,
        notification_type='balance_low',
        language='ru',
        context={'balance': '100'},
    )
    assert res is None, 'Non-configured notification type should fall back to default'
