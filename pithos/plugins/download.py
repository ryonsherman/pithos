from gi.repository import Gtk
from pithos.plugin import PithosPlugin


class Download(PithosPlugin):
    preference = 'download'

    def __init__(self, *args, **kwargs):
        PithosPlugin.__init__(self, *args, **kwargs)

        dialog = self.window.prefs_dlg

        option = Gtk.CheckButton("Enable downloading of songs")
        option.show()

        grid = dialog.builder.get_object('grid8')
        grid.attach(option, 0, len(grid.get_children()), 1, 1)

        def show(widget):
            option.set_active(dialog.get_preferences()['download'])
        dialog.connect('show', show)

        def response(widget, response):
            if response == Gtk.ResponseType.OK:
                dialog.get_preferences()['download'] = option.get_active()
                dialog.save()
        dialog.connect('response', response)

    def on_prepare(self):
        def save_dialog(song=None):
            song = song or self.window.current_song
            def response(dialog, response):
                if response == Gtk.ResponseType.ACCEPT:
                    self.worker_run(song.save, (dialog.get_filename(),), None, "Saving...")
                dialog.destroy()
            dialog = Gtk.FileChooserDialog("Save File", self.window, Gtk.FileChooserAction.SAVE,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT))
            dialog.set_do_overwrite_confirmation(True)
            dialog.set_modal(True)
            dialog.connect('response', response)
            dialog.set_current_name("{0} - {1} - {2}.mp4".format(song.artist, song.album, song.title))
            dialog.show()

        self.menu_item = Gtk.ImageMenuItem("Download Song")
        self.menu_item.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_SAVE, Gtk.IconSize.BUTTON))
        self.menu_item.connect('activate', (lambda *i: save_dialog(self.window.selected_song())))
        self.menu_item.show()

    def on_enable(self):
        self.window.song_menu.append(self.menu_item)
        print 'Download plugin enabled'

    def on_disable(self):
        print 'Download plugin disabled'


