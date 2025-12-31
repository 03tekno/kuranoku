import gi
import os
import re
import sys

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GdkPixbuf, Gdk, Gio, GLib

class QuranViewer(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("KURAN-I KERİM OKU")
        self.set_default_size(850, 950)

        # Değişkenler
        self.directory = "/opt/KuranOku/Diyanet"
        self.files = self.get_images()
        self.index = 0
        self.zoom_factor = 1.0

        # UI Kurulumu
        self.setup_ui()
        self.setup_controllers()

        if self.files:
            GLib.timeout_add(150, self.update_view)

    def setup_ui(self):
        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.main_vbox)

        # --- ÜST PANEL (HeaderBar) ---
        self.header_bar = Gtk.HeaderBar()
        self.set_titlebar(self.header_bar)

        # SOL: Sayfaya Git
        self.entry = Gtk.Entry(placeholder_text="Sayfa No...")
        self.entry.set_width_chars(8)
        self.entry.connect("activate", self.on_jump_clicked)
        self.header_bar.pack_start(self.entry)

        # SAĞ: Hakkında Butonu (En Sağda)
        btn_about = Gtk.Button.new_from_icon_name("help-about-symbolic")
        btn_about.set_tooltip_text("Uygulama Hakkında")
        btn_about.connect("clicked", self.on_about_clicked)
        self.header_bar.pack_end(btn_about)

        # SAĞ: Zoom Butonları
        zoom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        zoom_box.add_css_class("linked")

        btn_out = Gtk.Button.new_from_icon_name("zoom-out-symbolic")
        btn_out.connect("clicked", self.on_zoom_out_clicked)
        
        btn_reset = Gtk.Button.new_from_icon_name("zoom-original-symbolic")
        btn_reset.connect("clicked", self.on_zoom_reset_clicked)

        btn_in = Gtk.Button.new_from_icon_name("zoom-in-symbolic")
        btn_in.connect("clicked", self.on_zoom_in_clicked)

        zoom_box.append(btn_out)
        zoom_box.append(btn_reset)
        zoom_box.append(btn_in)
        self.header_bar.pack_end(zoom_box)

        # --- DURUM BİLGİSİ ---
        self.status_label = Gtk.Label(margin_top=5, margin_bottom=5)
        self.status_label.set_use_markup(True)
        self.main_vbox.append(self.status_label)

        # --- RESİM ALANI ---
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_vexpand(True)
        
        self.image_widget = Gtk.Image()
        self.image_widget.set_pixel_size(-1) 
        
        self.img_center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.img_center_box.set_halign(Gtk.Align.CENTER)
        self.img_center_box.append(self.image_widget)
        
        self.scrolled_window.set_child(self.img_center_box)
        self.main_vbox.append(self.scrolled_window)

        self.setup_bottom_navigation()

    def on_about_clicked(self, btn):
        # Hakkında Penceresi Oluşturma
        about = Gtk.AboutDialog()
        about.set_transient_for(self)
        about.set_modal(True)
        
        about.set_program_name("Kuran-ı Kerim Görüntüleyici")
        about.set_version("1.0.0")
        about.set_authors(["mobilturka"])
        about.set_copyright("© 2026 mobilturka")
        about.set_comments("GTK4 ile geliştirilmiş, hızlı ve modern Kur'an-ı Kerim okuma uygulaması.")
        about.set_website("https://github.com/03tekno")
        about.set_license_type(Gtk.License.GPL_3_0)
        # Sistem ikonunu kullan
        about.set_logo_icon_name("accessories-dictionary")
        
        about.present()

    def update_view(self):
        if not self.files: return False
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.files[self.index])
        win_h = self.get_height()
        if win_h < 100: win_h = 900
        base_h = win_h - 200
        target_h = int(base_h * self.zoom_factor)
        ratio = pixbuf.get_width() / pixbuf.get_height()
        target_w = int(target_h * ratio)
        scaled = pixbuf.scale_simple(target_w, target_h, GdkPixbuf.InterpType.BILINEAR)
        texture = Gdk.Texture.new_for_pixbuf(scaled)
        self.image_widget.set_from_paintable(texture)
        self.image_widget.set_size_request(target_w, target_h)
        self.status_label.set_markup(f"Sayfa: <b>{self.index + 1} / {len(self.files)}</b> | Zoom: <b>%{int(self.zoom_factor*100)}</b>")
        return False

    def on_jump_clicked(self, entry):
        text = entry.get_text()
        if text.isdigit():
            target_page = int(text) - 1
            if 0 <= target_page < len(self.files):
                self.index = target_page
                self.update_view()
                self.scrolled_window.get_vadjustment().set_value(0)
                entry.set_text("")
                self.set_focus(None)

    def on_zoom_in_clicked(self, btn):
        self.zoom_factor = min(self.zoom_factor + 0.1, 4.0)
        self.update_view()

    def on_zoom_out_clicked(self, btn):
        self.zoom_factor = max(self.zoom_factor - 0.1, 0.2)
        self.update_view()

    def on_zoom_reset_clicked(self, btn):
        self.zoom_factor = 1.0
        self.update_view()

    def setup_bottom_navigation(self):
        action_bar = Gtk.ActionBar()
        self.main_vbox.append(action_bar)
        box = Gtk.Box(spacing=10)
        btns = [
            ("go-first-symbolic", lambda x: self.go_to_page(0)),
            ("go-previous-symbolic", lambda x: self.change_page(-1)),
            ("go-next-symbolic", lambda x: self.change_page(1)),
            ("go-last-symbolic", lambda x: self.go_to_page(len(self.files)-1))
        ]
        for icon, cb in btns:
            b = Gtk.Button.new_from_icon_name(icon)
            b.connect("clicked", cb)
            box.append(b)
        action_bar.set_center_widget(box)

    def change_page(self, delta):
        new_idx = self.index + delta
        if 0 <= new_idx < len(self.files):
            self.index = new_idx
            self.update_view()
            self.scrolled_window.get_vadjustment().set_value(0)

    def go_to_page(self, p):
        self.index = p
        self.update_view()
        self.scrolled_window.get_vadjustment().set_value(0)

    def setup_controllers(self):
        kc = Gtk.EventControllerKey()
        kc.connect("key-pressed", self.on_key_pressed)
        self.add_controller(kc)
        sc = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.VERTICAL)
        sc.connect("scroll", self.on_scroll)
        self.scrolled_window.add_controller(sc)

    def on_scroll(self, ctrl, dx, dy):
        state = ctrl.get_current_event_state()
        if state & Gdk.ModifierType.CONTROL_MASK:
            if dy < 0: self.on_zoom_in_clicked(None)
            else: self.on_zoom_out_clicked(None)
            return True
        return False

    def on_key_pressed(self, ctrl, keyval, keycode, state):
        if keyval == Gdk.KEY_Right: self.change_page(1)
        elif keyval == Gdk.KEY_Left: self.change_page(-1)
        return False

    def get_images(self):
        if not os.path.exists(self.directory): return []
        f = [f for f in os.listdir(self.directory) if f.lower().endswith(('.png', '.jpg'))]
        f.sort(key=lambda v: [int(x) if x.isdigit() else x for x in re.split('([0-9]+)', v)])
        return [os.path.join(self.directory, img) for img in f]

class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.mobilturka.quran.final")
    def do_activate(self):
        win = QuranViewer(application=self)
        win.present()

if __name__ == "__main__":
    app = App()
    app.run(sys.argv)