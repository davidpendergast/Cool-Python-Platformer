import server
import threading
import random

_LOCK = threading.Lock()

_PLAYER_ID = None
_ACTOR = None
_GAME = None
_THREAD = None

_GHOSTS = []
_GHOSTS_READY = False


def __process():
    running = True
    while running:
        try:
            _LOCK.acquire()
            if _PLAYER_ID is not None:
                _LOCK.release()
                temp_ghosts = server.send(
                    _PLAYER_ID,
                    _GAME.level_num,
                    _ACTOR.rect.topleft)
                _LOCK.acquire()
                _GHOSTS = temp_ghosts
                _GHOSTS_READY = True
            else:
                running = False
        finally:
            _LOCK.release()


def connect(actor, game):
    try:
        _LOCK.acquire()
        _ACTOR = actor
        _GAME = game
        _PLAYER_ID = server.connect()
        _THREAD = threading.Thread(target=__process)
        _THREAD.run()
    except:
        _ACTOR = None
        _PLAYER_ID = None
        _GAME = None
    finally:
        _LOCK.release()


def disconnect():
    try:
        _LOCK.acquire()
        server.disconnect(_PLAYER_ID)
        _PLAYER_ID = None
        _GAME = None
        _ACTOR = None
        _THREAD = None
    finally:
        _LOCK.release()


def get_ghosts():
    r = []
    try:
        _LOCK.acquire()
        if _GHOSTS_READY:
            r = _GHOSTS
            _GHOSTS = []
            _GHOSTS_READY = False
    finally:
        _LOCK.release()
    return r
