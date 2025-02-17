#!/usr/bin/env sh

# делаем текущим каталог с этим стартовым скриптом

DIR=$(dirname "$0")
cd "${DIR}" || exit

# --auto-fullscreen для полноэкранного режима

if [ -f dist/loradio ]; then
  # запуск скомпилированного приложения
  dist/loradio --size=1000x600 -- --device /dev/ttyUSB0
else
  # запуск из исходного кода
  src/main.py --size=1000x600 -- --device /dev/ttyUSB0
fi
