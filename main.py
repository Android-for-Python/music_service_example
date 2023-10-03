from kivy.app import App
from kivy.metrics import sp
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import StringProperty, ObjectProperty
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage

from android import mActivity
from jnius import autoclass, cast

from oscpy.client import OSCClient
from oscpy.server import OSCThreadServer

from android_permissions import AndroidPermissions
from mediastore_utils import MediastoreUtils
from music_picker import MusicPicker
from string_lines import StringLines

LAYOUT = """
BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        size_hint: (1, 0.8)
        orientation: 'horizontal'
        RelativeButton: 
            pressed: app.add_to_playlist
            icon: 'icons/round_queue_music_white_48.png'
        RelativeButton: 
            pressed: app.terminate_service
            icon: 'icons/round_playlist_remove_white_48.png'
    LabelWithBackground:
        id: playlist
        size_hint: (1, 0.1)
        text: 'The Music Playlist is Empty.'
        font_size: '16sp'
    RelativeImage:
        id: album_art
    BoxLayout:
        orientation: 'vertical'
        LabelWithBackground:
            id: song_title
            bold : True
            font_size: '24sp'
            size_hint: (1, 0.6)
        LabelWithBackground:
            id: artist
            font_size: '16sp'
            size_hint: (1, 0.4)
        Background
            id: padding
            size_hint: (1, 0.2)
    BoxLayout:
        orientation: 'horizontal'
        RelativeButton: 
            pressed: app.skip_previous
            icon: 'icons/round_skip_previous_white_48.png'
        RelativeButton: 
            id: pp
            pressed: app.play_pause
            icon: 'icons/round_play_arrow_white_48.png'
        RelativeButton: 
            pressed: app.skip_next
            icon: 'icons/round_skip_next_white_48.png'

<Background@Widget>:
    canvas.before:
        Color: 
            rgba: rgba('#800000')
        Rectangle:
            pos: self.pos
            size: self.size

<LabelWithBackground@Label+Background>:
    text: ''

<RelativeImage@RelativeLayout>:
    texture: None
    Background:
    Image:
        texture: root.texture
        fit_mode: 'contain'
        size_hint: (None, 0.8)
        width: self.height
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}

<RelativeButton@RelativeLayout>:
    pressed: None
    icon: ''
    Background:
    Button:
        on_press: root.pressed()
        size_hint: (None, 0.5)
        width: self.height
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        background_normal: root.icon
        background_down: self.background_normal
"""

class ServiceMediaPlayer(App):
    
    ##################
    # Layout
    ##################

    def build(self, **args):
        self.show_pause = False
        self.granted = False
        self.kv = Builder.load_string(LAYOUT)
        return self.kv

    def set_pause(self):
        self.show_pause = True
        self.kv.ids.pp.icon = 'icons/round_pause_white_48.png'

    def set_play(self):
        self.show_pause = False
        self.kv.ids.pp.icon = 'icons/round_play_arrow_white_48.png'

    @mainthread
    def set_title(self, title):
        title = StringLines().multiline_string(title, self.cols_24sp) 
        self.kv.ids.song_title.text = title
        rows = title.count('\n') + 1
        self.set_size_hints(rows)

    @mainthread
    def set_artist(self, artist):
        artist = StringLines().multiline_string(artist, self.cols_16sp) 
        self.kv.ids.artist.text = artist

    @mainthread
    def set_album_art(self, texture):
        if texture == None:
            texture = CoreImage('icons/no_album_art.png').texture
        self.kv.ids.album_art.texture = texture        
        
    def set_playlist(self, playlist_state):
        self.kv.ids.playlist.text = playlist_state

    def set_size_hints(self, rows):
        off = max(rows, 2)
        self.kv.ids.song_title.size_hint = (1, off/3)
        self.kv.ids.artist.size_hint = (1, 1/3)
        self.kv.ids.padding.size_hint = (1, (2-off)/3)
        
    @mainthread
    def update_playlist_info(self, playlist_state):
        self.set_playlist(playlist_state.decode('utf8'))

    ##################
    # App Lifecycle
    ##################
    
    def on_start(self):
        self.set_album_art(None)
        self.string_lines = StringLines()
        self.cols_16sp = self.string_lines.estimate_columns(sp(16),Window.width)
        self.cols_24sp = self.string_lines.estimate_columns(sp(24),Window.width)
        server = OSCThreadServer()
        server.listen(address=b'localhost', port=3002, default=True)
        server.bind(b'/track_state', self.track_state)
        server.bind(b'/playlist_state', self.update_playlist_info)
        self.client = OSCClient(b'localhost', 3000)
        self.dont_gc = AndroidPermissions(self.app_start)

    def app_start(self):
        self.dont_gc = None
        self.granted = True
        self.query_service_state()
            
    def on_resume(self):
        self.query_service_state()
            
    ##################
    # Service State
    ##################

    def get_service_name(self):
        context =  mActivity.getApplicationContext()
        return str(context.getPackageName()) + '.Service' + 'Mediaplayer'

    def service_is_running(self):
        service_name = self.get_service_name()
        context =  mActivity.getApplicationContext()
        manager = cast('android.app.ActivityManager',
                       mActivity.getSystemService(context.ACTIVITY_SERVICE))
        for service in manager.getRunningServices(100):
            if service.service.getClassName() == service_name:
                return True
        return False
           
    def start_service_if_not_running(self):
        if self.service_is_running():
            return
        service = autoclass(self.get_service_name())
        service.start(mActivity,'round_music_note_white_24',
                      'Music Service','Started','')   

    def query_service_state(self):
        if self.service_is_running():
            self.client.send_message(b'/service_state', [])
        else:
            self.set_play()
            self.set_album_art(None)

    ##################
    # Track Metadata
    ##################

    def track_state(self, encoded_uri):
        uri = encoded_uri.decode('utf8')
        if uri:
            title, artist =\
                MediastoreUtils().list_track_info(uri, self.set_album_art)
            self.set_title(title)
            self.set_artist(artist)
        else:
            self.set_title('')
            self.set_artist('')
            self.set_album_art(None)

    ##################
    # UI Events
    ##################

    def add_to_playlist(self):
        if self.granted:
            self.start_service_if_not_running()         
            MusicPicker(self.picker_callback).open()

    def picker_callback(self, uri_list):
        encoded_uris = []
        for uri in uri_list:
            encoded_uris.append(uri.toString().encode('utf-8'))
        if encoded_uris:
            self.client.send_message(b'/add_playlist', encoded_uris)        

    def terminate_service(self):
        if self.granted:
            self.client.send_message(b'/terminate', [])
            self.set_play()

    def play_pause(self):
        if self.granted:
            if self.show_pause:
                self.client.send_message(b'/pause', [])
                self.set_play()
            else:
                self.client.send_message(b'/play', [])
                self.set_pause()

    def skip_next(self):
        if self.granted:
            self.client.send_message(b'/skip_next', [])        

    def skip_previous(self):
        if self.granted:
            self.client.send_message(b'/skip_previous', [])

ServiceMediaPlayer().run()
