import server
import threading
import random

_LOCK = threading.Lock()

_PLAYER_ID = None
_ACTOR = None
_GAME = None
_THREAD = None

_GHOSTS = []


def __process():
    global _GHOSTS, _GHOSTS_READY
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
            else:
                running = False
        finally:
            _LOCK.release()
    print "client thread stopping!"


def connect(actor, game):
    global _ACTOR, _GAME, _PLAYER_ID, _THREAD
    try:
        _LOCK.acquire()
        _ACTOR = actor
        _GAME = game
        _PLAYER_ID = server.connect()
        _THREAD = threading.Thread(target=__process)
        _THREAD.start()
    except:
        _ACTOR = None
        _PLAYER_ID = None
        _GAME = None
    finally:
        _LOCK.release()


def disconnect():
    global _ACTOR, _GAME, _PLAYER_ID, _THREAD
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
    global _GHOSTS
    r = []
    try:
        _LOCK.acquire()
        r = _GHOSTS
    finally:
        _LOCK.release()
    return r
