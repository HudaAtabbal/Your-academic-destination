import os, sys, time, traceback
_d = os.path.dirname(__file__)

_ENABLE_LOG = os.environ.get('WJ_WSGI_LOG', '0') == '1'
def _log(m):
    if _ENABLE_LOG:
        open(os.path.join(_d, 'boot_log.txt'), 'a').write('%.1f %s\n' % (time.time(), m))

sys.path.insert(0, _d)
_asgi = None
try:
    from a2wsgi import ASGIMiddleware
    from main import app
    _log('IMPORT DONE')
except Exception:
    _log('IMPORT ERROR:\n' + traceback.format_exc())
    raise

def application(environ, start_response):
    global _asgi
    # a2wsgi spawns its asyncio loop as a background thread at construction time.
    # Passenger/LiteSpeed fork workers AFTER module import, and threads do not
    # survive fork. Lazy creation ensures the loop thread is born inside the
    # forked worker where it stays alive for every subsequent request.
    if _asgi is None:
        _asgi = ASGIMiddleware(app)
    try:
        r = _asgi(environ, start_response)
        def _gen():
            total = 0
            try:
                for chunk in r:
                    total += len(chunk)
                    yield chunk
                _log('REQ %s 200 BODY=%d' % (environ.get('PATH_INFO', ''), total))
            except Exception:
                _log('REQ %s ERROR:\n%s' % (environ.get('PATH_INFO', ''), traceback.format_exc()))
                raise
            finally:
                try:
                    r.close()
                except Exception:
                    pass
        return _gen()
    except Exception:
        _log('REQ %s RAISE:\n%s' % (environ.get('PATH_INFO', ''), traceback.format_exc()))
        raise