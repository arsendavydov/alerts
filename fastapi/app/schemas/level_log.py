from enum import Enum


class LevelLog(int, Enum):
    debug = 10
    info = 20
    warning = 30
    error = 40
    critical = 50
    notset = 0
