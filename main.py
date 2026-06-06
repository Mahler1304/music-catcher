"""
YTGrab — A clean, ad-free YouTube audio/video downloader.
Built with KivyMD 2.0 + yt-dlp.
"""

import os
import json
import threading
from datetime import datetime
from pathlib import Path
from functools import partial

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.screenmanager import FadeTransition
from kivy.properties import StringProperty
from kivy.metrics import dp
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.list import (
    MDListItem,
    MDListItemHeadlineText,
    MDListItemSupportingText,
    MDListItemLeadingIcon,
    MDListItemTrailingIcon,
)
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
)
from kivymd.uix.button import MDButton, MDButtonText

import yt_dlp

# ─── Paths ────────────────────────────────────────────────────────────────────
if platform == "android":
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.INTERNET,
    ])
    DOWNLOAD_DIR = "/storage/emulated/0/Download/YTGrab"
else:
    DOWNLOAD_DIR = str(Path.home() / "Downloads" / "YTGrab")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

DATA_DIR = os.path.join(
    os.environ.get("ANDROID_APP_PATH", os.path.dirname(os.path.abspath(__file__))),
    "data",
)
os.makedirs(DATA_DIR, exist_ok=True)
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")


# ─── KV Layout (KivyMD 2.0 syntax) ──────────────────────────────────────────
KV = """
<VideoInfoCard>:
    orientation: "vertical"
    adaptive_height: True
    padding: dp(16)
    spacing: dp(10)
    md_bg_color: app.theme_cls.surfaceContainerColor
    radius: [dp(16), dp(16), dp(16), dp(16)]

    FitImage:
        source: root.thumbnail_url
        size_hint_y: None
        height: dp(190)
        radius: [dp(12), dp(12), dp(12), dp(12)]

    MDLabel:
        text: root.video_title
        font_style: "Title"
        role: "medium"
        adaptive_height: True

    MDLabel:
        text: root.channel_name
        font_style: "Body"
        role: "medium"
        theme_text_color: "Secondary"
        adaptive_height: True

    MDLabel:
        text: root.duration_text
        font_style: "Label"
        role: "small"
        theme_text_color: "Hint"
        adaptive_height: True


MDScreenManager:
    id: sm

    MDScreen:
        name: "splash"
        md_bg_color: app.theme_cls.backgroundColor

        MDBoxLayout:
            id: splash_box
            orientation: "vertical"
            adaptive_height: True
            spacing: dp(14)
            pos_hint: {"center_x": .5, "center_y": .5}
            size_hint: None, None
            width: dp(320)
            opacity: 0

            MDIcon:
                icon: "music-circle"
                halign: "center"
                theme_font_size: "Custom"
                font_size: dp(96)
                theme_text_color: "Custom"
                text_color: app.theme_cls.primaryColor
                size_hint_y: None
                height: dp(110)

            MDLabel:
                id: greet_label
                text: "Hello Francisco"
                halign: "center"
                font_style: "Display"
                role: "small"
                adaptive_height: True

            MDLabel:
                text: "M.C. — Music Catcher"
                halign: "center"
                font_style: "Title"
                role: "medium"
                theme_text_color: "Custom"
                text_color: app.theme_cls.primaryColor
                adaptive_height: True

    MDScreen:
        name: "main"

        MDBoxLayout:
            orientation: "vertical"

            MDTopAppBar:
                type: "small"
                pos_hint: {"top": 1}

                MDTopAppBarTitle:
                    text: "M.C. — Music Catcher"

                MDTopAppBarTrailingButtonContainer:
                    MDActionTopAppBarButton:
                        icon: "history"
                        on_release: app.go_history()

            ScrollView:
                MDBoxLayout:
                    orientation: "vertical"
                    padding: dp(20)
                    spacing: dp(16)
                    adaptive_height: True

                    MDTextField:
                        id: url_field
                        mode: "outlined"
                        size_hint_x: 1
                        multiline: False
                        write_tab: False
                        on_text_validate: app.fetch_info()

                        MDTextFieldLeadingIcon:
                            icon: "youtube"

                        MDTextFieldHintText:
                            text: "Paste YouTube link here"

                    MDButton:
                        style: "filled"
                        size_hint_x: 1
                        height: dp(48)
                        on_press: app.fetch_info()

                        MDButtonText:
                            text: "Fetch Video Info"

                    VideoInfoCard:
                        id: info_card
                        opacity: 0
                        disabled: True
                        size_hint_y: None
                        height: self.minimum_height if self.opacity else 0

                    MDBoxLayout:
                        id: format_box
                        orientation: "vertical"
                        adaptive_height: True
                        spacing: dp(2)
                        opacity: 0
                        disabled: True

                        MDLabel:
                            text: "Choose format"
                            font_style: "Title"
                            role: "small"
                            adaptive_height: True

                        MDDivider:

                    MDTextField:
                        id: filename_field
                        mode: "outlined"
                        size_hint_x: 1
                        opacity: 0
                        disabled: True

                        MDTextFieldLeadingIcon:
                            icon: "rename-box"

                        MDTextFieldHintText:
                            text: "Custom filename (optional)"

                    MDButton:
                        id: dl_btn
                        style: "filled"
                        size_hint_x: 1
                        height: dp(48)
                        opacity: 0
                        disabled: True
                        on_release: app.start_download()

                        MDButtonText:
                            text: "Download"

                    MDLabel:
                        id: status_label
                        text: ""
                        font_style: "Body"
                        role: "medium"
                        theme_text_color: "Secondary"
                        adaptive_height: True
                        halign: "center"

                    Widget:
                        size_hint_y: None
                        height: dp(60)

    MDScreen:
        name: "history"

        MDBoxLayout:
            orientation: "vertical"

            MDTopAppBar:
                type: "small"
                pos_hint: {"top": 1}

                MDTopAppBarLeadingButtonContainer:
                    MDActionTopAppBarButton:
                        icon: "arrow-left"
                        on_release: app.go_main()

                MDTopAppBarTitle:
                    text: "History"

                MDTopAppBarTrailingButtonContainer:
                    MDActionTopAppBarButton:
                        icon: "delete-sweep"
                        on_release: app.clear_all_history()

            ScrollView:
                MDList:
                    id: history_list
"""


# ─── Custom widget ────────────────────────────────────────────────────────────
class VideoInfoCard(MDBoxLayout):
    thumbnail_url = StringProperty("")
    video_title = StringProperty("")
    channel_name = StringProperty("")
    duration_text = StringProperty("")


# ─── Format definitions ──────────────────────────────────────────────────────
FORMATS = [
    {"label": "MP3 — 128 kbps", "ext": "mp3", "type": "audio", "quality": "128"},
    {"label": "MP3 — 192 kbps", "ext": "mp3", "type": "audio", "quality": "192"},
    {"label": "MP3 — 320 kbps", "ext": "mp3", "type": "audio", "quality": "320"},
    {"label": "MP4 — 360p",     "ext": "mp4", "type": "video", "quality": "360"},
    {"label": "MP4 — 480p",     "ext": "mp4", "type": "video", "quality": "480"},
    {"label": "MP4 — 720p",     "ext": "mp4", "type": "video", "quality": "720"},
    {"label": "MP4 — 1080p",    "ext": "mp4", "type": "video", "quality": "1080"},
]


# ─── Helpers ──────────────────────────────────────────────────────────────────
def load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history(data: list):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fmt_seconds(sec) -> str:
    if sec is None:
        return ""
    sec = int(sec)
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def sanitize(name: str) -> str:
    return "".join(c if c.isalnum() or c in " _-." else "_" for c in name).strip()


# ─── App ──────────────────────────────────────────────────────────────────────
class YTGrabApp(MDApp):

    video_info = {}
    selected_format_idx = 0

    def build(self):
        self.title = "M.C. - Music Catcher"
        self.theme_cls.theme_style = "Dark"
        # Green-family palette. Swap to "Green", "Emerald", or "Forest"
        # for a more saturated green if you prefer.
        self.theme_cls.primary_palette = "Teal"
        self.root = Builder.load_string(KV)
        # Smooth fade between screens
        self.root.transition = FadeTransition(duration=0.35)
        self.root.current = "splash"
        return self.root

    def on_start(self):
        self.populate_history()
        # Kick off the intro animation a moment after the window is ready.
        Clock.schedule_once(self._play_splash, 0.3)

    def _play_splash(self, *args):
        box = self.root.ids.splash_box
        box.opacity = 0
        # Start slightly lower and small, then rise + fade in.
        box.y -= dp(30)

        fade_in = Animation(opacity=1, y=box.y + dp(30),
                            duration=0.7, t="out_cubic")
        fade_out = Animation(opacity=0, duration=0.5, t="in_cubic")

        def go_main(*_):
            self.root.current = "main"

        # fade in → hold ~1.2s → fade out → switch to main
        fade_in.bind(on_complete=lambda *a: Clock.schedule_once(
            lambda dt: fade_out.start(box), 1.2))
        fade_out.bind(on_complete=go_main)
        fade_in.start(box)

    # ── Navigation ───────────────────────────────────────────────────────
    def go_history(self):
        self.populate_history()
        self.root.current = "history"

    def go_main(self):
        self.root.current = "main"

    # ── Fetch video info ─────────────────────────────────────────────────
    def fetch_info(self):
        # Release the text field's focus first — on KivyMD 2.0 desktop a
        # focused MDTextField can swallow the next click, which is why the
        # button appeared dead.
        self.root.ids.url_field.focus = False
        url = self.root.ids.url_field.text.strip()
        print(f"[YTGrab] Fetch pressed. URL = '{url}'")
        if not url:
            self.root.ids.status_label.text = "Please enter a YouTube link"
            return

        self.root.ids.status_label.text = "Fetching video info…"
        self._set_controls_visible(False)
        threading.Thread(target=self._fetch_worker, args=(url,), daemon=True).start()

    def _fetch_worker(self, url):
        import traceback
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
        os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
        try:
            print(f"[YTGrab] Worker started for: {url}")
            ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            print(f"[YTGrab] Fetch OK — {info.get('title', '?')}")
            Clock.schedule_once(partial(self._on_info_fetched, info))
        except Exception as e:
            print(f"[YTGrab] Fetch FAILED:\n{traceback.format_exc()}")
            Clock.schedule_once(partial(self._set_status, f"Error: {str(e)[:200]}"))

    def _set_status(self, msg, *args):
        self.root.ids.status_label.text = msg

    def _on_info_fetched(self, info, *args):
        self.video_info = info
        card = self.root.ids.info_card
        card.thumbnail_url = info.get("thumbnail", "")
        card.video_title = info.get("title", "Unknown title")
        card.channel_name = info.get("channel", info.get("uploader", ""))
        card.duration_text = fmt_seconds(info.get("duration"))

        self.root.ids.filename_field.text = sanitize(info.get("title", "video"))
        self._build_format_options()
        self._set_controls_visible(True)
        self.root.ids.status_label.text = ""

    # ── Format radio buttons ─────────────────────────────────────────────
    def _build_format_options(self):
        box = self.root.ids.format_box
        # keep the label + divider (last 2 children); clear the rest
        while len(box.children) > 2:
            box.remove_widget(box.children[0])

        for i, fmt in enumerate(FORMATS):
            row = MDBoxLayout(adaptive_height=True, spacing=dp(8), padding=[0, dp(2)])
            cb = MDCheckbox(
                group="format",
                size_hint=(None, None),
                size=(dp(40), dp(40)),
                active=(i == 0),
                pos_hint={"center_y": 0.5},
            )
            cb.fmt_index = i
            cb.bind(active=self._on_format_select)

            ico = MDIcon(
                icon="music" if fmt["type"] == "audio" else "movie-open",
                theme_text_color="Custom",
                text_color=self.theme_cls.primaryColor,
                pos_hint={"center_y": 0.5},
                size_hint_x=None,
                width=dp(32),
            )
            lbl = MDLabel(
                text=fmt["label"],
                font_style="Body",
                role="large",
                adaptive_height=True,
                pos_hint={"center_y": 0.5},
            )
            row.add_widget(cb)
            row.add_widget(ico)
            row.add_widget(lbl)
            box.add_widget(row)

        self.selected_format_idx = 0

    def _on_format_select(self, checkbox, active):
        if active:
            self.selected_format_idx = checkbox.fmt_index

    # ── Download ─────────────────────────────────────────────────────────
    def start_download(self):
        if not self.video_info:
            return
        fmt = FORMATS[self.selected_format_idx]
        name = sanitize(self.root.ids.filename_field.text) or "download"

        self.root.ids.dl_btn.disabled = True
        self.root.ids.status_label.text = "Starting download…"

        url = self.video_info.get("webpage_url", self.root.ids.url_field.text.strip())
        threading.Thread(
            target=self._download_worker, args=(url, fmt, name), daemon=True
        ).start()

    def _download_worker(self, url, fmt, name):
        import traceback
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
        os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

        out_template = os.path.join(DOWNLOAD_DIR, f"{name}.%(ext)s")

        def hook(d):
            if d["status"] == "downloading":
                pct = d.get("_percent_str", "?").strip()
                Clock.schedule_once(partial(self._set_status, f"Downloading… {pct}"))
            elif d["status"] == "finished":
                Clock.schedule_once(partial(self._set_status, "Processing…"))

        ydl_opts = {
            "outtmpl": out_template,
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
        }
        if fmt["type"] == "audio":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": fmt["quality"],
                }],
            })
        else:
            h = fmt["quality"]
            ydl_opts.update({
                "format": f"bestvideo[height<={h}]+bestaudio/best[height<={h}]",
                "merge_output_format": "mp4",
            })

        try:
            print(f"[YTGrab] Downloading: {fmt['label']}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            entry = {
                "title": self.video_info.get("title", ""),
                "url": url,
                "thumbnail": self.video_info.get("thumbnail", ""),
                "channel": self.video_info.get("channel", ""),
                "format": fmt["label"],
                "filename": name,
                "date": datetime.now().isoformat(),
            }
            hist = load_history()
            hist.insert(0, entry)
            save_history(hist)

            print(f"[YTGrab] Done: {name}.{fmt['ext']}")
            Clock.schedule_once(
                partial(self._set_status, f"Saved: Downloads/YTGrab/{name}.{fmt['ext']}")
            )
            Clock.schedule_once(self._reenable_dl)
        except Exception as e:
            print(f"[YTGrab] Download FAILED:\n{traceback.format_exc()}")
            Clock.schedule_once(partial(self._set_status, f"Error: {str(e)[:200]}"))
            Clock.schedule_once(self._reenable_dl)

    def _reenable_dl(self, *args):
        self.root.ids.dl_btn.disabled = False

    # ── Visibility toggle ────────────────────────────────────────────────
    def _set_controls_visible(self, visible: bool):
        v = 1 if visible else 0
        ids = self.root.ids
        for w in (ids.info_card, ids.format_box, ids.filename_field, ids.dl_btn):
            w.opacity = v
            w.disabled = not visible

    # ── History ──────────────────────────────────────────────────────────
    def populate_history(self):
        lst = self.root.ids.history_list
        lst.clear_widgets()
        history = load_history()

        if not history:
            empty = MDListItem(MDListItemHeadlineText(text="No downloads yet"))
            lst.add_widget(empty)
            return

        for i, entry in enumerate(history):
            item = MDListItem(
                MDListItemLeadingIcon(
                    icon="music" if "MP3" in entry.get("format", "") else "movie-open"
                ),
                MDListItemHeadlineText(text=entry.get("title", "Untitled")[:50]),
                MDListItemSupportingText(
                    text=f"{entry.get('format', '')}  ·  {entry.get('date', '')[:10]}"
                ),
                MDListItemTrailingIcon(icon="delete-outline"),
            )
            item.entry = entry
            item.index = i
            item.bind(on_release=self._on_history_tap)
            # the trailing icon is the last child added inside MDListItem
            for child in item.children:
                if isinstance(child, MDListItemTrailingIcon):
                    child.bind(on_release=partial(self._delete_history_entry, i))
            lst.add_widget(item)

    def _on_history_tap(self, item):
        self.root.ids.url_field.text = item.entry.get("url", "")
        self.root.current = "main"
        self.root.ids.status_label.text = "Link loaded — tap Fetch Video Info"

    def _delete_history_entry(self, index, *args):
        hist = load_history()
        if 0 <= index < len(hist):
            hist.pop(index)
            save_history(hist)
            self.populate_history()

    def clear_all_history(self):
        self._dialog = MDDialog(
            MDDialogHeadlineText(text="Clear all history?"),
            MDDialogSupportingText(text="This cannot be undone."),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Cancel"),
                    style="text",
                    on_release=lambda x: self._dialog.dismiss(),
                ),
                MDButton(
                    MDButtonText(text="Clear"),
                    style="filled",
                    on_release=lambda x: self._do_clear_all(),
                ),
                spacing=dp(8),
            ),
        )
        self._dialog.open()

    def _do_clear_all(self):
        save_history([])
        self.populate_history()
        self._dialog.dismiss()


if __name__ == "__main__":
    YTGrabApp().run()
