import os.path
import urllib
import logging

from gi.repository import Gtk
from pithos.plugin import PithosPlugin


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

    def on_disable(self):
        self.window.song_menu.remove(self.song_menu_item)
        if self.icon:
            self.icon.menu.remove(self.icon_menu_item)

    @property
    def prefs_dlg(self):
        dialog = getattr(self, '_prefs_dlg', False)
        if not dialog:
            dialog = self.window.prefs_dlg
            pref = self.download_pref

            def show(widget):
                self.download_pref.set_active(dialog.get_preferences().get('download', False))
                self.auto_download_pref.set_active(dialog.get_preferences().get('auto_download', False))
            dialog.connect('show', show)

            def response(widget, response):
                if response == Gtk.ResponseType.OK:
                    dialog.get_preferences()['download'] = self.download_pref.get_active()
                    dialog.get_preferences()['auto_download'] = self.auto_download_pref.get_active()
                    dialog.save()
            dialog.connect('response', response)

            self.grid.attach(self.download_pref, 0, len(self.grid.get_children()), 1, 1)
            self.grid.attach(self.auto_download_pref, 0, len(self.grid.get_children()), 1, 1)
            self.grid.attach(self.download_folder_pref, 0, len(self.grid.get_children()), 1, 1)

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
                    self.auto_download_pref.show()
                    self.download_folder_pref.show()
                else:
                    self.auto_download_pref.hide()
                    self.download_folder_pref.hide()
            pref.connect('toggled', toggled)

            self._download_pref = pref
        return pref

    @property
    def auto_download_pref(self):
        pref = getattr(self, '_auto_download_pref', False)
        if not pref:
            pref = Gtk.CheckButton("Automatically download loved songs")
            pref.set_margin_left(25)
            pref.hide()

            def toggled(widget):
                self.download_folder_pref.set_sensitive(widget.get_active())
            pref.connect('toggled', toggled)

            self._auto_download_pref = pref
        return pref

    @property
    def download_folder_pref(self):
        pref = getattr(self, '_download_folder_pref', False)
        if not pref:
            pref = Gtk.Grid()
            pref.set_sensitive(False)
            pref.set_margin_left(30)
            pref.set_column_spacing(10)
            pref.hide()

            label = Gtk.Label("Folder:")
            label.show()

            entry = Gtk.Entry()
            entry.show()

            button = Gtk.Button(" ... ")
            button.show()

            pref.attach(label, 0, 0, 1, 1)
            pref.attach(entry, 1, 0, 1, 1)
            pref.attach(button, 2, 0, 1, 1)

            self._download_folder_pref = pref
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
