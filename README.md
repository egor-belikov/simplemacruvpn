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

## Homebrew

```bash
brew tap egor-belikov/simplemacruvpn https://github.com/egor-belikov/simplemacruvpn
brew install simplemacruvpn
```

Если `brew install` жалуется, что файл **`/usr/local/bin/vpn`** уже есть (старый ручной симлинк), удалите его или переустановите ссылку: **`brew unlink simplemacruvpn`** / **`brew link --overwrite simplemacruvpn`**.

У стабильной установке в формуле зафиксированы Git-тег **`v1.3.8`** и **`revision`** (хеш коммита этого тега).

Подробнее: `vpn help` после установки.

## Что понадобится на машине

- [mihomo](https://formulae.brew.sh/formula/mihomo) (`brew install mihomo`), конфиг в `MIHOMO_DIR`. Если переменная не задана, берётся `/opt/homebrew/etc/mihomo`, когда он существует, иначе `/usr/local/etc/mihomo` (см. `bin/vpn`).
- `/usr/bin/python3` или задайте `VPN_PY`.

## Репозиторий

- <https://github.com/egor-belikov/simplemacruvpn>

```bash
git clone https://github.com/egor-belikov/simplemacruvpn.git
cd simplemacruvpn
```

## Homebrew

Позже — отдельный tap / formula.

## Лицензия

MIT.
