# Configuration Variants

## Simple Keys
- `default`
- `beta`
- `authenticated`
- `verified`
- `creator`
- `curator`
- `banned`
- `nsfw`
- `owner`

## Operator-Based Keys (with `=`)
- `os=ios`, `os=android`, `os=linux`, `os=web`
- `os_version=android-8`, `os_version=ios-12`, `os_version=ios-13`, `os_version=ios-14`, `os_version=ios-17.1-above`
- `country=tw`, `country=jp`, `country=cn`, `country=hk`, `country=sg`, `country=my`, `country=vn`, `country=th`, `country=ph`, `country=id`, `country=in`, `country=kr`, `country=au`, `country=nz`, `country=ca`, `country=us`, `country=gb`, etc.
- `country-group=europe`, `country-group=east-asia`, `country-group=south-east-asia`, `country-group=north-america`, etc.
- `language=zh-hant`, `language=zh`, `language=ja`, `language=vi`, `language=th`, `language=ko`, `language=en`
- `currency=twd`, `currency=usd`, etc.
- `flavor=city.cafe.browser`, `flavor=girl.missav.com`, `flavor=food.ramen.miso`, `flavor=8maple.im`, `flavor=todau.club`, etc.
- `utm_campaign=telegram_01`, `utm_campaign=configtest`, `utm_campaign=feed_test`, etc.
- `utm_source=telegram`
- `utm_medium=affiliate`, `utm_medium=non-rtb`
- `utm_content=test_battle_pass`, `utm_content=domain_cn`, `utm_content=fetnet_1001`, etc.
- `utm_term=nf`, `utm_term=ss_test`
- `ab=api_prefix-a`, `ab=livestream_sorting-a`, `ab=karaoke_hint-a`, etc.
- `cohort=4631709`, `cohort=5897245`, `cohort=user_created__7d`, `cohort=user_created__1d__sg`, etc.
- `browser=web`
- `pusher-app=550591`, `pusher-app=1166635`
- `forced-update=android-com-swaglive-swag`, `forced-update=ios-com-swaglive-swag`, etc.
- `suggested-update=android-com-swaglive-swag`, `suggested-update=ios-soft-app-live`, etc.

## Compound Keys

### Hyphen separator (`-`)
```
utm-campaign-telegram-01-utm-content-20230206-utm-medium-non-rtb
```

### Ampersand separator (`&`)
```
my_routine&utm_medium=non-rtb&utm_source=cheongdb2u
```

### Semicolon separator (`;`)
```
swag.live;webview
utm-campaign-telegram-01;utm-content-20230206;utm-medium-non-rtb
```
