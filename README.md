# README

Передача голоса через последовательные LoRa-устройства серии `LoRa E22-xxxT22U`.

Используется вокодер `codec2`.

Предполагается, что устройства имеют vendor:model id `1a86:7523`

При использовании устройств с другими id 
необходимо поменять константы `DEVICE_VENDOR_ID` и `DEVICE_MODEL_ID` в `main.py`.

`PTT` - передача голоса.

`PTT TEST` - передача тестовых данных для тестирования канала. Каждый "пик" - прием пакета.

Запуск - скриптом `run-loradio.sh`:
```shell
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

./run-loradio.sh
```

`build.sh` - компиляция с помощью `nuitka`.

`dist.sh` - сборка скомпилированного проекта в `zip` архив.
