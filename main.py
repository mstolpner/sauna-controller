from kivy.config import Config

from SaunaController import SaunaController

# Enable virtual keyboard - must be before other kivy imports
Config.set('kivy', 'keyboard_mode', 'systemanddock')

from SaunaContext import SaunaContext
from ErrorManager import ErrorManager
from SaunaControllerUI import SaunaControlApp

if __name__ == '__main__':
    ctx = SaunaContext()
    errorMgr = ErrorManager()

    # Initialize Sauna Controller
    sc = SaunaController(ctx, errorMgr)
    sc.run()

    # Run the UI application (this blocks until app closes)
    SaunaControlApp(ctx=ctx, errorMgr=errorMgr).run()







