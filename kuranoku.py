import gi
import os
import re

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Gdk

class QuranViewer(Gtk.Window):
    def __init__(self, directory):
        super().__init__(title="Kuran-ı Kerim Görüntüleyici")
        self.set_default_size(850, 950)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.directory = directory
        self.files = self.get_images()
        self.index = 0
        self.zoom_factor = 1.0  

        if not self.files:
            print("Hata: Resim bulunamadı!")
            return

        # Ana Taşıyıcı
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.vbox)

        # Üst Panel
        self.top_bar = Gtk.HeaderBar()
        self.top_bar.set_show_close_button(True)
        self.top_bar.set_title("KURAN-I KERİM OKU - mobilturka")
        self.set_titlebar(self.top_bar)

        # Üst Bar Kontrolleri
        self.create_top_controls()

        # Sayfa Bilgisi Etiketi
        self.label = Gtk.Label()
        self.vbox.pack_start(self.label, False, False, 5)

        # Resim Alanı ve Kaydırma
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.image_widget = Gtk.Image()
        self.scrolled_window.add(self.image_widget)
        self.vbox.pack_start(self.scrolled_window, True, True, 0)

        # --- ALT NAVİGASYON PANELİ ---
        self.create_bottom_navigation()

        # Eventler
        self.scrolled_window.connect("scroll-event", self.on_scroll)
        self.connect("key-press-event", self.on_key_press)
        
        self.update_view()

    def create_top_controls(self):
        # Sayfa git kutusu
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Sayfaya Git...")
        self.entry.set_width_chars(10)
        self.entry.connect("activate", self.on_jump_clicked)
        self.top_bar.pack_start(self.entry)

        # Zoom butonları
        zoom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(zoom_box.get_style_context(), "linked")

        btn_out = Gtk.Button.new_from_icon_name("zoom-out-symbolic", Gtk.IconSize.BUTTON)
        btn_out.connect("clicked", lambda x: self.change_zoom(-0.1))
        
        btn_reset = Gtk.Button.new_from_icon_name("zoom-original-symbolic", Gtk.IconSize.BUTTON)
        btn_reset.connect("clicked", lambda x: self.reset_zoom())

        btn_in = Gtk.Button.new_from_icon_name("zoom-in-symbolic", Gtk.IconSize.BUTTON)
        btn_in.connect("clicked", lambda x: self.change_zoom(0.1))

        zoom_box.pack_start(btn_out, False, False, 0)
        zoom_box.pack_start(btn_reset, False, False, 0)
        zoom_box.pack_start(btn_in, False, False, 0)
        self.top_bar.pack_end(zoom_box)

    def create_bottom_navigation(self):
        # Alt panel için taşıyıcı kutu
        self.nav_box = Gtk.ActionBar()
        self.vbox.pack_end(self.nav_box, False, False, 0)

        # Butonları ortalamak için bir kutu
        center_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # İlk Sayfa Butonu
        btn_first = Gtk.Button.new_from_icon_name("go-first-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        btn_first.set_tooltip_text("İlk Sayfa")
        btn_first.connect("clicked", lambda x: self.go_to_page(0))

        # Geri Butonu
        btn_prev = Gtk.Button.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        btn_prev.set_tooltip_text("Önceki Sayfa")
        btn_prev.connect("clicked", lambda x: self.change_page(-1))

        # İleri Butonu
        btn_next = Gtk.Button.new_from_icon_name("go-next-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        btn_next.set_tooltip_text("Sonraki Sayfa")
        btn_next.connect("clicked", lambda x: self.change_page(1))

        # Son Sayfa Butonu
        btn_last = Gtk.Button.new_from_icon_name("go-last-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        btn_last.set_tooltip_text("Son Sayfa")
        btn_last.connect("clicked", lambda x: self.go_to_page(len(self.files) - 1))

        # Butonları yerleştir
        center_box.pack_start(btn_first, False, False, 5)
        center_box.pack_start(btn_prev, False, False, 5)
        center_box.pack_start(btn_next, False, False, 5)
        center_box.pack_start(btn_last, False, False, 5)

        self.nav_box.set_center_widget(center_box)

    def go_to_page(self, page_index):
        self.index = page_index
        self.update_view()
        self.reset_scroll()

    def change_page(self, delta):
        new_index = self.index + delta
        # Sınırları kontrol et (Döngüsel geçiş isterseniz % kullanabilirsiniz)
        if 0 <= new_index < len(self.files):
            self.index = new_index
            self.update_view()
            self.reset_scroll()

    def reset_scroll(self):
        adj = self.scrolled_window.get_vadjustment()
        adj.set_value(adj.get_lower())

    def change_zoom(self, delta):
        self.zoom_factor = max(0.5, min(self.zoom_factor + delta, 3.0))
        self.update_view()

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.update_view()

    def on_scroll(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.direction == Gdk.ScrollDirection.UP:
                self.change_zoom(0.1)
            elif event.direction == Gdk.ScrollDirection.DOWN:
                self.change_zoom(-0.1)
            return True
        return False

    def update_view(self):
        if 0 <= self.index < len(self.files):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.files[self.index])
            window_height = self.get_size()[1]
            base_height = window_height - 180 # Alt bar için payı artırdık
            
            target_height = int(base_height * self.zoom_factor)
            aspect_ratio = pixbuf.get_width() / pixbuf.get_height()
            new_width = int(target_height * aspect_ratio)
            
            scaled_pixbuf = pixbuf.scale_simple(new_width, target_height, GdkPixbuf.InterpType.BILINEAR)
            self.image_widget.set_from_pixbuf(scaled_pixbuf)

            zoom_perc = int(self.zoom_factor * 100)
            self.label.set_markup(f"<span size='large'>Sayfa: <b>{self.index + 1} / {len(self.files)}</b>  |  Zoom: <b>%{zoom_perc}</b></span>")

    def on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK

        if not self.entry.is_focus():
            if keyname == "Right": self.change_page(1)
            elif keyname == "Left": self.change_page(-1)
            elif ctrl and keyname == "plus": self.change_zoom(0.1)
            elif ctrl and keyname == "minus": self.change_zoom(-0.1)
            elif ctrl and keyname == "0": self.reset_zoom()
        
        if keyname == "Escape": Gtk.main_quit()

    def on_jump_clicked(self, widget):
        text = self.entry.get_text()
        if text.isdigit() and 1 <= int(text) <= len(self.files):
            self.go_to_page(int(text) - 1)
            self.entry.set_text("")
            self.image_widget.grab_focus()

    def get_images(self):
        try:
            files = [f for f in os.listdir(self.directory) if f.startswith("image") and f.endswith(".png")]
            files.sort(key=lambda var: [int(x) if x.isdigit() else x for x in re.split('([0-9]+)', var)])
            return [os.path.join(self.directory, f) for f in files]
        except: return []

if __name__ == "__main__":
    RESIM_DIZINI = "/opt/KuranOku/Diyanet"
    win = QuranViewer(RESIM_DIZINI)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()