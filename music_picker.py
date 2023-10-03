from kivy.lang import Builder
from kivy.metrics import sp
from kivy.utils import rgba
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.modalview import ModalView
from kivy.properties import NumericProperty, StringProperty, ObjectProperty

from string_lines import StringLines
from mediastore_utils import MediastoreUtils, MS_FAIL

##################################################################
# MusicPicker is the root_class, it displays a list of Genres.
# On genre selection MusicPicker opens AlbumPicker passing genre_id,
# AlbumPicker displays a list of Albums.
# On album selection AlbumPicker opens TrackPicker passing album_id,
# TrackPicker displays a list of Tracks.
# On track selection TrackPicker updates the temp track list in MusicPicker.
# On MusicPicker close the track list is converted to a Uri list
#   and returned in a callback.
##################################################################

#######################
# Music Picker
#######################

Builder.load_string('''
<MusicPicker>:
    # RecycleView incorrectly ignores ModalView border, 
    # so explicity set border to zero.
    border: (0,0,0,0)
    MenuBackground
    BoxLayout:
        orientation: 'vertical'
        GenresRV:
            picker_root: root.picker_root
        MenuRelativeImageButton:
            size_hint_y: 0.1
            pressed: root.quit_picker
            source: 'icons/arrow_left_white.png'

<GenresRV>:
    viewclass: 'GenreSelection'
    RecycleBoxLayout:
        default_size: None, dp(56)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'

<GenreSelection>:
    MenuBackGesturePadding
    MenuTextButton:
        text: root.genre_name
        on_press: root.show_albums()
    MenuBackGesturePadding

<MenuBackground@Widget>:
    canvas.before:
        Color: 
            rgba: rgba('#708090')
        Rectangle:
            pos: self.pos
            size: self.size

<MenuTextButton@ButtonBehavior+Label>:

<MenuImageButton@ButtonBehavior+Image>:

<MenuRelativeImageButton@RelativeLayout>:
    pressed: None
    source: ''
    MenuImageButton:
        source: root.source
        on_press: root.pressed()
        fit_mode: 'contain'
        size_hint: (None, 0.8)
        width: self.height
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}

# A Button Press may occur (usually occurs?) before a Back Gesture :(
# So a back gesture is passed to the Button's new child ModalView which
# immediately responds to the parent's gesture and closes. 
# Creating an unexpected NOP. So pad viewclass edges.

<MenuBackGesturePadding@MenuBackground>:
    width: self.height // 3
    size_hint: (None, 1)

''')


class MusicPicker(ModalView):
    picker_root = ObjectProperty()

    def __init__(self, callback, **args):
        super().__init__(**args)
        self.picker_root = self
        self.callback = callback
        self.temp_track_list = []
        if MS_FAIL:
            self.quit_picker()

    def on_pre_dismiss(self,*args):
        uris = []
        for track_id in self.temp_track_list:
            uris.append(MediastoreUtils().id_to_uri(track_id))
        self.callback(uris)

    def quit_picker(self):
        self.dismiss()
        

class GenresRV(RecycleView):
    picker_root = ObjectProperty()

    def on_picker_root(self, obj, items):
        genres = MediastoreUtils().list_genres()
        for g in genres:
            g['picker_root'] = self.picker_root
        self.data = genres
        
class GenreSelection(BoxLayout):
    genre_id = NumericProperty()
    genre_name = StringProperty()
    picker_root = ObjectProperty()

    def show_albums(self):
        AlbumPicker(self.genre_id, self.picker_root).open()


#######################
# Album Picker
#######################

Builder.load_string('''
<AlbumPicker>:
    border: (0,0,0,0) 
    MenuBackground 
    BoxLayout:
        orientation: 'vertical'
        Albums:
            picker_root: root.picker_root
            genre_id: root.genre_id
        MenuRelativeImageButton:
            size_hint_y: 0.1
            pressed: root.quit_picker
            source: 'icons/arrow_left_white.png'

<Albums>:
    viewclass: 'AlbumSelection'
    RecycleBoxLayout:
        id: rbl
        default_size: None, dp(56)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'

<AlbumSelection>:
    Image:
        texture: root.album_art
        fit_mode: 'contain'
        width: self.height
        size_hint: (None, 1)
    MenuTextButton:
        text: root.album_name
        on_press: root.show_tracks()
    MenuBackGesturePadding

''')

class AlbumPicker(ModalView):
    genre_id = NumericProperty()
    picker_root = ObjectProperty()

    def __init__(self, genre_id, picker_root, **args):
        super().__init__(**args)
        self.genre_id = genre_id
        self.picker_root = picker_root

    def quit_picker(self):
        self.dismiss()
        
class Albums(RecycleView):
    genre_id = NumericProperty()
    picker_root = ObjectProperty()

    def on_picker_root(self, obj, items):
        if self.genre_id:
            self.read_mediastore()
    
    def on_genre_id(self, obj, items):
        if self.picker_root:
            self.read_mediastore()

    def art_callback(self, index, texture):
        self.data[index]['album_art'] = texture    
        
    def read_mediastore(self):
        # Don't know how long the label will be, so guess 85% of Window
        # based on image on left and padding on right.
        sl = StringLines()
        max_cols = sl.estimate_columns(sp(16),round(Window.width * 0.85))
        
        albums, arts = MediastoreUtils().list_albums_in_genre(self.genre_id)
        for a in albums:
            a['picker_root'] = self.picker_root
            a['album_name'] = sl.multiline_string(a['album_name'], max_cols, 2)
        self.data = albums
        # resolution of 160 is picked for speed
        MediastoreUtils().add_many_thumbnails(self.art_callback, arts, 160, 0)

            
class AlbumSelection(BoxLayout):
    album_id = NumericProperty()
    album_name = StringProperty()
    album_art = ObjectProperty()
    picker_root = ObjectProperty()

    def show_tracks(self):
        TrackPicker(self.album_id, self.picker_root).open()

#######################
# Track Picker
#######################

Builder.load_string('''
<TrackPicker>:
    border: (0,0,0,0)
    MenuBackground 
    BoxLayout:
        orientation: 'vertical'
        Label:
            size_hint_y: 0.05
        TrackHeader:
            album_id: root.album_id
            size_hint_y: 0.15
        Label:
            size_hint_y: 0.05
        TracksRV:
            picker_root: root.picker_root
            album_id: root.album_id
        MenuRelativeImageButton:
            size_hint_y: 0.1
            pressed: root.quit_picker
            source: 'icons/arrow_left_white.png'

<TracksRV>:
    viewclass: 'TrackSelection'
    RecycleBoxLayout:
        default_size: None, dp(56)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'

<TrackSelection>:
    MenuBackGesturePadding
    MenuTextButton:
        id: mtb
        text: root.track_name
        on_press: root.pick_item()
    MenuBackGesturePadding

<TrackHeader>:
    orientation: 'horizontal'
    MenuBackGesturePadding
    Image:
        texture: root.album_art
        fit_mode: 'contain'
        width: self.height
        size_hint: (None, 1)
    BoxLayout:
        orientation: 'vertical'
        Label:
            text: root.album_title
            bold : True
        Label:
            text: root.album_artist
            bold : True
        MenuBackGesturePadding

''')

class TrackPicker(ModalView):
    album_id = NumericProperty()
    picker_root = ObjectProperty()

    def __init__(self, album_id, picker_root, **args):
        super().__init__(**args)
        self.album_id = album_id
        self.picker_root = picker_root        
        self.selected = []

    def quit_picker(self):
        self.dismiss()

class TrackHeader(BoxLayout):
    album_id = NumericProperty()
    album_title = StringProperty()
    album_artist = StringProperty()
    album_art = ObjectProperty()

    def art_callback(self, texture):
        self.album_art = texture

    def on_album_id(self, album_id, items):
        album, artist = MediastoreUtils().list_album_info(self.art_callback,
                                                          self.album_id)
        sl = StringLines()    # another estimate..
        max_cols = sl.estimate_columns(sp(16),round(Window.width * 0.8))
        self.album_title = sl.multiline_string(album, max_cols, 2)
        self.album_artist = sl.multiline_string(artist, max_cols, 2)

        
class TracksRV(RecycleView):
    album_id = NumericProperty()
    picker_root = ObjectProperty()

    def on_picker_root(self, obj, items):
        if self.album_id:
            self.read_mediastore()
    
    def on_album_id(self, obj, items):
        if self.picker_root:
            self.read_mediastore()
        
    def read_mediastore(self):
        tracks = MediastoreUtils().list_tracks_in_album(self.album_id)
        sl = StringLines()    # another estimate..
        max_cols = sl.estimate_columns(sp(16),round(Window.width * 0.9))
        for t in tracks:
            t['picker_root'] = self.picker_root
            t['track_name'] = sl.multiline_string(t['track_name'], max_cols, 2)
        self.data = tracks
        

class TrackSelection(BoxLayout):
    track_id = NumericProperty()
    track_name = StringProperty()
    picker_root = ObjectProperty()

    def on_picker_root(self, obj, items):
        if self.track_id:
            self.update_selected()
    
    def on_track_id(self, obj, items):
        if self.picker_root:
            self.update_selected()

    def update_selected(self):
        if self.track_id in self.picker_root.temp_track_list:
            self.ids.mtb.color = rgba('#800000')
            
    def pick_item(self):
        if self.track_id in self.picker_root.temp_track_list:
            self.picker_root.temp_track_list.remove(self.track_id)
            self.ids.mtb.color = rgba('#FFFFFF')
        else:
            self.picker_root.temp_track_list.append(self.track_id)
            self.ids.mtb.color = rgba('#800000')

