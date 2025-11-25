from kivy.config import Config
from core.SaunaController import SaunaController
from SaunaWebUIServer import SaunaWebUIServer
import threading

# Enable virtual keyboard - must be before other kivy imports
Config.set('kivy', 'keyboard_mode', 'systemanddock')

from core.SaunaContext import SaunaContext
from core.SaunaErrorMgr import SaunaErrorMgr
from SaunaUIMainScreen import SaunaControlApp

if __name__ == '__main__':
    _ctx = SaunaContext()
    _errorMgr = SaunaErrorMgr(_ctx)

    # Initialize Sauna Controller
    _sc = SaunaController(_ctx, _errorMgr)
    _sc.run()
    """
    # Start web server in background thread
    web_thread = threading.Thread(
        target=SaunaWebUIServer.start_web_ui,
        args=(_ctx, _errorMgr),
        daemon=True
    )
    web_thread.start()"""

    # Start web server in background thread
    server = SaunaWebUIServer(_ctx, _errorMgr)
    web_thread = threading.Thread(
        target=server.run,
        daemon=True
    )
    web_thread.start()

    # Run the Kivy UI application (this blocks until app closes)
    SaunaControlApp(ctx=_ctx, errorMgr=_errorMgr).run()







