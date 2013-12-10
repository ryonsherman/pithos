import os
import urllib
import logging

from gi.repository import Gtk
from pithos.plugin import PithosPlugin
from pithos.pandora import RATE_LOVE


class Download(PithosPlugin):
    preference = 'download'

    def __init__(self, *args, **kwargs):
        PithosPlugin.__init__(self, *args, **kwargs)
        self.grid = self.window.prefs_dlg.builder.get_object('grid8')
        self.window.prefs_dlg = self.prefs_dlg
        self.icon = self.window.plugins.get('notification_icon', False)

    def on_enable(self):
        self.window.song_menu.append(self.song_menu_item)
        if self.icon:
            self.icon.menu.append(self.icon_menu_item)
        self.window.connect('song-changed', self.song_changed)

    def on_disable(self):
        self.window.song_menu.remove(self.song_menu_item)
        if self.icon:
            self.icon.menu.remove(self.icon_menu_item)
        self.window.disconnect_by_func(self.song_changed)

    @property
    def prefs_dlg(self):
        dialog = getattr(self, '_prefs_dlg', False)
        if not dialog:
            dialog = self.window.prefs_dlg
            pref = self.download_pref

            def show(widget):
                self.download_pref.set_active(dialog.get_preferences().get('download', False))
                self.download_folder_pref.entry.set_text(self.download_folder)
                self.auto_download_pref.set_active(dialog.get_preferences().get('auto_download', False))
            dialog.connect('show', show)

            def response(widget, response):
                if response == Gtk.ResponseType.OK:
                    dialog.get_preferences()['download'] = self.download_pref.get_active()
                    dialog.get_preferences()['download_folder'] = self.download_folder_pref.entry.get_text()
                    dialog.get_preferences()['auto_download'] = self.auto_download_pref.get_active()
                    dialog.save()
            dialog.connect('response', response)

            self.grid.attach(self.download_pref, 0, len(self.grid.get_children()), 1, 1)
            self.grid.attach(self.download_folder_pref, 0, len(self.grid.get_children()), 1, 1)
            self.grid.attach(self.auto_download_pref, 0, len(self.grid.get_children()), 1, 1)

            self._prefs_dlg = dialog
        return dialog

    @property
    def download_folder(self):
        folder = self.window.prefs_dlg.get_preferences().get('download_folder', False)
        if not folder:
            folder = os.path.expanduser('~/Music')
        if not os.path.exists(folder):
            folder = os.path.expanduser('~/Downloads')
        if not os.path.exists(folder):
            folder = os.path.expanduser('~')
        return folder

    def song_folder(self, song=None, exists=False):
        song = song or self.window.current_song
        folder = os.path.join(self.download_folder, song.artist, song.album)
        if not exists:
            return folder
        if os.path.exists(folder):
            return folder
        folder = os.path.join(self.download_folder, song.artist)
        if os.path.exists(folder):
            return folder
        return self.download_folder

    def song_filename(self, song=None, folder=None):
        song = song or self.windo.current_song
        filename = "{0}.mp4".format(song.title)

        if folder and folder.endswith(song.album):
            return filename
        if folder and folder.endswith(song.artist):
            return "{0} - {1}".format(song.album, filename)
        return "{0} - {1} - {2}".format(song.artist, song.album, filename)

    @property
    def download_pref(self):
        pref = getattr(self, '_download_pref', False)
        if not pref:
            pref = Gtk.CheckButton("Enable downloading of songs")
            pref.show()

            def toggled(widget):
                if widget.get_active():
                    self.download_folder_pref.show()
                    self.auto_download_pref.show()
                else:
                    self.download_folder_pref.hide()
                    self.auto_download_pref.hide()
            pref.connect('toggled', toggled)

            self._download_pref = pref
        return pref

    @property
    def download_folder_pref(self):
        pref = getattr(self, '_download_folder_pref', False)
        if not pref:
            pref = Gtk.Grid()
            pref.set_margin_left(30)
            pref.set_column_spacing(10)
            pref.hide()

            label = Gtk.Label("Folder:")
            label.show()

            entry = Gtk.Entry()
            entry.set_editable(False)
            entry.show()
            pref.entry = entry

            button = Gtk.Button(" ... ")
            button.connect('clicked', (lambda *i: self.show_download_folder_dialog()))
            button.show()

            pref.attach(label, 0, 0, 1, 1)
            pref.attach(entry, 1, 0, 1, 1)
            pref.attach(button, 2, 0, 1, 1)

            self._download_folder_pref = pref
        return pref

    @property
    def auto_download_pref(self):
        pref = getattr(self, '_auto_download_pref', False)
        if not pref:
            pref = Gtk.CheckButton("Automatically download loved songs")
            pref.set_margin_left(25)
            pref.hide()

            self._auto_download_pref = pref
        return pref

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
        folder = self.song_folder(song, True)

        dialog = Gtk.FileChooserDialog("Save File", self.window, Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT))
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_modal(True)
        dialog.set_current_folder(folder)
        dialog.set_current_name(self.song_filename(song, folder))
        dialog.show()

        def response(dialog, response):
            if response == Gtk.ResponseType.ACCEPT:
                self.window.worker_run(self.save_song, (dialog.get_filename(), song), None, "Saving...")
            dialog.destroy()
        dialog.connect('response', response)

    def show_download_folder_dialog(self):
        dialog = Gtk.FileChooserDialog("Select Folder", self.window, Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_modal(True)
        dialog.set_current_folder(self.download_folder)
        dialog.show()

        def response(dialog, response):
            if response == Gtk.ResponseType.OK:
                self.download_folder_pref.entry.set_text(dialog.get_filename())
            dialog.destroy()
        dialog.connect('response', response)

    def song_changed(self, window, song):
        if window.prefs_dlg.get_preferences().get('auto_download', False) and song.rating == RATE_LOVE:
            folder = self.song_folder(song)
            filename = os.path.join(folder, self.song_filename(song, folder))
            if not os.path.exists(filename):
                if not os.path.exists(folder):
                    os.makedirs(folder)
                self.window.worker_run(self.save_song, (filename, song), None, "Saving...")
