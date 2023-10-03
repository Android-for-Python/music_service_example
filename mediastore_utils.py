from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture

from android import mActivity
from jnius import autoclass
from functools import partial

Uri = autoclass('android.net.Uri')
Size = autoclass('android.util.Size')
ContentUris = autoclass('android.content.ContentUris')
MS_FAIL = False

try:
    BitmapUtil = autoclass('org.kivy.player.BitmapUtil')
except Exception as e:
    Logger.error("Idiot, you didn't include the java in the build.\n" + str(e))
    MS_FAIL = True

try:
    MediaStoreConstants = autoclass('org.kivy.player.MediaStoreConstants')
    # Tables
    GENRE_TABLE = MediaStoreConstants.GENRE_TABLE
    MEDIA_TABLE = MediaStoreConstants.MEDIA_TABLE
    # Columns
    ID = MediaStoreConstants.ID
    GENRE_NAME = MediaStoreConstants.GENRE_NAME
    GENRE = MediaStoreConstants.GENRE
    GENRE_ID = MediaStoreConstants.GENRE_ID
    ALBUM = MediaStoreConstants.ALBUM
    ALBUM_ID = MediaStoreConstants.ALBUM_ID
    ALBUM_ARTIST = MediaStoreConstants.ALBUM_ARTIST
    TITLE = MediaStoreConstants.TITLE
    DISPLAY_NAME = MediaStoreConstants.DISPLAY_NAME
except Exception as e:
    Logger.error('Device Mediastore configuration error.\n' + str(e))
    MS_FAIL = True

class MediastoreUtils():

    def id_to_uri(self, ms_id):
        return ContentUris.withAppendedId(MEDIA_TABLE, ms_id)
    
    def list_genres(self):
        results = []
        try:
            columns = [GENRE_NAME, ID]
            context =  mActivity.getApplicationContext()
            cursor = context.getContentResolver().query(
                GENRE_TABLE, columns, None, None, GENRE_NAME + " ASC")
            genre_index = cursor.getColumnIndex(GENRE_NAME)
            id_index = cursor.getColumnIndex(ID)
            while cursor and cursor.moveToNext():
                genre_name = str(cursor.getString(genre_index))
                if genre_name != 'None':
                    results.append({'genre_name': genre_name,
                                    'genre_id': cursor.getLong(id_index)})
            if cursor:
                cursor.close()
        except Exception as e:
            Logger.error('Mediastore Genres error.\n' + str(e))
        return results

    def list_albums_in_genre(self, genre_id):
        results = []
        art_ids = []
        try:
            columns = [ID, ALBUM, ALBUM_ID, GENRE_ID] 
            selection = GENRE_ID + '=' + str(genre_id)
            context =  mActivity.getApplicationContext()
            resolver = context.getContentResolver()
            cursor = resolver.query(MEDIA_TABLE, columns, selection,
                                    None, ALBUM + " ASC")
            id_index = cursor.getColumnIndex(ID)
            album_index = cursor.getColumnIndex(ALBUM)
            album_id_index = cursor.getColumnIndex(ALBUM_ID)
            default_texture = CoreImage('icons/no_album_art.png').texture
            previous_album_name = ''
            index = 0
            while cursor and cursor.moveToNext():
                album_name = cursor.getString(album_index)
                # Can't get MediaStore to use DISCRETE, so filter by name.
                if album_name != previous_album_name:
                    art_ids.append((index, cursor.getLong(id_index)))
                    index += 1
                    results.append({'album_name': album_name,
                                    'album_art': default_texture,
                                    'album_id': cursor.getLong(album_id_index)})
                previous_album_name = album_name
            if cursor:
                cursor.close()
        except Exception as e:
            Logger.error('Mediastore Albums error.\n' + str(e))
        return results, art_ids

    def list_tracks_in_album(self, album_id):
        results = []
        try:
            columns = [ID, ALBUM_ID, TITLE, DISPLAY_NAME]
            selection = ALBUM_ID + '=' + str(album_id)  
            context =  mActivity.getApplicationContext()
            cursor = context.getContentResolver().query(
                MEDIA_TABLE, columns, selection, None, DISPLAY_NAME + ' ASC')
            title_index = cursor.getColumnIndex(TITLE)
            id_index = cursor.getColumnIndex(ID)
            while cursor and cursor.moveToNext():
                results.append({'track_name': cursor.getString(title_index),
                                'track_id': cursor.getLong(id_index)})
            if cursor:
                cursor.close()
        except Exception as e:
            Logger.error('Mediastore Track error.\n' + str(e))          
        return results
    
    def list_album_info(self, art_callback, album_id):
        track_id = None
        album = ''
        artist = ''
        try:
            columns = [ID, ALBUM_ID, ALBUM, ALBUM_ARTIST]
            selection = ALBUM_ID + '=' + str(album_id)  
            context =  mActivity.getApplicationContext()
            resolver = context.getContentResolver()
            cursor = resolver.query(MEDIA_TABLE, columns, selection, None, None)
            album_index = cursor.getColumnIndex(ALBUM)
            artist_index = cursor.getColumnIndex(ALBUM_ARTIST)
            id_index = cursor.getColumnIndex(ID)
            if cursor and cursor.moveToFirst():
                album = cursor.getString(album_index)
                artist = cursor.getString(artist_index)
                track_id = cursor.getLong(id_index)
            if cursor:
                cursor.close()
        except Exception as e:
            Logger.error('Mediastore Album Info error.\n' + str(e))
        if track_id:
            Clock.schedule_once(partial(self.add_thumbnail, art_callback,
                                        track_id, 300), 0.1)    
        return album, artist

    def list_track_info(self, track_uri_string, art_callback):
        track_name = ''
        artist_name = ''
        track_id = None
        try: 
            track_uri = Uri.parse(track_uri_string)
            columns = [ID, TITLE, ALBUM_ARTIST]
            context =  mActivity.getApplicationContext()
            resolver = context.getContentResolver()
            cursor = resolver.query(track_uri, columns, None, None, None)
            title_index = cursor.getColumnIndex(TITLE)
            artist_index = cursor.getColumnIndex(ALBUM_ARTIST)
            id_index = cursor.getColumnIndex(ID)
            if cursor and cursor.moveToFirst():
                track_name = cursor.getString(title_index)
                artist_name = cursor.getString(artist_index)  
                track_id = cursor.getLong(id_index)
            if cursor:
                cursor.close()
        except Exception as e:
            Logger.error('Mediastore Track Info error.\n' + str(e))
        if track_id:
            Clock.schedule_once(partial(self.add_thumbnail, art_callback,
                                        track_id, 800), 0.1) 
        return track_name, artist_name


    def add_thumbnail(self, art_callback, track_id, size, dt):
        thumbnail_size = Size(size, size)
        track_uri = ContentUris.withAppendedId(MEDIA_TABLE, track_id)
        try:
            context =  mActivity.getApplicationContext()
            resolver = context.getContentResolver()
            bitmap = resolver.loadThumbnail(track_uri, thumbnail_size, None)
        except Exception as e:
            # File not found
            bitmap = None
        if bitmap:
            size = (bitmap.getWidth(), bitmap.getHeight())
            pixels = bytes(BitmapUtil().toPixels(bitmap))
            texture = Texture.create(size, colorfmt='rgba')
            texture.flip_vertical()
            texture.blit_buffer(pixels, colorfmt='rgba', bufferfmt='ubyte')
        else:
            texture = CoreImage('icons/no_album_art.png').texture
        art_callback(texture)
        
    def add_many_thumbnails(self, art_callback, track_ids, resolution, dt):
        context =  mActivity.getApplicationContext()
        resolver = context.getContentResolver()       
        # Visible thumbnails are never updated by RV so we set the first 14 now.
        # 14 is a guess, of the number of instances first visible
        # The remainder are scheduled in chunks
        now = track_ids[:14]
        later = track_ids[14:]
        thumbnail_size = Size(resolution, resolution)
        for track_id in now:
            index = track_id[0]
            tid   = track_id[1]
            track_uri = ContentUris.withAppendedId(MEDIA_TABLE, tid)
            try:
                bitmap = resolver.loadThumbnail(track_uri, thumbnail_size, None)
            except Exception as e:
                # File not found
                bitmap = None
            if bitmap:
                size = (bitmap.getWidth(), bitmap.getHeight())
                pixels = bytes(BitmapUtil().toPixels(bitmap))
                texture = Texture.create(size, colorfmt='rgba')
                texture.flip_vertical()
                texture.blit_buffer(pixels, colorfmt='rgba', bufferfmt='ubyte')
                art_callback(index, texture)
            index += 1
        if later:
            Clock.schedule_once(partial(self.add_many_thumbnails, art_callback,
                                        later, resolution),0.1)
             
