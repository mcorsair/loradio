from enum import Enum


class LowerEnum(Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()


class ExtraEnum(Enum):
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        # чтобы device.value возвращал одно str значение, а не весь кортеж атрибутов
        obj._value_ = args[0]
        return obj
