Music Service Example
=====================

Plays music from a service, the player is persistent regardless of the app state. Features are only those required to illustrate playing music from a service.

The example illustrates using a 'foreground sticky' service that is stateful. It also illustrates querying the Android Mediastore.

To use the app, music must exist on the device. Add music to the app's playlist using the app's picker.

The playlist is played in order and repeats. The lifetime of the playlist is the lifetime of the service. You can append to or clear the playlist at any time, while the app is open.

Receiving shares is not implemented, if you want to add this take a look at the [share_receive_example](https://github.com/Android-for-Python/share_receive_example).

Playing streamed music is not implemented, as it is not required to illustrate playing music from a service. But presumably streamed music is just another uri, however it is possible you may have to research the implications for metadata. Don't ask I didn't look at this.

The music on the device must be tagged with album artist, album name, track name, genre, and optionally album art. If there is no (suitably tagged) music found some picker screens will be empty.

It is possible that some device vendors will have non-standard Mediastore implementations that are different in a way that is significant to this example. In this case the picker will immediately close. See the logcat for details. There are no known cases of this, but this does not mean that there won't be.

buildozer.spec:
```
requirements = python3,kivy,oscpy

services = Mediaplayer:player_service.py:foreground:sticky

android.permissions = INTERNET, FOREGROUND_SERVICE, READ_MEDIA_AUDIO, POST_NOTIFICATIONS

android.api = 34

android.add_src = java

android.add_resources = icons/round_music_note_white_24.png:mipmap



```

