import server
import threading
import random
import colorsys
import phys_objects

_LOCK = threading.Lock()

_PLAYER_ID = None
_ACTOR = None
_GAME = None
_THREAD = None

_GHOSTS = []


def __process():
    global _GHOSTS
    running = True
    while running:
        try:
            _LOCK.acquire()
            if _PLAYER_ID is not None:
                _LOCK.release()
                temp_ghosts = []
                for ghast in server.send(
                        _PLAYER_ID,
                        _GAME.level_num,
                        _ACTOR.rect.topleft):
                    temp_ghosts.append(phys_objects.Ghost(
                        ghast['position'],
                        color=get_ghost_color(ghast['user'])))
                _LOCK.acquire()
                _GHOSTS = temp_ghosts
            else:
                running = False
        finally:
            _LOCK.release()
    print("client thread stopping!")


def connect(actor, game):
    global _ACTOR, _GAME, _PLAYER_ID, _THREAD
    try:
        _LOCK.acquire()
        _ACTOR = actor
        _GAME = game
        _PLAYER_ID = server.connect()
        _THREAD = threading.Thread(target=__process)
        _THREAD.start()
        actor.color = get_ghost_color(_PLAYER_ID)
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
        if _PLAYER_ID is not None:
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
        r = list(_GHOSTS)
    finally:
        _LOCK.release()
    return r


def get_ghost_color(i):
    state = random.getstate()
    random.seed(i)
    color = colorsys.hsv_to_rgb(random.random(), 1.0, 1.0)
    random.setstate(state)
    return tuple([x * 255 for x in color])
