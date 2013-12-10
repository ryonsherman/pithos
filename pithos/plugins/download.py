import os.path
import urllib
import logging

from gi.repository import Gtk
from pithos.plugin import PithosPlugin


class Download(PithosPlugin):
    preference = 'download'

    def __init__(self, *args, **kwargs):
        PithosPlugin.__init__(self, *args, **kwargs)
        self.window.prefs_dlg = self.prefs_dlg
        self.icon = self.window.plugins.get('notification_icon', False)

    def on_enable(self):
        self.window.song_menu.append(self.song_menu_item)
        if self.icon:
            self.icon.menu.append(self.icon_menu_item)
        print "Download plugin enabled"

    def on_disable(self):
        self.window.song_menu.remove(self.song_menu_item)
        if self.icon:
            self.icon.menu.remove(self.icon_menu_item)
        print "Download plugin disabled"

    @property
    def prefs_dlg(self):
        dialog = getattr(self, '_prefs_dlg', False)
        if not dialog:
            dialog = self.window.prefs_dlg
            pref = self.download_pref

            def show(widget):
                pref.set_active(dialog.get_preferences()['download'])
            dialog.connect('show', show)

            def response(widget, response):
                if response == Gtk.ResponseType.OK:
                    dialog.get_preferences()['download'] = pref.get_active()
                    dialog.save()
            dialog.connect('response', response)

            grid = dialog.builder.get_object('grid8')
            grid.attach(self.download_pref, 0, len(grid.get_children()), 1, 1)

            self._prefs_dlg = dialog
        return dialog

    @property
    def download_pref(self):
        pref = getattr(self, '_download_pref', False)
        if not pref:
            pref = Gtk.CheckButton("Enable downloading of songs")
            pref.show()

            # additional options
            # automatically download loved songs
            # allow

            def toggled(widget):
                if widget.get_active():
                    print 'show additional options'
                else:
                    print 'hide additional options'
            pref.connect('toggled', toggled)

            self._download_pref = pref
        return pref

    @property
    def additional_preferences(self):
        prefs = getattr(self, '_preferences', False)
        if not prefs:
            prefs = None
        return prefs

    @property
    def song_menu_item(self):
        item = getattr(self, '_song_menu_item', False)
        if not item:
            item = Gtk.ImageMenuItem("Download Song")
            item.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_SAVE, Gtk.IconSize.BUTTON))
            item.connect('activate', (lambda *i: self.show_save_dialog(self.window.selected_song())))
            item.show()
            self._song_menu_item = item
        return item

    @property
    def icon_menu_item(self):
        item = getattr(self, '_icon_menu_item', False)
        if not item:
            item = Gtk.ImageMenuItem("Download Song")
            item.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_SAVE, Gtk.IconSize.MENU))
            item.connect('activate', (lambda *i: self.show_save_dialog()))
            item.show()
            self._icon_menu_item = item
        return item

    def save_song(self, filename, song=None):
        song = song or self.window.current_song
        urllib.urlretrieve(song.audioUrl, filename)

    def show_save_dialog(self, song=None):
        song = song or self.window.current_song

        def response(dialog, response):
            if response == Gtk.ResponseType.ACCEPT:
                self.window.worker_run(self.save_song, (dialog.get_filename(), song), None, "Saving...")
            dialog.destroy()

        dialog = Gtk.FileChooserDialog("Save File", self.window, Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT))
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_modal(True)
        dialog.connect('response', response)
        dialog.set_current_folder(os.path.expanduser('~/Music'))
        dialog.set_current_name("{0} - {1} - {2}.mp4".format(song.artist, song.album, song.title))
        dialog.show()
