# simplemacruvpn

Обёртка для **SOCKS через mihomo** (macOS, Homebrew): узлы по стране, подписки, справка `vpn help`.

## Состав

```
simplemacruvpn/
├── bin/vpn             # главный скрипт (bash)
├── lib/vpn_subs_cmd.py # команды vpn subs (Python 3 stdlib)
├── README.md
└── LICENSE
```

## Установка вручную

```bash
cd simplemacruvpn
chmod +x bin/vpn lib/vpn_subs_cmd.py
sudo ln -sf "$PWD/bin/vpn" /usr/local/bin/vpn   # или другой каталог из PATH
```

По умолчанию **`VPN_SUBS_CMD`** указывает на **`$VPN_PROJECT_ROOT/lib/vpn_subs_cmd.py`** (корень = родитель каталога `bin/`).

Состояние и подписки: `~/.local/state/vpn/` (файл `subscriptions.txt`), если не переопределить `VPN_SUBSCRIPTIONS_FILE`.

## Команды

```bash
vpn help
```

## Что понадобится на машине

- [mihomo](https://formulae.brew.sh/formula/mihomo) (`brew install mihomo`), конфиг в `MIHOMO_DIR` (по умолчанию `/usr/local/etc/mihomo`).
- `/usr/bin/python3` или задайте `VPN_PY`.

## GitHub и Homebrew

Репозиторий: **simplemacruvpn**. Дальше — отдельный Homebrew tap / formula.

## Лицензия

MIT.
