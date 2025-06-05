from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.app import App
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture

import shutil
import os


class ScanlineScreen(Screen):
    scan_texture = ObjectProperty(None)
    scan_offset = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._scan_offset = 0
        Clock.schedule_interval(self._update_scanlines, 1 / 60.)  # 30 fps

        self.scan_texture = CoreImage("assets\scanlines.png").texture
        self.scan_texture.wrap = 'repeat'

    def _update_scanlines(self, dt):
        self._scan_offset += 0.3
        #self.canvas.ask_update()


def animate_glitch(label):
    anim = Animation(color=(0, 1, 1, 0.6), duration=0.2) + Animation(color=(0, 1, 1, 1), duration=0.2)
    anim.repeat = True
    anim.start(label)


class LoginPopup(Popup):
    def validate(self, password):
        App.get_running_app().validate_admin(password)
        self.dismiss()


class MenuScreen(ScanlineScreen):
    def on_enter(self):
        print("IDs dans MenuScreen :", self.ids)
        animate_glitch(self.ids.title_label)
        self.ids.album_grid.clear_widgets()
        albums_path = "albums"
        if not os.path.exists(albums_path):
            os.makedirs(albums_path)
        for album_name in os.listdir(albums_path):
            btn = Button(text=album_name, size_hint_y=None, height=40)
            btn.bind(on_release=lambda x, a=album_name: self.open_album(a))
            self.ids.album_grid.add_widget(btn)

    def open_album(self, album_name):
        self.manager.get_screen('album').album_name = album_name
        self.manager.current = 'album'

    def open_admin(self):
        popup = LoginPopup()
        popup.open()


class AlbumScreen(Screen):
    album_name = ""

    def on_enter(self):
        self.ids.media_grid.clear_widgets()
        album_path = os.path.join("albums", self.album_name)
        for filename in os.listdir(album_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(album_path, filename)
                self.ids.media_grid.add_widget(Image(source=image_path))


class AdminScreen(Screen):
    def on_pre_enter(self):
        self.refresh_spinners()

    def refresh_spinners(self):
        albums = self.get_album_list()
        self.ids.delete_album_spinner.values = albums
        self.ids.import_album_spinner.values = albums

    def get_album_list(self):
        albums_path = "albums"
        if not os.path.exists(albums_path):
            os.makedirs(albums_path)
        return [d for d in os.listdir(albums_path) if os.path.isdir(os.path.join(albums_path, d))]

    def create_album(self):
        album_name = self.ids.new_album_name.text.strip()
        if album_name:
            path = os.path.join("albums", album_name)
            if not os.path.exists(path):
                os.makedirs(path)
                self.ids.new_album_name.text = ""
                self.refresh_spinners()

    def delete_selected_album(self, force=False):
        album = self.ids.delete_album_spinner.text
        if album != "Choisir un album à supprimer":
            path = os.path.join("albums", album)
            try:
                if force:
                    shutil.rmtree(path)
                else:
                    os.rmdir(path)
                self.ids.delete_album_spinner.text = "Choisir un album à supprimer"
                self.refresh_spinners()
            except Exception as e:
                print(f"Erreur lors de la suppression : {e}")

    def import_image_to_album(self):
        album = self.ids.import_album_spinner.text
        if album == "Choisir un album":
            return
        content = FileChooserListView(filters=["*.png", "*.jpg", "*.jpeg"])
        popup = Popup(title="Choisir une image", content=content, size_hint=(0.9, 0.9))

        def select_and_copy(*args):
            selection = content.selection
            if selection:
                dest_dir = os.path.join("albums", album)
                shutil.copy(selection[0], dest_dir)
                popup.dismiss()

        content.bind(on_submit=lambda *args: select_and_copy())
        popup.open()


class DatapadApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(AlbumScreen(name='album'))
        sm.add_widget(AdminScreen(name='admin'))
        return sm

    def validate_admin(self, entered_password):
        correct_password = "R2KT"  # ← Modifie ici le mot de passe
        if entered_password == correct_password:
            self.root.current = "admin"
            Popup(title="Accès accordé", content=Label(text="Bienvenue !"), size_hint=(.6, .3)).open()
        else:
            Popup(title="Erreur", content=Label(text="Mot de passe incorrect"), size_hint=(.6, .3)).open()


#Builder.load_file("datapad.kv")

if __name__ == '__main__':
    DatapadApp().run()
