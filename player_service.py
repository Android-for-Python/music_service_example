from time import sleep
from oscpy.server import OSCThreadServer
from oscpy.client import OSCClient 
from android.config import SERVICE_CLASS_NAME
from jnius import autoclass

from android_media_player import AndroidMediaPlayer

PythonService = autoclass(SERVICE_CLASS_NAME)

class Player:

    #############
    # Event Loop
    #############    

    def run(self):
        # Player and OSC state
        self.server = OSCThreadServer()
        self.server.listen('localhost', port=3000, default=True)
        self.client = OSCClient('localhost', 3002)
        self.player = AndroidMediaPlayer()
        self.mService = PythonService.mService
        self.playlist = []
        self.now_playing = 0
        self.loop_running = True
        self.paused = False

        # UI events
        self.server.bind(b'/add_playlist', self.add_playlist)
        self.server.bind(b'/terminate', self.terminate)
        self.server.bind(b'/play', self.play)
        self.server.bind(b'/pause', self.pause)
        self.server.bind(b'/skip_next', self.skip_next)
        self.server.bind(b'/skip_previous', self.skip_previous)
        self.server.bind(b'/service_state', self.service_state)

        # Android MediaPlayer Event
        self.player.init_player(self.play_next)

        # Loop
        while self.loop_running:
            sleep(0.1)
        self.mService.stopSelf()

    ##################
    # Event Actions
    ##################

    def add_playlist(self, *uri_list):
        for uri in uri_list:
            self.playlist.append(uri)
        self.service_state()

    def terminate(self):
        self.playlist = []
        self.loop_running = False
        self.service_state()
        self.player.stop()
        self.player.release()
        self.server.terminate_server()
        sleep(0.1)
        self.server.close()

    def play(self, *action_list):
        if self.playlist:
            if self.paused:
                self.paused = False
                self.player.resume()
            else:
                self.player.start(self.mService,self.playlist[self.now_playing])

    def pause(self, *action_list):
        if self.playlist and not self.paused:
            self.player.pause()
            self.paused = True

    def skip_next(self):
        self.player.stop()
        self.play_next()

    def skip_previous(self):
        if self.now_playing < 1:
            self.now_playing = len(self.playlist)
        self.now_playing = self.now_playing -1
        self.player.stop()
        self.service_state()
        if not self.paused:
            self.player.start(self.mService, self.playlist[self.now_playing])

    def play_next(self):
        self.now_playing = self.now_playing +1
        if self.now_playing >= len(self.playlist):
            self.now_playing = 0
        self.service_state()
        if not self.paused:
            self.player.start(self.mService, self.playlist[self.now_playing])

    def service_state(self):
        if self.playlist:
            uri = self.playlist[self.now_playing]
        else:
            uri = ''.encode('utf8')
        self.client.send_message(b'/track_state', [uri])

        if self.playlist:
            msg = 'Track ' + str(self.now_playing + 1) + ' of ' +\
                str(len(self.playlist)) + ' in the Playlist.'
        else:
            msg = 'The Music Playlist is Empty.'
        self.client.send_message(b'/playlist_state', [msg.encode('utf8')])
         

Player().run()

