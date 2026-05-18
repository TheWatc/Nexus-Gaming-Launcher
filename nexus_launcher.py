"""
╔══════════════════════════════════════════╗
║        NEXUS LAUNCHER  v1.0              ║
║   Cyberpunk Mor-Pembe Masaüstü Başlatıcı ║
║                                          ║
║  Kurulum: pip install psutil             ║
║  Çalıştır: python nexus_launcher.py      ║
╚══════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, colorchooser
import subprocess
import threading
import time
import json
import os
import sys
import platform

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False
    print("UYARI: psutil bulunamadı. 'pip install psutil' çalıştırın.")

# ─── RENK PALETİ (Cyberpunk Mor-Pembe) ───────────────────────────────────────
C = {
    "bg":         "#0a0010",
    "bg2":        "#110020",
    "bg3":        "#1a0030",
    "panel":      "#12001f",
    "card":       "#1e0038",
    "card_hover": "#2a004d",
    "neon_pink":  "#002d61",
    "neon_purple":"#148bda",
    "neon_cyan":  "#00f5ff",
    "neon_yellow":"#ffe600",
    "text":       "#f0d0ff",
    "text_dim":   "#413c8d",
    "text_bright":"#ffffff",
    "border":     "#3d0070",
    "border_hot": "#1f1b5f",
    "green":      "#00ff88",
    "red":        "#ff2060",
    "orange":     "#ff8c00",
}

FONT_TITLE  = ("Courier New", 11, "bold")
FONT_MONO   = ("Courier New", 9)
FONT_MONO_S = ("Courier New", 8)
FONT_LABEL  = ("Courier New", 10, "bold")
FONT_BIG    = ("Courier New", 18, "bold")
FONT_ICON   = ("Segoe UI Emoji", 22)
FONT_ICON_S = ("Segoe UI Emoji", 16)

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nexus_config.json")

DEFAULT_APPS = [
    {"name": "Dosya Yöneticisi", "icon": "📁", "cmd": "explorer" if sys.platform=="win32" else "nautilus", "color": C["neon_cyan"]},
    {"name": "Tarayıcı",         "icon": "🌐", "cmd": "chrome" if sys.platform=="win32" else "firefox",   "color": C["neon_purple"]},
    {"name": "Terminal",         "icon": "⚡", "cmd": "cmd" if sys.platform=="win32" else "bash",          "color": C["neon_pink"]},
    {"name": "Notepad",          "icon": "📝", "cmd": "notepad" if sys.platform=="win32" else "gedit",     "color": C["neon_yellow"]},
    {"name": "Görev Yöneticisi", "icon": "📊", "cmd": "taskmgr" if sys.platform=="win32" else "gnome-system-monitor", "color": C["green"]},
    {"name": "Hesap Makinesi",   "icon": "🔢", "cmd": "calc" if sys.platform=="win32" else "gnome-calculator", "color": C["neon_cyan"]},
    {"name": "Ayarlar",          "icon": "⚙️",  "cmd": "ms-settings:" if sys.platform=="win32" else "gnome-control-center", "color": C["text_dim"]},
    {"name": "Fotoğraflar",      "icon": "🖼️",  "cmd": "ms-photos:" if sys.platform=="win32" else "eog",   "color": C["neon_pink"]},
]

# ─── CONFIG ───────────────────────────────────────────────────────────────────
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"apps": DEFAULT_APPS, "volume": 50, "wallpaper": "", "username": "KULLANICI"}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

# ─── YARDIMCI FONKSİYONLAR ───────────────────────────────────────────────────
def launch_app(cmd):
    try:
        if sys.platform == "win32":
            os.startfile(cmd) if os.path.exists(cmd) else subprocess.Popen(cmd, shell=True)
        else:
            subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        messagebox.showerror("Hata", f"Uygulama açılamadı:\n{e}")

def set_volume_system(vol):
    try:
        if sys.platform == "win32":
            # Windows için nircmd veya PowerShell
            subprocess.Popen(
                f'powershell -c "[audio]::Volume = {vol/100}"',
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        elif sys.platform == "darwin":
            subprocess.Popen(["osascript", "-e", f"set volume output volume {vol}"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["amixer", "-D", "pulse", "sset", "Master", f"{vol}%"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

def get_sys_info():
    if not PSUTIL_OK:
        return {"cpu": 0, "ram_used": 0, "ram_total": 8, "ram_pct": 0, "disk_pct": 0, "temp": None}
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    temp = None
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for k, v in temps.items():
                if v:
                    temp = v[0].current
                    break
    except:
        pass
    return {
        "cpu": cpu,
        "ram_used": ram.used / 1024**3,
        "ram_total": ram.total / 1024**3,
        "ram_pct": ram.percent,
        "disk_pct": disk.percent,
        "temp": temp,
    }

# ─── ANA UYGULAMA ─────────────────────────────────────────────────────────────
class NexusLauncher:
    def __init__(self):
        self.cfg = load_config()
        self.search_var = None
        self.app_cards = []
        self.running = True

        self.root = tk.Tk()
        self.root.title("NEXUS LAUNCHER")
        self.root.configure(bg=C["bg"])

        # Tam ekran
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", self.toggle_fullscreen)
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.fullscreen = True

        self.W = self.root.winfo_screenwidth()
        self.H = self.root.winfo_screenheight()

        self._build_ui()
        self._start_sys_monitor()
        self._start_clock()

        self.root.mainloop()
        self.running = False

    # ── UI İNŞASI ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Ana çerçeve
        self.main = tk.Frame(self.root, bg=C["bg"])
        self.main.pack(fill="both", expand=True)

        # ─ ÜSTTÜ BAR ─
        self._build_topbar()

        # ─ ORTA İÇERİK ─
        content = tk.Frame(self.main, bg=C["bg"])
        content.pack(fill="both", expand=True, padx=0, pady=0)

        # Sol panel: sistem bilgisi
        self._build_sidebar(content)

        # Sağ taraf: arama + app grid
        right = tk.Frame(content, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True)

        self._build_search(right)
        self._build_app_grid(right)

        # ─ ALT BAR ─
        self._build_bottombar()

    def _neon_label(self, parent, text, fg=None, font=None, **kw):
        fg = fg or C["neon_purple"]
        font = font or FONT_LABEL
        lbl = tk.Label(parent, text=text, fg=fg, bg=kw.pop("bg", C["bg"]),
                       font=font, **kw)
        return lbl

    # ── ÜSTTÜ BAR ─────────────────────────────────────────────────────────────
    def _build_topbar(self):
        bar = tk.Frame(self.main, bg=C["panel"], height=54)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Neon çizgi
        tk.Frame(bar, bg=C["neon_pink"], height=2).pack(fill="x", side="bottom")

        # Logo
        logo = tk.Label(bar, text="◈ NEXUS", fg=C["neon_pink"],
                        bg=C["panel"], font=("Courier New", 20, "bold"))
        logo.pack(side="left", padx=20)

        sub = tk.Label(bar, text="LAUNCHER v1.0", fg=C["text_dim"],
                       bg=C["panel"], font=FONT_MONO_S)
        sub.place(x=170, y=34)

        # Saat (sağ)
        self.clock_var = tk.StringVar(value="00:00:00")
        self.date_var  = tk.StringVar(value="")
        right_frame = tk.Frame(bar, bg=C["panel"])
        right_frame.pack(side="right", padx=20)

        self.username_lbl = tk.Label(right_frame,
                                     text=f"▸ {self.cfg.get('username','KULLANICI')}",
                                     fg=C["neon_cyan"], bg=C["panel"], font=FONT_MONO)
        self.username_lbl.pack(side="left", padx=(0,20))

        tk.Label(right_frame, textvariable=self.date_var,
                 fg=C["text_dim"], bg=C["panel"], font=FONT_MONO_S).pack()
        tk.Label(right_frame, textvariable=self.clock_var,
                 fg=C["neon_yellow"], bg=C["panel"],
                 font=("Courier New", 16, "bold")).pack()

        # Kapatma / minimize butonları
        btn_frame = tk.Frame(bar, bg=C["panel"])
        btn_frame.pack(side="right", padx=5)

        self._topbtn(btn_frame, "⊡", C["text_dim"], self.toggle_fullscreen)
        self._topbtn(btn_frame, "✕", C["neon_pink"], self.root.destroy)

    def _topbtn(self, parent, txt, color, cmd):
        b = tk.Label(parent, text=txt, fg=color, bg=C["panel"],
                     font=("Courier New", 14, "bold"), cursor="hand2", padx=8)
        b.pack(side="left")
        b.bind("<Button-1>", lambda e: cmd())
        b.bind("<Enter>", lambda e: b.config(fg=C["text_bright"]))
        b.bind("<Leave>", lambda e: b.config(fg=color))

    # ── SOL SİDEBAR ───────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=C["panel"], width=260)
        sidebar.pack(side="left", fill="y", padx=0, pady=0)
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg=C["border"], width=2).pack(side="right", fill="y")

        inner = tk.Frame(sidebar, bg=C["panel"])
        inner.pack(fill="both", expand=True, padx=14, pady=14)

        # ── SİSTEM BİLGİSİ ──
        self._section_title(inner, "◈ SİSTEM")

        self.cpu_var  = tk.StringVar(value="CPU  : ---%")
        self.ram_var  = tk.StringVar(value="RAM  : ---")
        self.disk_var = tk.StringVar(value="DISK : ---%")
        self.temp_var = tk.StringVar(value="TEMP : ---")

        self.cpu_bar  = self._stat_row(inner, self.cpu_var,  C["neon_pink"])
        self.ram_bar  = self._stat_row(inner, self.ram_var,  C["neon_purple"])
        self.disk_bar = self._stat_row(inner, self.disk_var, C["neon_cyan"])
        self.temp_bar = self._stat_row(inner, self.temp_var, C["neon_yellow"])

        # ── SES KONTROLÜ ──
        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=14)
        self._section_title(inner, "◈ SES")

        vol_row = tk.Frame(inner, bg=C["panel"])
        vol_row.pack(fill="x", pady=4)

        self.vol_icon_var = tk.StringVar(value="🔊")
        vol_icon = tk.Label(vol_row, textvariable=self.vol_icon_var,
                            font=FONT_ICON_S, bg=C["panel"], fg=C["text_bright"])
        vol_icon.pack(side="left")

        self.vol_var = tk.IntVar(value=self.cfg.get("volume", 50))
        vol_slider = tk.Scale(
            vol_row, from_=0, to=100, orient="horizontal",
            variable=self.vol_var, command=self._on_volume,
            bg=C["panel"], fg=C["neon_purple"], troughcolor=C["bg3"],
            highlightthickness=0, relief="flat", sliderlength=14,
            activebackground=C["neon_pink"], length=150
        )
        vol_slider.pack(side="left", padx=6)

        self.vol_pct = tk.Label(vol_row, textvariable=tk.StringVar(value=""),
                                fg=C["neon_yellow"], bg=C["panel"], font=FONT_MONO_S)
        self.vol_pct.pack(side="left")
        self._update_vol_label()

        # ── HIZLI EYLEMLER ──
        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=14)
        self._section_title(inner, "◈ EYLEMLER")

        actions = [
            ("+ Uygulama Ekle",  C["neon_pink"],   self._add_app_dialog),
            ("✎ Adı Değiştir",   C["neon_purple"], self._rename_dialog),
            ("⟳ Yenile",         C["neon_cyan"],   self._refresh_grid),
        ]
        for label, color, cmd in actions:
            self._action_btn(inner, label, color, cmd)

        # ── PLATFORM ──
        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=14)
        plat = platform.node()[:18]
        tk.Label(inner, text=f"🖥  {plat}", fg=C["text_dim"],
                 bg=C["panel"], font=FONT_MONO_S).pack(anchor="w")
        tk.Label(inner, text=f"🐍  Python {sys.version[:6]}",
                 fg=C["text_dim"], bg=C["panel"], font=FONT_MONO_S).pack(anchor="w")

    def _section_title(self, parent, text):
        tk.Label(parent, text=text, fg=C["neon_purple"],
                 bg=C["panel"], font=FONT_TITLE).pack(anchor="w", pady=(0,6))

    def _stat_row(self, parent, var, bar_color):
        tk.Label(parent, textvariable=var, fg=C["text"], bg=C["panel"],
                 font=FONT_MONO_S, anchor="w").pack(fill="x")
        canvas = tk.Canvas(parent, height=4, bg=C["bg3"],
                           highlightthickness=0, bd=0)
        canvas.pack(fill="x", pady=(1,6))
        return canvas

    def _action_btn(self, parent, text, color, cmd):
        f = tk.Frame(parent, bg=C["card"], cursor="hand2")
        f.pack(fill="x", pady=3)
        lbl = tk.Label(f, text=text, fg=color, bg=C["card"],
                       font=FONT_MONO, padx=10, pady=6)
        lbl.pack(anchor="w")
        for w in (f, lbl):
            w.bind("<Button-1>", lambda e: cmd())
            w.bind("<Enter>",    lambda e, f=f, l=lbl, c=color: (
                f.config(bg=C["card_hover"]), l.config(bg=C["card_hover"], fg=C["text_bright"])))
            w.bind("<Leave>",    lambda e, f=f, l=lbl, c=color: (
                f.config(bg=C["card"]), l.config(bg=C["card"], fg=c)))

    # ── ARAMA ─────────────────────────────────────────────────────────────────
    def _build_search(self, parent):
        sf = tk.Frame(parent, bg=C["bg"])
        sf.pack(fill="x", padx=24, pady=(18, 10))

        # Arama kutusu çerçevesi
        border = tk.Frame(sf, bg=C["neon_purple"], padx=2, pady=2)
        border.pack(side="left", fill="x", expand=True)

        inner = tk.Frame(border, bg=C["card"])
        inner.pack(fill="both")

        lbl = tk.Label(inner, text="⌕ ", fg=C["neon_pink"],
                       bg=C["card"], font=("Courier New", 13, "bold"))
        lbl.pack(side="left", padx=(8, 0))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search)

        entry = tk.Entry(inner, textvariable=self.search_var,
                         bg=C["card"], fg=C["text_bright"],
                         insertbackground=C["neon_pink"],
                         relief="flat", font=("Courier New", 13),
                         bd=0)
        entry.pack(side="left", fill="x", expand=True, padx=6, pady=10)

        clear_btn = tk.Label(inner, text="✕", fg=C["text_dim"],
                             bg=C["card"], font=FONT_MONO, cursor="hand2")
        clear_btn.pack(side="right", padx=8)
        clear_btn.bind("<Button-1>", lambda e: self.search_var.set(""))

        self.result_lbl = tk.Label(sf, text="", fg=C["text_dim"],
                                   bg=C["bg"], font=FONT_MONO_S)
        self.result_lbl.pack(side="left", padx=12)

    # ── APP GRİD ──────────────────────────────────────────────────────────────
    def _build_app_grid(self, parent):
        # Scrollable frame
        container = tk.Frame(parent, bg=C["bg"])
        container.pack(fill="both", expand=True, padx=24, pady=(0, 0))

        canvas = tk.Canvas(container, bg=C["bg"], highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                 command=canvas.yview, bg=C["bg3"])
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = tk.Frame(canvas, bg=C["bg"])
        self.grid_window = canvas.create_window((0, 0), window=self.grid_frame,
                                                anchor="nw")

        self.grid_frame.bind("<Configure>",
                             lambda e: canvas.configure(
                                 scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(
                        self.grid_window, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        self.app_canvas = canvas
        self._refresh_grid()

    def _refresh_grid(self, filter_text=""):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.app_cards = []

        apps = self.cfg["apps"]
        if filter_text:
            apps = [a for a in apps if filter_text.lower() in a["name"].lower()]

        self.result_lbl.config(text=f"{len(apps)} uygulama")

        cols = max(2, (self.W - 320) // 160)
        for i, app in enumerate(apps):
            row, col = divmod(i, cols)
            card = self._make_card(self.grid_frame, app, i)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.grid_frame.columnconfigure(col, weight=1)

        # "Boş" placeholder
        if not apps:
            tk.Label(self.grid_frame, text="Sonuç bulunamadı 🔍",
                     fg=C["text_dim"], bg=C["bg"],
                     font=FONT_LABEL).grid(row=0, column=0, padx=40, pady=40)

    def _make_card(self, parent, app, idx):
        color = app.get("color", C["neon_purple"])
        card = tk.Frame(parent, bg=C["card"], width=140, height=120,
                        cursor="hand2")
        card.pack_propagate(False)

        # Neon üst çizgi
        accent = tk.Frame(card, bg=color, height=3)
        accent.pack(fill="x")

        # İkon
        icon_lbl = tk.Label(card, text=app["icon"], font=FONT_ICON,
                            bg=C["card"], fg=color)
        icon_lbl.pack(pady=(10, 4))

        # İsim
        name_lbl = tk.Label(card, text=app["name"], font=FONT_MONO_S,
                            bg=C["card"], fg=C["text"],
                            wraplength=130, justify="center")
        name_lbl.pack()

        # Sağ tık menüsü
        def right_click(e, a=app, i=idx):
            m = tk.Menu(self.root, tearoff=0,
                        bg=C["card"], fg=C["text"],
                        activebackground=C["neon_purple"],
                        activeforeground=C["text_bright"],
                        font=FONT_MONO_S)
            m.add_command(label="▶ Aç",    command=lambda: launch_app(a["cmd"]))
            m.add_command(label="✎ Düzenle", command=lambda: self._edit_app(i))
            m.add_separator()
            m.add_command(label="🗑 Kaldır", command=lambda: self._remove_app(i))
            m.post(e.x_root, e.y_root)

        def enter(e):
            card.config(bg=C["card_hover"])
            for w in card.winfo_children():
                if isinstance(w, tk.Label):
                    w.config(bg=C["card_hover"])
            accent.config(bg=C["text_bright"])

        def leave(e):
            card.config(bg=C["card"])
            for w in card.winfo_children():
                if isinstance(w, tk.Label):
                    w.config(bg=C["card"])
            accent.config(bg=color)

        cmd = app["cmd"]
        for w in [card, icon_lbl, name_lbl, accent]:
            w.bind("<Button-1>",         lambda e, c=cmd: launch_app(c))
            w.bind("<Button-3>",         right_click)
            w.bind("<Enter>",            enter)
            w.bind("<Leave>",            leave)

        self.app_cards.append(card)
        return card

    # ── ALT BAR ───────────────────────────────────────────────────────────────
    def _build_bottombar(self):
        bar = tk.Frame(self.main, bg=C["panel"], height=32)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Frame(bar, bg=C["neon_purple"], height=1).pack(fill="x")

        tips = [
            ("ESC", "Tam Ekran Aç/Kapat"),
            ("Sağ Tık", "Uygulama Menüsü"),
            ("F11", "Tam Ekran"),
        ]
        tip_f = tk.Frame(bar, bg=C["panel"])
        tip_f.pack(side="left", padx=16)
        for key, desc in tips:
            tk.Label(tip_f, text=f"[{key}]", fg=C["neon_pink"],
                     bg=C["panel"], font=FONT_MONO_S).pack(side="left", padx=2)
            tk.Label(tip_f, text=desc+"  ", fg=C["text_dim"],
                     bg=C["panel"], font=FONT_MONO_S).pack(side="left")

        self.status_var = tk.StringVar(value="● HAZIR")
        tk.Label(bar, textvariable=self.status_var,
                 fg=C["green"], bg=C["panel"], font=FONT_MONO_S).pack(side="right", padx=16)

    # ── EVENTLER ──────────────────────────────────────────────────────────────
    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def _on_search(self, *args):
        self._refresh_grid(self.search_var.get())

    def _on_volume(self, val):
        self._update_vol_label()
        v = int(float(val))
        self.cfg["volume"] = v
        icon = "🔇" if v==0 else "🔉" if v<50 else "🔊"
        self.vol_icon_var.set(icon)
        set_volume_system(v)
        save_config(self.cfg)

    def _update_vol_label(self):
        v = self.vol_var.get()
        self.vol_pct.config(text=f" {v}%")

    # ── DİYALOGLAR ────────────────────────────────────────────────────────────
    def _add_app_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Uygulama Ekle")
        dlg.configure(bg=C["bg2"])
        dlg.geometry("420x340")
        dlg.grab_set()

        tk.Label(dlg, text="◈ UYGULAMA EKLE", fg=C["neon_pink"],
                 bg=C["bg2"], font=FONT_BIG).pack(pady=16)

        fields = {}
        labels = [("İsim",     "Ad"), ("Komut / Yol", "Cmd"),
                  ("İkon (emoji)", "İkon")]
        for text, key in labels:
            row = tk.Frame(dlg, bg=C["bg2"])
            row.pack(fill="x", padx=24, pady=6)
            tk.Label(row, text=text, fg=C["text_dim"], bg=C["bg2"],
                     font=FONT_MONO, width=16, anchor="w").pack(side="left")
            var = tk.StringVar()
            e = tk.Entry(row, textvariable=var, bg=C["card"],
                         fg=C["text_bright"], insertbackground=C["neon_pink"],
                         relief="flat", font=FONT_MONO, bd=4)
            e.pack(side="left", fill="x", expand=True)
            fields[key] = var

        fields["İkon"].set("🚀")

        def confirm():
            name = fields["Ad"].get().strip()
            cmd  = fields["Cmd"].get().strip()
            icon = fields["İkon"].get().strip() or "🚀"
            if not name or not cmd:
                messagebox.showwarning("Eksik", "İsim ve Komut zorunludur!", parent=dlg)
                return
            self.cfg["apps"].append({"name": name, "cmd": cmd, "icon": icon,
                                     "color": C["neon_purple"]})
            save_config(self.cfg)
            self._refresh_grid()
            self.status_var.set(f"● {name} eklendi")
            dlg.destroy()

        tk.Button(dlg, text="✔ EKLE", command=confirm,
                  bg=C["neon_purple"], fg=C["text_bright"],
                  font=FONT_LABEL, relief="flat", padx=24, pady=8,
                  cursor="hand2").pack(pady=20)

    def _edit_app(self, idx):
        app = self.cfg["apps"][idx]
        dlg = tk.Toplevel(self.root)
        dlg.title("Düzenle")
        dlg.configure(bg=C["bg2"])
        dlg.geometry("420x300")
        dlg.grab_set()

        tk.Label(dlg, text="✎ DÜZENLE", fg=C["neon_yellow"],
                 bg=C["bg2"], font=FONT_BIG).pack(pady=14)

        fields = {}
        for text, key, val in [("İsim", "name", app["name"]),
                                ("Komut", "cmd", app["cmd"]),
                                ("İkon",  "icon", app["icon"])]:
            row = tk.Frame(dlg, bg=C["bg2"])
            row.pack(fill="x", padx=24, pady=6)
            tk.Label(row, text=text, fg=C["text_dim"], bg=C["bg2"],
                     font=FONT_MONO, width=10, anchor="w").pack(side="left")
            var = tk.StringVar(value=val)
            tk.Entry(row, textvariable=var, bg=C["card"], fg=C["text_bright"],
                     insertbackground=C["neon_pink"],
                     relief="flat", font=FONT_MONO, bd=4).pack(side="left", fill="x", expand=True)
            fields[key] = var

        def save():
            self.cfg["apps"][idx]["name"] = fields["name"].get().strip()
            self.cfg["apps"][idx]["cmd"]  = fields["cmd"].get().strip()
            self.cfg["apps"][idx]["icon"] = fields["icon"].get().strip()
            save_config(self.cfg)
            self._refresh_grid()
            dlg.destroy()

        tk.Button(dlg, text="✔ KAYDET", command=save,
                  bg=C["neon_yellow"], fg=C["bg"],
                  font=FONT_LABEL, relief="flat", padx=20, pady=8,
                  cursor="hand2").pack(pady=16)

    def _remove_app(self, idx):
        name = self.cfg["apps"][idx]["name"]
        if messagebox.askyesno("Kaldır", f'"{name}" kaldırılsın mı?'):
            self.cfg["apps"].pop(idx)
            save_config(self.cfg)
            self._refresh_grid()
            self.status_var.set(f"● {name} kaldırıldı")

    def _rename_dialog(self):
        name = simpledialog.askstring(
            "Kullanıcı Adı", "Yeni kullanıcı adı:",
            initialvalue=self.cfg.get("username", "KULLANICI"),
            parent=self.root
        )
        if name:
            self.cfg["username"] = name.upper()
            self.username_lbl.config(text=f"▸ {name.upper()}")
            save_config(self.cfg)

    # ── SİSTEM İZLEYİCİ ───────────────────────────────────────────────────────
    def _start_sys_monitor(self):
        if not PSUTIL_OK:
            return
        psutil.cpu_percent(interval=None)  # ilk çağrı warmup

        def loop():
            while self.running:
                info = get_sys_info()
                self.root.after(0, self._update_sys_ui, info)
                time.sleep(2)

        threading.Thread(target=loop, daemon=True).start()

    def _draw_bar(self, canvas, pct, color):
        canvas.delete("all")
        w = canvas.winfo_width()
        if w < 4:
            w = 230
        fill_w = int(w * pct / 100)
        canvas.create_rectangle(0, 0, w, 4, fill=C["bg3"], outline="")
        if fill_w > 0:
            c = color
            if pct > 85:
                c = C["red"]
            elif pct > 65:
                c = C["orange"]
            canvas.create_rectangle(0, 0, fill_w, 4, fill=c, outline="")

    def _update_sys_ui(self, info):
        self.cpu_var.set(f"CPU  : {info['cpu']:.0f}%")
        self.ram_var.set(
            f"RAM  : {info['ram_used']:.1f}/{info['ram_total']:.1f} GB")
        self.disk_var.set(f"DISK : {info['disk_pct']:.0f}%")
        if info["temp"]:
            self.temp_var.set(f"TEMP : {info['temp']:.0f}°C")
        else:
            self.temp_var.set("TEMP : N/A")

        self._draw_bar(self.cpu_bar,  info["cpu"],      C["neon_pink"])
        self._draw_bar(self.ram_bar,  info["ram_pct"],  C["neon_purple"])
        self._draw_bar(self.disk_bar, info["disk_pct"], C["neon_cyan"])

        # Status
        cpu = info["cpu"]
        if cpu > 85:
            self.status_var.set("● YÜKSEK CPU KULLANIMI")
        else:
            self.status_var.set("● HAZIR")

    # ── SAAT ──────────────────────────────────────────────────────────────────
    def _start_clock(self):
        days = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]

        def tick():
            now = time.localtime()
            self.clock_var.set(time.strftime("%H:%M:%S", now))
            self.date_var.set(
                f"{days[now.tm_wday]} {now.tm_mday:02d}.{now.tm_mon:02d}.{now.tm_year}"
            )
            if self.running:
                self.root.after(1000, tick)

        tick()


# ─── BAŞLAT ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    NexusLauncher()
