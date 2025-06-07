import random

from kivy.core.text import LabelBase
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.factory import Factory

import shutil
import os


LabelBase.register(name="DroidOBesh", fn_regular="assets/fonts/DroidOBesh.otf")
LabelBase.register(name="AurebeshEnglish", fn_regular="assets/fonts/AurebeshEnglish.ttf")

class GlitchLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = "AurebeshEnglish"
        self._schedule_next_glitch()

    def _glitch(self, dt):
        # Random short glitch
        self.font_name = "DroidOBesh"
        duration = random.uniform(0.25, 0.7)
        Clock.schedule_once(self._restore_font, duration)

    def _restore_font(self, dt):
        self.font_name = "AurebeshEnglish"
        self._schedule_next_glitch()

    def _schedule_next_glitch(self):
        delay = random.uniform(2, 5)
        Clock.schedule_once(self._glitch, delay)

    def on_parent(self, instance, parent):
        if parent and not self._is_in_admin_screen():
            self.animate_glitch()

    def animate_glitch(label):
        anim = Animation(color=(0, 1, 1, 0.6), duration=0.2) + Animation(color=(0, 1, 1, 1), duration=0.2)
        anim.repeat = True
        anim.start(label)

    def _is_in_admin_screen(self):
        current = self
        while current:
            if current.__class__.__name__=='AdminScreen':
                return True
            current = current.parent
        return False

Factory.register('GlitchLabel', cls=GlitchLabel)

class LoginPopup(Popup):
    def validate(self, password):
        App.get_running_app().validate_admin(password)
        self.dismiss()


class MenuScreen(Screen):
    def on_enter(self):
        print("IDs dans MenuScreen :", self.ids)
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
    album_name = StringProperty("")

    def on_enter(self):
        self.ids.media_grid.clear_widgets()
        album_path = os.path.join("albums", self.album_name)
        for filename in os.listdir(album_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.abspath(os.path.join(album_path, filename))
                self.ids.media_grid.add_widget(Image(source=image_path, size_hint_y=None, height=200))


class AdminScreen(Screen):
    def on_pre_enter(self):
        self.refresh_spinners()

    def refresh_spinners(self):
        albums = self.get_album_list()
        self.ids.delete_album_spinner.values = albums
        selected_album = self.ids.import_album_spinner.text
        if selected_album and os.path.isdir(os.path.join("albums", selected_album)):
            image_dir = os.path.join("albums", selected_album)
            images = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            self.ids.delete_image_spinner.values = images
        else:
            self.ids.delete_image_spinner.values = []
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
        self.ids.admin_status_label.text = f"Image ajouter avec succès."
        popup.open()

    def delete_selected_image(self):
        album = self.ids.import_album_spinner.text
        image_name = self.ids.delete_image_spinner.text
        if album == "Choisir un album" or image_name == "Choisir une image à supprimer":
            self.ids.admin_status_label.text = "Veuillez sélectionner un album et une image."
            return
        image_path = os.path.join("albums", album, image_name)
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                self.ids.admin_status_label.text = f"Image '{image_name}' supprimée avec succès."
                self.refresh_spinners()
            else:
                self.ids.admin_status_label.text = "Image introuvable."
        except Exception as e:
            print(f"Erreur lors de la suppression d'image : {e}")


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
