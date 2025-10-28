from kivy.config import Config
from SaunaController import SaunaController
import web_server

# Enable virtual keyboard - must be before other kivy imports
Config.set('kivy', 'keyboard_mode', 'systemanddock')

from SaunaContext import SaunaContext
from ErrorManager import ErrorManager
from SaunaControllerUI import SaunaControlApp

if __name__ == '__main__':
    _ctx = SaunaContext()
    _errorMgr = ErrorManager()

    # Initialize Sauna Controller
    _sc = SaunaController(_ctx, _errorMgr)
    _sc.run()

    web_server.start_web_ui(_ctx, _sc, _errorMgr)

    # Run the UI application (this blocks until app closes)
    SaunaControlApp(ctx=_ctx, errorMgr=_errorMgr).run()







