#!/usr/bin/env sh

python -m nuitka \
  --standalone \
  --follow-imports \
  --output-dir=.build \
  --include-module=colorlog \
  --include-data-files=src/app_icon.png=. \
  --output-filename=loradio \
  --include-module=kivymd.icon_definitions \
  --include-module=kivy.core.clipboard.clipboard_xclip \
  --include-module=kivy.core.clipboard.clipboard_xsel \
  --include-module=kivy.core.clipboard.clipboard_dbusklipper \
  --include-module=kivy.core.clipboard.clipboard_gtk3 \
  --include-module=kivy.core.clipboard.clipboard_sdl2 \
  --include-module=kivy.core.clipboard.clipboard_dummy \
  src/main.py
