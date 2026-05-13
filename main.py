"""
Rock · Paper · Scissors — Android Multiplayer
Kivy app — works on Android and Desktop
Real TCP/IP over Wi-Fi between two devices
"""
import socket, threading, json
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle

Window.clearcolor = get_color_from_hex("#0a0a0f")

def gc(h): return get_color_from_hex(h)

BG      = gc("#0a0a0f")
CARD    = gc("#1c1c2a")
BORDER  = gc("#2a2a3a")
ACCENT  = gc("#e8ff47")
RED     = gc("#ff4778")
BLUE    = gc("#47d0ff")
MUTED   = gc("#6b6b8a")
WHITE   = gc("#f0f0f8")
MCLR    = {"rock": gc("#ff6b47"), "paper": gc("#47d0ff"), "scissors": gc("#e8ff47")}

EMOJI = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
BEATS = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
MOVES = ["rock", "paper", "scissors"]
PORT  = 9999

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def send_msg(sock, t, **d):
    sock.sendall((json.dumps({"type": t, **d}) + "\n").encode())

def evaluate(p, o):
    if p == o: return "tie"
    return "win" if BEATS[p] == o else "lose"

def L(text, size=14, color=None, bold=False, halign="center", **kw):
    return Label(text=text, font_size=dp(size),
                 color=color or WHITE, bold=bold, halign=halign,
                 size_hint_y=None, height=dp(size * 2.2), **kw)

def Btn(text, bg=None, fg=None, cb=None, **kw):
    b = Button(text=text, font_size=dp(15), bold=True,
               background_normal="",
               background_color=bg or ACCENT,
               color=fg or BG,
               size_hint_y=None, height=dp(54), **kw)
    if cb:
        b.bind(on_press=lambda *_: cb())
    return b

def Card(border=None, **kw):
    f = BoxLayout(**kw)
    bc = border or BORDER
    with f.canvas.before:
        Color(*bc)
        r1 = RoundedRectangle(pos=f.pos, size=f.size, radius=[dp(12)])
        Color(*CARD)
        r2 = RoundedRectangle(
            pos=(f.x + dp(2), f.y + dp(2)),
            size=(max(0, f.width - dp(4)), max(0, f.height - dp(4))),
            radius=[dp(10)]
        )
    def upd(*_):
        r1.pos = f.pos
        r1.size = f.size
        r2.pos = (f.x + dp(2), f.y + dp(2))
        r2.size = (max(0, f.width - dp(4)), max(0, f.height - dp(4)))
    f.bind(pos=upd, size=upd)
    return f


class NameScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(30), spacing=dp(12))
        root.add_widget(BoxLayout())
        root.add_widget(L("🪨  📄  ✂️", size=44))
        root.add_widget(L("ROCK · PAPER · SCISSORS", size=17, color=ACCENT, bold=True))
        root.add_widget(L("MULTIPLAYER  NETWORK  EDITION", size=10, color=MUTED))
        root.add_widget(BoxLayout(size_hint_y=None, height=dp(20)))
        root.add_widget(L("ENTER YOUR NAME", size=11, color=MUTED))
        self.ni = TextInput(
            text="Player", font_size=dp(24), halign="center",
            background_color=CARD, foreground_color=WHITE,
            cursor_color=ACCENT, multiline=False,
            size_hint_y=None, height=dp(56),
            padding=[dp(12), dp(14)]
        )
        root.add_widget(self.ni)
        root.add_widget(BoxLayout(size_hint_y=None, height=dp(8)))
        root.add_widget(Btn("CONTINUE  →", cb=self._go))
        root.add_widget(BoxLayout())
        self.add_widget(root)

    def _go(self):
        App.get_running_app().player_name = (self.ni.text.strip() or "Player")[:20]
        self.manager.current = "launcher"


class LauncherScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(14))
        root.add_widget(BoxLayout(size_hint_y=None, height=dp(16)))
        root.add_widget(L("RPS · GO", size=26, color=ACCENT, bold=True))
        root.add_widget(L("Two players. Two devices. One winner.", size=12))

        hc = Card(border=ACCENT, orientation="vertical", padding=dp(14), spacing=dp(8),
                  size_hint_y=None, height=dp(170))
        hc.add_widget(L("🖥  HOST THE GAME", size=16, color=ACCENT, bold=True))
        hc.add_widget(L("Start a server on THIS device.\nYour friend connects to your IP.",
                         size=11, color=MUTED))
        hc.add_widget(Btn("HOST  →", cb=lambda: setattr(self.manager, "current", "host")))
        root.add_widget(hc)

        jc = Card(border=BLUE, orientation="vertical", padding=dp(14), spacing=dp(8),
                  size_hint_y=None, height=dp(170))
        jc.add_widget(L("📡  JOIN A GAME", size=16, color=BLUE, bold=True))
        jc.add_widget(L("Connect to your friend's device.\nYou need their IP address.",
                         size=11, color=MUTED))
        jc.add_widget(Btn("JOIN  →", bg=BLUE, cb=lambda: setattr(self.manager, "current", "join")))
        root.add_widget(jc)

        root.add_widget(L("Both devices must be on the same Wi-Fi", size=10, color=MUTED))
        root.add_widget(BoxLayout())
        self.add_widget(root)


class HostScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._srv = None
        self._active = False
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(14))
        root.add_widget(BoxLayout(size_hint_y=None, height=dp(16)))
        root.add_widget(L("🖥  HOSTING", size=22, color=ACCENT, bold=True))
        root.add_widget(L("Tell your friend this IP address:", size=12, color=MUTED))

        ipc = Card(border=ACCENT, orientation="vertical", padding=dp(12),
                   size_hint_y=None, height=dp(110))
        ipc.add_widget(L("YOUR IP ADDRESS", size=10, color=MUTED, bold=True))
        self.ip_l = L("...", size=28, color=ACCENT, bold=True)
        ipc.add_widget(self.ip_l)
        ipc.add_widget(L(f"Port: {PORT}", size=11, color=MUTED))
        root.add_widget(ipc)

        self.st = L("⏳  Waiting for opponent...", size=13, color=BLUE)
        root.add_widget(self.st)
        root.add_widget(BoxLayout())
        root.add_widget(Btn("← Back", bg=CARD, fg=MUTED, cb=self._back))
        self.add_widget(root)

    def on_enter(self):
        self._active = True
        self.ip_l.text = get_ip()
        threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        try:
            self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._srv.bind(("0.0.0.0", PORT))
            self._srv.listen(1)
            conn, _ = self._srv.accept()
            if not self._active:
                conn.close()
                return
            app = App.get_running_app()
            send_msg(conn, "HELLO", name=app.player_name)
            raw = conn.recv(4096).decode()
            opp = "Opponent"
            for line in raw.strip().split("\n"):
                try:
                    d = json.loads(line)
                    if d.get("type") == "HELLO":
                        opp = d.get("name", opp)
                except:
                    pass
            Clock.schedule_once(
                lambda dt: self._start(conn, app.player_name, opp), 0.5)
        except Exception as e:
            if self._active:
                Clock.schedule_once(
                    lambda dt: setattr(self.st, "text", f"❌  {e}"), 0)

    def _start(self, conn, mn, on):
        gs = self.manager.get_screen("game")
        gs.setup(conn, mn, on, True)
        self.manager.current = "game"

    def _back(self):
        self._active = False
        try:
            self._srv.close()
        except:
            pass
        self.manager.current = "launcher"

    def on_leave(self):
        self._active = False


class JoinScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(14))
        root.add_widget(BoxLayout(size_hint_y=None, height=dp(16)))
        root.add_widget(L("📡  JOIN GAME", size=22, color=BLUE, bold=True))
        root.add_widget(L("Type your friend's IP address:", size=12, color=MUTED))

        ipc = Card(border=BLUE, orientation="vertical", padding=dp(12),
                   size_hint_y=None, height=dp(100))
        ipc.add_widget(L("FRIEND'S IP ADDRESS", size=10, color=MUTED, bold=True))
        self.ip = TextInput(
            text="192.168.1.", font_size=dp(22), halign="center",
            background_color=CARD, foreground_color=ACCENT,
            cursor_color=ACCENT, multiline=False,
            size_hint_y=None, height=dp(52),
            padding=[dp(12), dp(10)]
        )
        ipc.add_widget(self.ip)
        root.add_widget(ipc)

        self.st = L("Enter IP then tap Connect", size=11, color=MUTED)
        root.add_widget(self.st)
        root.add_widget(Btn("🔌  CONNECT", bg=BLUE, cb=self._connect))
        root.add_widget(BoxLayout())
        root.add_widget(Btn("← Back", bg=CARD, fg=MUTED,
                             cb=lambda: setattr(self.manager, "current", "launcher")))
        self.add_widget(root)

    def _connect(self):
        host = self.ip.text.strip()
        if not host:
            self.st.text = "❌  Please enter an IP address"
            return
        self.st.text = f"⏳  Connecting to {host}..."
        threading.Thread(target=self._do, args=(host,), daemon=True).start()

    def _do(self, host):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(8)
            s.connect((host, PORT))
            s.settimeout(None)
            app = App.get_running_app()
            send_msg(s, "HELLO", name=app.player_name)
            raw = s.recv(4096).decode()
            opp = "Host"
            for line in raw.strip().split("\n"):
                try:
                    d = json.loads(line)
                    if d.get("type") == "HELLO":
                        opp = d.get("name", opp)
                except:
                    pass
            Clock.schedule_once(
                lambda dt: self._start(s, app.player_name, opp), 0)
        except socket.timeout:
            Clock.schedule_once(
                lambda dt: setattr(self.st, "text", "❌  Timed out. Check IP."), 0)
        except ConnectionRefusedError:
            Clock.schedule_once(
                lambda dt: setattr(self.st, "text", "❌  Refused. Is host ready?"), 0)
        except Exception as e:
            Clock.schedule_once(
                lambda dt: setattr(self.st, "text", f"❌  {e}"), 0)

    def _start(self, s, mn, on):
        gs = self.manager.get_screen("game")
        gs.setup(s, mn, on, False)
        self.manager.current = "game"


class GameScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.sock = None
        self.my_name = ""
        self.opp_name = ""
        self.my_move = None
        self.opp_move = None
        self.my_score = 0
        self.opp_score = 0
        self.history = []
        self.busy = False
        self._buf = ""
        self._built = False

    def setup(self, sock, mn, on, is_host):
        self.sock = sock
        self.my_name = mn
        self.opp_name = on
        self.my_score = self.opp_score = 0
        self.history = []
        self.my_move = self.opp_move = None
        self.busy = False
        self._buf = ""
        if not self._built:
            self._build()
            self._built = True
        else:
            self._reset_ui()
        threading.Thread(target=self._recv, daemon=True).start()
        Clock.schedule_once(lambda dt: self._log(f"✅ Connected! Playing vs {on}"), 0)

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))

        hdr = BoxLayout(size_hint_y=None, height=dp(36))
        hdr.add_widget(L("🪨📄✂️  RPS MULTIPLAYER", size=13,
                          color=ACCENT, bold=True, halign="left"))
        root.add_widget(hdr)

        sf = BoxLayout(size_hint_y=None, height=dp(80), spacing=dp(8))
        pc = Card(orientation="vertical", padding=dp(6))
        pc.add_widget(L("YOU", size=9, color=MUTED))
        self.ms = L("0", size=36, color=ACCENT, bold=True)
        pc.add_widget(self.ms)
        sf.add_widget(pc)
        sf.add_widget(L("VS", size=13, color=MUTED, bold=True,
                         size_hint_x=None, width=dp(32)))
        oc = Card(orientation="vertical", padding=dp(6))
        self.opp_lbl = L(self.opp_name[:12], size=9, color=MUTED)
        oc.add_widget(self.opp_lbl)
        self.os = L("0", size=36, color=RED, bold=True)
        oc.add_widget(self.os)
        sf.add_widget(oc)
        root.add_widget(sf)

        mf = BoxLayout(size_hint_y=None, height=dp(106), spacing=dp(8))
        pc2 = Card(orientation="vertical", padding=dp(6))
        pc2.add_widget(L("YOU", size=9, color=MUTED))
        self.pe = L("🤔", size=38)
        pc2.add_widget(self.pe)
        self.pm = L("Pick!", size=10, color=MUTED)
        pc2.add_widget(self.pm)
        mf.add_widget(pc2)
        cc = Card(orientation="vertical", padding=dp(6))
        self.oe_name = L(self.opp_name[:12], size=9, color=MUTED)
        cc.add_widget(self.oe_name)
        self.oe = L("🤖", size=38)
        cc.add_widget(self.oe)
        self.om = L("Waiting...", size=10, color=MUTED)
        cc.add_widget(self.om)
        mf.add_widget(cc)
        root.add_widget(mf)

        self.res = L("", size=20, color=ACCENT, bold=True,
                     size_hint_y=None, height=dp(42))
        root.add_widget(self.res)

        root.add_widget(L("— YOUR MOVE —", size=10, color=MUTED))
        bf = GridLayout(cols=3, spacing=dp(6), size_hint_y=None, height=dp(96))
        self.mbtns = {}
        for mv in MOVES:
            b = Button(text=f"{EMOJI[mv]}\n{mv.upper()}", font_size=dp(13),
                       bold=True, background_normal="",
                       background_color=CARD, color=WHITE)
            b.bind(on_press=lambda _, m=mv: self._move(m))
            bf.add_widget(b)
            self.mbtns[mv] = b
        root.add_widget(bf)

        root.add_widget(L("💬 CHAT", size=9, color=MUTED, halign="left"))
        self.chat = Label(text="", font_size=dp(10), color=WHITE,
                          halign="left", valign="top",
                          size_hint_y=None, height=dp(60),
                          text_size=(Window.width - dp(20), None))
        sv = ScrollView(size_hint_y=None, height=dp(62))
        sv.add_widget(self.chat)
        root.add_widget(sv)

        cf = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.ci = TextInput(
            hint_text="Type a message...", font_size=dp(12),
            background_color=CARD, foreground_color=WHITE,
            cursor_color=ACCENT, multiline=False,
            padding=[dp(8), dp(8)]
        )
        cf.add_widget(self.ci)
        sb = Button(text="Send", font_size=dp(12), bold=True,
                    background_normal="", background_color=MUTED,
                    color=BG, size_hint_x=None, width=dp(66))
        sb.bind(on_press=lambda *_: self._chat())
        cf.add_widget(sb)
        root.add_widget(cf)

        root.add_widget(Btn("← New Game", bg=CARD, fg=MUTED,
                             cb=lambda: setattr(self.manager, "current", "launcher")))
        self.add_widget(root)

    def _reset_ui(self):
        self.opp_lbl.text = self.opp_name[:12]
        self.oe_name.text = self.opp_name[:12]
        self.ms.text = "0"
        self.os.text = "0"
        self.pe.text = "🤔"
        self.pm.text = "Pick!"
        self.oe.text = "🤖"
        self.om.text = "Waiting..."
        self.res.text = ""
        for b in self.mbtns.values():
            b.disabled = False

    def _log(self, t):
        self.chat.text += t + "\n"

    def _chat(self):
        msg = self.ci.text.strip()
        if not msg:
            return
        self.ci.text = ""
        self._log(f"You: {msg}")
        try:
            send_msg(self.sock, "CHAT", name=self.my_name, text=msg)
        except:
            pass

    def _move(self, mv):
        if self.busy:
            return
        self.busy = True
        self.my_move = mv
        for b in self.mbtns.values():
            b.disabled = True
        self.pe.text = EMOJI[mv]
        self.pm.text = mv.upper()
        self.res.text = "⏳ Waiting for opponent..."
        self.res.color = MUTED
        self._log(f"You: {EMOJI[mv]} {mv}")
        try:
            send_msg(self.sock, "MOVE", move=mv)
        except Exception as e:
            self._log(f"❌ {e}")
            self.busy = False

    def _recv(self):
        while True:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                self._buf += data.decode()
                while "\n" in self._buf:
                    line, self._buf = self._buf.split("\n", 1)
                    if line.strip():
                        try:
                            m = json.loads(line)
                            Clock.schedule_once(lambda dt, msg=m: self._handle(msg), 0)
                        except:
                            pass
            except:
                break
        Clock.schedule_once(lambda dt: self._disc(), 0)

    def _handle(self, msg):
        t = msg.get("type")
        if t == "MOVE":
            self.opp_move = msg.get("move")
            self.oe.text = EMOJI.get(self.opp_move, "❓")
            self.om.text = (self.opp_move or "?").upper()
            self._log(f"{self.opp_name}: {EMOJI.get(self.opp_move,'')} {self.opp_move}")
            if self.my_move:
                self._resolve()
        elif t == "CHAT":
            self._log(f"{msg.get('name', self.opp_name)}: {msg.get('text', '')}")

    def _resolve(self):
        r = evaluate(self.my_move, self.opp_move)
        if r == "win":
            self.res.text = "🎉  YOU WIN!"
            self.res.color = ACCENT
            self.my_score += 1
            self.history.append("w")
        elif r == "lose":
            self.res.text = f"😔  {self.opp_name} WINS"
            self.res.color = RED
            self.opp_score += 1
            self.history.append("l")
        else:
            self.res.text = "🤝  TIE!"
            self.res.color = BLUE
            self.history.append("t")
        self.ms.text = str(self.my_score)
        self.os.text = str(self.opp_score)
        self.my_move = self.opp_move = None
        self.busy = False
        for b in self.mbtns.values():
            b.disabled = False

    def _disc(self):
        self._log(f"⚠️  {self.opp_name} disconnected.")
        self.res.text = "DISCONNECTED"
        self.res.color = RED


class RPSApp(App):
    player_name = "Player"

    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(NameScreen(name="name"))
        sm.add_widget(LauncherScreen(name="launcher"))
        sm.add_widget(HostScreen(name="host"))
        sm.add_widget(JoinScreen(name="join"))
        sm.add_widget(GameScreen(name="game"))
        return sm


if __name__ == "__main__":
    RPSApp().run()
