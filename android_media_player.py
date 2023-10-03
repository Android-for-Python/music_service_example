from kivy.logger import Logger
from jnius import autoclass, PythonJavaClass, java_method

MediaPlayer = autoclass('android.media.MediaPlayer')
KivyCompletionListener = autoclass('org.kivy.player.KivyCompletionListener')
Uri = autoclass('android.net.Uri')


class AndroidMediaPlayer():

    # self.player.setWakeMode(getApplicationContext(), PowerManager.PARTIAL_WAKE_LOCK)

    def init_player(self, service_callback):
        self.callback_wrapper = CallbackWrapper(service_callback,
                                                self.error_handler)
        self.player = MediaPlayer()
        self.player.setOnCompletionListener(
            KivyCompletionListener(self.callback_wrapper))

    def start(self, mActivity, uri):
        try:
            self.player.reset()
            self.player.setDataSource(mActivity, Uri.parse(uri))
            self.player.prepare()
            self.player.start()
        except Exception as e:
            Logger.warning('Android Media Player prepare() failed.\n' +\
                           str(e))

    def pause(self):
        self.player.pause()
    
    def resume(self):
        self.player.start()
    
    def stop(self):
        self.player.stop()

    def release(self):
        self.player.release()

    def error_handler(self):
        Logger.warning('Android Media Player was reset due to an error.')
        self.player.reset()
        

class CallbackWrapper(PythonJavaClass):
    __javacontext__ = 'app'
    __javainterfaces__ = ['org/kivy/player/CallbackWrapper']

    def __init__(self, service_callback, error_callback):
        super().__init__()
        self.service_callback = service_callback
        self.error_callback = error_callback

    @java_method('()V')        
    def on_completion(self):
        if self.service_callback:
            self.service_callback()        

    @java_method('()V')        
    def on_error(self):
        if self.error_callback:
            self.error_callback()
        if self.service_callback:            
            self.service_callback()     
