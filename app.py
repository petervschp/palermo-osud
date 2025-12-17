from browser import document, html, window, timer, ajax
import json
import random

LS_KEY = "palermo_osud_brython_v1"

# -------- Utilities --------
def toast(msg: str):
    t = document["toast"]
    t.text = msg
    t.style.display = "block"
    def hide():
        t.style.display = "none"
    timer.clear_timeout(getattr(toast, "_tm", None) or 0)
    toast._tm = timer.set_timeout(hide, 1800)


def _bind_focus_scroll(inp, target):
    try:
        def _on_focus(ev):
            try:
                target.scrollIntoView({"block": "center", "behavior": "smooth"})
            except Exception:
                try:
                    target.scrollIntoView()
                except Exception:
                    pass
        inp.bind("focus", _on_focus)
    except Exception:
        pass


def _set_pin_attrs(inp):
    """Force numeric keypad + reduce keyboard/UI issues on mobile."""
    try:
        inp.type = "tel"          # numeric keypad (more reliable than type=number/password on iOS)
        inp.inputMode = "numeric" # hint for modern browsers
        inp.pattern = "[0-9]*"
        inp.autocomplete = "off"
        inp.autocapitalize = "off"
        inp.spellcheck = False
    except Exception:
        pass



def save(state):
    window.localStorage.setItem(LS_KEY, json.dumps(state))

def load():
    raw = window.localStorage.getItem(LS_KEY)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None

def clear_state():
    window.localStorage.removeItem(LS_KEY)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def shuffle(lst):
    lst = list(lst)
    random.shuffle(lst)
    return lst

def role_label(role):
    return {
        "mafia": "Mafia",
        "katanyi": "Komisár Katányi",
        "doctor": "Lekár",
        "citizen": "Občan"
    }.get(role, role)

def side_label(role):
    return "MAFIA" if role == "mafia" else "OBČAN"

def alive_players(state):
    return [p for p in state["players"] if p["alive"]]

def get_player(state, pid):
    for p in state["players"]:
        if p["id"] == pid:
            return p
    return None

def win_check(state):
    alive = alive_players(state)
    mafia = sum(1 for p in alive if p["role"] == "mafia")
    others = len(alive) - mafia
    if mafia <= 0:
        return {"over": True, "winner": "obcan"}
    if mafia >= others and len(alive) > 0:
        return {"over": True, "winner": "mafia"}
    return {"over": False}

def allowed_mafia_counts(n):
    # defaults: 5-6 -> [1], 7-9 -> [1,2] (default 2), 10-12 -> [2,3] (default 3)
    if n <= 6:
        return [1]
    if n <= 9:
        return [1,2]
    return [2,3]

# -------- Facts loading --------
FACTS = []
FACTS_READY = False

def load_facts():
    global FACTS, FACTS_READY
    def on_complete(req):
        global FACTS, FACTS_READY
        if req.status in (200, 0):
            try:
                FACTS = json.loads(req.text)
            except Exception:
                FACTS = []
        FACTS_READY = True
        render()
    req = ajax.Ajax()
    req.bind("complete", lambda ev: on_complete(req))
    req.open("GET", "facts_chobotnica.json", True)
    req.send()

def pick_fact(state):
    if not FACTS:
        return None
    no_spoiler = state["settings"]["facts_no_spoiler"]
    pool = [f for f in FACTS if (not no_spoiler) or (not f.get("spoiler", False))]
    if not pool:
        return None
    used = state.setdefault("_facts_used", [])
    # avoid repeats: try a few times
    for _ in range(10):
        f = random.choice(pool)
        if f.get("id") not in used:
            used.append(f.get("id"))
            used[:] = used[-200:]
            return f
    return random.choice(pool)

# -------- UI helpers --------
def card(*children, cls="card"):
    return html.DIV(children, Class=cls)

def h2(text): return html.H2(text)
def para(text, cls=""): return html.P(text, Class=cls) if cls else html.P(text)
def hr(): return html.DIV(Class="hr")
def tag(text): return html.SPAN(text, Class="tag")

def choice_row(label, on_click):
    row = html.DIV(Class="choice")
    row <= html.SPAN(label)
    row <= html.SPAN("Vybrať", Class="kbd")
    row.bind("click", on_click)
    return row

def set_subtitle(text):
    document["subtitle"].text = text


PUBLIC_URL = ""
PUBLIC_URL_READY = False

def _is_local_host():
    try:
        host = window.location.hostname
        proto = window.location.protocol
        return proto == "file:" or host in ("localhost","127.0.0.1","0.0.0.0")
    except Exception:
        return False

def _is_standalone():
    try:
        return window.matchMedia("(display-mode: standalone)").matches
    except Exception:
        return False

def _load_public_url():
    """Load public URL for QR (optional). Put your GitHub Pages URL into public_url.txt."""
    global PUBLIC_URL, PUBLIC_URL_READY
    try:
        def ok(req):
            global PUBLIC_URL, PUBLIC_URL_READY
            if req.status in (200, 0):
                PUBLIC_URL = (req.text or "").strip()
            PUBLIC_URL_READY = True
        def fail(req):
            global PUBLIC_URL_READY
            PUBLIC_URL_READY = True
        ajax.get("public_url.txt", oncomplete=ok, onerror=fail, timeout=1500)
    except Exception:
        PUBLIC_URL_READY = True

def _show_about():
    # overlay
    ov = html.DIV(Class="overlay")
    modal = html.DIV(Class="card grid modal")
    modal <= h2("O hre Palermo – Osud")
    modal <= para("Hostless verzia hry Mestečko Palermo/Mafia: roly, noc/deň, tajné akcie. Mobil koluje u každého živého hráča; appka nahrádza moderátora („Osud“).", "small")
    modal <= hr()

    left = html.DIV(Class="grid")
    left <= tag("Ako hrať (stručne)")
    left <= para("1) Nastav mená, PIN a roly. 2) Rozdaj roly (mobil koluje). 3) Počas noci každý živý hráč spraví akciu. 4) Ráno appka vyhodnotí noc. 5) Cez deň diskutujete mimo appky a v appke zadáte odsúdeného.", "small")
    left <= para("Tip: Mikro-obsah a maskovacia akcia vyrovnávajú čas na mobile, aby sa roly neprezrádzali podľa rýchlosti.", "small")

    right = html.DIV(Class="grid center")
    right <= tag("Web verzia")
    if not PUBLIC_URL_READY:
        right <= para("Načítavam URL…", "small")
    if PUBLIC_URL:
        right <= html.DIV(PUBLIC_URL, Class="kbd")
        # QR via remote generator (lightweight)
        try:
            enc = window.encodeURIComponent(PUBLIC_URL)
        except Exception:
            enc = PUBLIC_URL
        qr = html.IMG(Src=f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={enc}", Class="qr", Alt="QR")
        right <= qr
        right <= para("Naskenuj QR a otvor web. Potom si môžeš appku nainštalovať do zariadenia.", "small")
    else:
        right <= para("Doplň svoju GitHub Pages URL do súboru public_url.txt (v koreni projektu).", "small")

    two = html.DIV(Class="two")
    two <= left
    two <= right
    modal <= two
    modal <= hr()
    close = html.BUTTON("Zavrieť", Class="secondary")
    def do_close(ev=None):
        try:
            ov.remove()
        except Exception:
            pass
    close.bind("click", do_close)
    modal <= close
    ov <= modal
    document <= ov

def _wire_install_about_button(state):
    """Header button: on web show Install (if available), on local show About."""
    try:
        btn = document["btn_install"]
    except Exception:
        return

    # Default: hidden
    btn.style.display = "none"
    btn.text = "Inštalovať"
    btn.dataset.mode = ""

    # Hide when installed
    if _is_standalone():
        return

    # Local: About
    if _is_local_host():
        btn.style.display = "inline-flex"
        btn.text = "O hre"
        btn.dataset.mode = "about"
    else:
        # Web: show only if install prompt available (set by JS)
        try:
            if getattr(window, "deferredPrompt", None):
                btn.style.display = "inline-flex"
                btn.text = "Inštalovať"
                btn.dataset.mode = "install"
        except Exception:
            pass

    def on_click(ev=None):
        mode = getattr(btn, "dataset", {}).get("mode", "")
        if mode == "install":
            try:
                dp = getattr(window, "deferredPrompt", None)
                if dp:
                    dp.prompt()
                    # userChoice is a promise; we don't need to await
                    window.deferredPrompt = None
                    btn.style.display = "none"
            except Exception:
                pass
        else:
            _show_about()
    btn.unbind("click")
    btn.bind("click", on_click)

def _wire_osud_button(state):
    """Show Osud button only when 'first dead = osud' is active and enabled."""
    try:
        btn = document["btn_osud"]
    except Exception:
        return
    btn.style.display = "none"
    if not state:
        return
    if state.get("settings", {}).get("first_dead_osud") and state.get("osud", {}).get("enabled"):
        btn.style.display = "inline-flex"

# -------- State / Phases --------
# phases:
# setup
# role_pass
# night_turn
# dawn
# day_admin
# end

DEFAULTS = {
    "include_katanyi": True,
    "include_doctor": False,
    "mafia_know": True,
    "mafia_strict_unanimity": True,
    "reveal_after_judgement": "side", # none/side/full
    "first_dead_osud": False,
    "mask_citizens": True,
    "facts_enabled": True,
    "facts_for_all": False,
    "facts_no_spoiler": True,
    "min_screen_ms": 3000
}


def normalize_names(raw_lines):
    """Strip names, drop empties, and make them unique (case-insensitive) while preserving order.
    Returns (names, fixed_dupes) where fixed_dupes is a list of original duplicate base names.
    """
    cleaned = [x.strip() for x in raw_lines if x and x.strip()]
    seen = {}
    out = []
    fixed = []
    for name in cleaned:
        key = name.casefold()
        if key not in seen:
            seen[key] = 1
            out.append(name)
        else:
            seen[key] += 1
            if name not in fixed:
                fixed.append(name)
            out.append(f"{name} ({seen[key]})")
    return out, fixed

def new_game(names, pin, mafia_count, settings):
    players = [{"id": i, "name": n, "alive": True, "role": "citizen"} for i, n in enumerate(names)]
    roles = []
    roles += ["mafia"] * mafia_count
    if settings["include_katanyi"]:
        roles.append("katanyi")
    if settings["include_doctor"]:
        roles.append("doctor")
    while len(roles) < len(players):
        roles.append("citizen")
    roles = shuffle(roles)
    for i, r in enumerate(roles):
        players[i]["role"] = r

    state = {
        "phase": "role_pass",
        "day": 1,
        "players": players,
        "pin": pin,
        "settings": settings,
        "step_index": 0,
        "night": {
            "mafia_votes": {},      # voterId -> targetId
            "katanyi_check": None,  # (voterId, targetId, isMafia)
            "doctor_save": None,    # targetId
            "citizen_dummy": {}     # voterId -> targetId
        },
        "last": {"night_dead": None, "day_dead": None},
        "osud": {"enabled": False, "player_id": None}
    }
    return state

def reset_night(state):
    state["night"] = {"mafia_votes": {}, "katanyi_check": None, "doctor_save": None, "citizen_dummy": {}}
    state["step_index"] = 0

def goto(phase):
    state = load()
    if not state:
        return
    state["phase"] = phase
    state["step_index"] = 0
    save(state)
    render()

# -------- Screens --------
def screen_setup():
    set_subtitle("Nastavenie hry")
    root = html.DIV(Class="grid")

    left = html.DIV(Class="card grid")
    left <= h2("Nastavenie")
    left <= para("Zadaj mená hráčov (každé na nový riadok). Rozsah v1: 5–12 hráčov.", "small")
    ta = html.TEXTAREA(Placeholder="Napr.\nAnna\nBoris\nCyril\nDáša\nEma\n…")
    left <= ta

    pin_in = html.INPUT(Type="tel", Placeholder="Spoločný PIN (4 číslice)", Maxlength="4", Class="pin")
    _set_pin_attrs(pin_in)
    pin_wrap = html.DIV(Class="grid")
    pin_wrap <= html.DIV([html.LABEL("Spoločný PIN (4 číslice)"), pin_in])
    left <= pin_wrap

    unlock_sel = html.SELECT()
    unlock_sel <= html.OPTION("Posuvník (default)", value="slider", selected=True)
    unlock_sel <= html.OPTION("Tlačidlo", value="button")
    left <= html.DIV([html.LABEL("Odomknutie obrazovky"), unlock_sel])


    # Settings cards (right)
    right = html.DIV(Class="card grid")
    right <= h2("Roly a pravidlá (defaulty)")
    # toggles
    def toggle(label, key, default):
        cb = html.INPUT(Type="checkbox")
        cb.checked = default
        row = html.LABEL(Class="pill", style={"gap":"10px"})
        row <= cb
        row <= html.SPAN(label)
        return cb, row

    cb_k, row_k = toggle("Komisár Katányi (Corrado Cattani)", "include_katanyi", True)
    cb_d, row_d = toggle("Lekár (voliteľné)", "include_doctor", False)
    cb_mk, row_mk = toggle("Mafia pozná ostatných mafiánov", "mafia_know", True)
    cb_mu, row_mu = toggle("Mafia: prísna zhoda (inak nikto nezomrie)", "mafia_strict_unanimity", True)
    cb_mask, row_mask = toggle("Maskovacia akcia pre civilov", "mask_citizens", True)
    cb_fact, row_fact = toggle("Mikro‑obsah po výbere", "facts_enabled", True)
    cb_fact_all, row_fact_all = toggle("Mikro‑obsah aj pre špeciálne roly", "facts_for_all", False)
    cb_nospoil, row_nospoil = toggle("Mikro‑obsah bez spoilerov", "facts_no_spoiler", True)
    cb_osud, row_osud = toggle("Prvý mŕtvy sa stane Osudom", "first_dead_osud", False)

    right <= row_k
    right <= row_d
    right <= hr()
    right <= row_mk
    right <= row_mu
    right <= hr()
    right <= row_mask
    right <= row_fact
    right <= row_fact_all
    right <= row_nospoil
    right <= hr()
    right <= row_osud

    reveal = html.SELECT()
    reveal <= html.OPTION("Po odsúdení: nič", value="none")
    reveal <= html.OPTION("Po odsúdení: mafia / občan (default)", value="side", selected=True)
    reveal <= html.OPTION("Po odsúdení: plná rola", value="full")
    right <= html.DIV([html.LABEL("Odhaľovanie po odsúdení"), reveal])

    # mafia count placeholder (depends on names)
    mafia_sel = html.SELECT()
    right <= html.DIV([html.LABEL("Počet mafiánov (ponuka sa prispôsobí počtu hráčov)"), mafia_sel])

    def refresh_mafia_options():
        names = [x.strip() for x in ta.value.splitlines() if x.strip()]
        n = len(names)
        mafia_sel.clear()
        opts = allowed_mafia_counts(n)
        for v in opts:
            opt = html.OPTION(str(v), value=str(v))
            # default choice: highest option
            if v == max(opts):
                opt.selected = True
            mafia_sel <= opt

    ta.bind("input", lambda ev: refresh_mafia_options())
    refresh_mafia_options()

    def on_start(ev=None):
        names, dupes = normalize_names(ta.value.splitlines())
        if dupes:
            toast("Duplicitné mená upravené: " + ", ".join(dupes))
            ta.value = "\n".join(names)
        if len(names) < 5 or len(names) > 12:
            window.alert("V1 je navrhnutá pre 5–12 hráčov. Uprav počet mien.")
            return
        pin = (pin_in.value or "").strip()
        if not (pin.isdigit() and len(pin) == 4):
            window.alert("Zadaj spoločný PIN – presne 4 číslice.")
            return

        settings = {
            "include_katanyi": bool(cb_k.checked),
            "include_doctor": bool(cb_d.checked),
            "mafia_know": bool(cb_mk.checked),
            "mafia_strict_unanimity": bool(cb_mu.checked),
            "unlock_mode": unlock_sel.value,
            "reveal_after_judgement": reveal.value,
            "first_dead_osud": bool(cb_osud.checked),
            "mask_citizens": bool(cb_mask.checked),
            "facts_enabled": bool(cb_fact.checked),
            "facts_for_all": bool(cb_fact_all.checked),
            "facts_no_spoiler": bool(cb_nospoil.checked),
            "min_screen_ms": DEFAULTS["min_screen_ms"]
        }
        mafia_count = int(mafia_sel.value)
        st = new_game(names, pin, mafia_count, settings)
        save(st)
        render()

    btn = html.BUTTON("Začať a rozdať roly")
    btn.bind("click", on_start)

    root <= html.DIV([left, right], Class="split")
    root <= card(tag("Tip"), para("Po prvom online načítaní (GitHub Pages) bude appka fungovať aj offline vďaka cache.", "small"))
    root <= html.DIV([btn], Class="card center")

    return root

def pass_gate(title_text, subtitle_text, on_unlock):
    st = load()
    pin_required = st["pin"] if st else ""

    wrap = html.DIV(Class="card grid center gate")
    wrap <= h2(title_text)
    if subtitle_text:
        wrap <= para(subtitle_text, "small")

    pin_in = html.INPUT(Type="tel", Placeholder="Zadaj PIN", Maxlength="4", Class="pin")
    _set_pin_attrs(pin_in)
    wrap <= pin_in

    # Unlock UI (default: slider; optional: button)
    mode = "slider"
    try:
        if st and "settings" in st:
            mode = st["settings"].get("unlock_mode", "slider")
    except Exception:
        mode = "slider"

    info = html.DIV("", Class="small")

    def check_pin():
        pin = (pin_in.value or "").strip()
        if pin != pin_required:
            toast("Nesprávny PIN")
            return False
        return True

    def do_unlock():
        if hasattr(window.navigator, "vibrate"):
            window.navigator.vibrate(40)
        on_unlock()

    if mode == "button":
        wrap <= para("Odomkni tlačidlom (nastavenie hry).", "small")
        btn = html.BUTTON("Odomknúť", Class="secondary", style={"fontSize":"18px", "padding":"16px 18px"})
        wrap <= btn
        wrap <= info
        def on_btn(ev=None):
            if check_pin():
                do_unlock()
        btn.bind("click", on_btn)
    else:
        wrap <= para("Potiahni posuvník doprava na odomknutie.", "small")
        slider = html.INPUT(Type="range", Min="0", Max="100", Value="0", Class="unlock-slider")
        wrap <= slider
        wrap <= info
        def on_slide(ev=None):
            if slider.value == "100":
                if check_pin():
                    do_unlock()
                # vždy vráť posuvník späť
                slider.value = "0"
        slider.bind("input", on_slide)
        slider.bind("change", on_slide)

    return wrap

def min_delay_button(label, ms, on_click, cls="secondary"):
    btn = html.BUTTON(label, Class=cls)
    btn.disabled = True
    left = {"t": int(ms/1000)}
    note = html.DIV(f"Môžeš pokračovať o {left['t']}s…", Class="small")

    def tick():
        left["t"] -= 1
        if left["t"] <= 0:
            btn.disabled = False
            note.text = ""
            timer.clear_interval(tick._i)
        else:
            note.text = f"Môžeš pokračovať o {left['t']}s…"
    tick._i = timer.set_interval(tick, 1000)
    btn.bind("click", lambda ev: on_click())
    return html.DIV([btn, note], Class="grid")

def role_pass_screen(state):
    set_subtitle("Rozdanie rolí")
    idx = state["step_index"]
    if idx >= len(state["players"]):
        # move to night
        reset_night(state)
        state["phase"] = "night_turn"
        save(state)
        return card(
            tag("Roly rozdané"),
            html.DIV("Začína noc 🌙", Class="big"),
            para("Počas noci koluje mobil u každého živého hráča. Každý prejde rovnakými krokmi.", "small"),
            html.BUTTON("Začať noc", **{"Class":"", "id":"start_night"})
        , cls="card grid center")

    player = state["players"][idx]

    def unlock():
        # after unlock: show role card
        role = player["role"]
        mafia_list = []
        if role == "mafia" and state["settings"]["mafia_know"]:
            mafia_list = [p["name"] for p in state["players"] if p["role"] == "mafia" and p["id"] != player["id"]]
        role_card = html.DIV(Class="card grid center")
        role_card <= tag("Tvoja rola")
        role_card <= html.DIV(role_label(role), Class="big")
        if role == "mafia":
            role_card <= para("V noci tajne vyberieš obeť. Nevidíš hlasy ostatných mafiánov.", "small")
            if state["settings"]["mafia_know"]:
                role_card <= para("Ostatní mafiáni:", "small")
                role_card <= html.DIV(", ".join(mafia_list) if mafia_list else "Si jediný mafián.", Class="kbd")
        elif role == "katanyi":
            role_card <= para("Raz za noc preveríš jedného hráča: MAFIA / OBČAN. Výsledok vidíš iba ty.", "small")
        elif role == "doctor":
            role_card <= para("Raz za noc zachrániš jedného hráča. Ak mafia trafí toho istého, nikto nezomrie.", "small")
        else:
            role_card <= para("Nemáš špeciálnu schopnosť (môžeš mať maskovaciu akciu).", "small")

        def next_step():
            st = load()
            st["step_index"] += 1
            save(st)
            render()

        role_card <= min_delay_button("Skryť a podať ďalšiemu", state["settings"]["min_screen_ms"], next_step)
        document["app"].clear()
        document["app"] <= role_card

    return pass_gate(
        f"Telefón pre: {player['name']}",
        "Zadaj PIN a odomkni. Potom si pozri rolu, skry a podaj ďalej.",
        unlock
    )

def pick_target_list(state, exclude_ids=None):
    exclude_ids = set(exclude_ids or [])
    living = alive_players(state)
    choices = [p for p in living if p["id"] not in exclude_ids]
    box = html.DIV(Class="list")
    for p in choices:
        box <= choice_row(p["name"], lambda ev, pid=p["id"]: on_pick(pid))
    return box, choices

def night_turn_screen(state):
    set_subtitle("Noc 🌙")
    alive = alive_players(state)
    idx = state["step_index"]
    if idx >= len(alive):
        # resolve night
        resolve_night(state)
        save(state)
        return dawn_screen(state)

    player = alive[idx]

    def unlock():
        role = player["role"]
        settings = state["settings"]

        # unified screen: choose name from list
        action = html.DIV(Class="card grid")
        action <= html.DIV([tag("Noc"), html.SPAN(f"Na rade: {player['name']}", Class="kbd")], Class="row")
        action <= h2("Vyber meno zo zoznamu")
        prompt = ""
        if role == "mafia":
            prompt = "Tajný výber mafie: koho by si zabil?"
        elif role == "katanyi":
            prompt = "Katányi: koho chceš preveriť?"
        elif role == "doctor":
            prompt = "Lekár: koho chceš zachrániť? (môžeš aj seba)"
        else:
            prompt = "Maskovanie: koho si túto noc „všímaš“?"
        action <= para(prompt, "small")

        result = html.DIV(Class="card grid center")
        result.style.display = "none"

        # define pick handler
        def do_pick(target_id):
            # store action
            if role == "mafia":
                state["night"]["mafia_votes"][str(player["id"])] = target_id
                res_main = f"Zaznamenané. (Mafia hlas)"
                res_sub = f"Tvoj cieľ: {get_player(state, target_id)['name']}"
            elif role == "katanyi":
                target = get_player(state, target_id)
                is_mafia = (target["role"] == "mafia")
                state["night"]["katanyi_check"] = {"voter": player["id"], "target": target_id, "is_mafia": is_mafia}
                res_main = "Výsledok"
                res_sub = f"{target['name']} je: {'MAFIA' if is_mafia else 'OBČAN'}"
            elif role == "doctor":
                state["night"]["doctor_save"] = target_id
                res_main = "Zachránené"
                res_sub = f"Chrániš: {get_player(state, target_id)['name']}"
            else:
                state["night"]["citizen_dummy"][str(player["id"])] = target_id
                res_main = "Zaznamenané"
                res_sub = f"Vybral(a) si: {get_player(state, target_id)['name']}"

            # microfact logic
            show_fact = settings["facts_enabled"] and (settings["facts_for_all"] or role == "citizen")
            fact = pick_fact(state) if show_fact else None

            result.clear()
            result <= tag("Hotovo")
            result <= html.DIV(res_main, Class="big")
            result <= para(res_sub, "small")

            if fact:
                result <= hr()
                result <= html.DIV("🦑 Mikro‑obsah", Class="tag")
                result <= html.P(fact.get("text",""), Class="small")

            def next_player():
                st = load()
                st["step_index"] += 1
                save(st)
                render()

            result <= min_delay_button("Skryť a podať ďalej", settings["min_screen_ms"], next_player)
            result.style.display = "grid"
            action.style.display = "none"
            save(state)

        # build list
        exclude = []
        if role != "doctor":
            exclude = [player["id"]]
        targets = [p for p in alive if p["id"] not in set(exclude)]
        lst = html.DIV(Class="list")
        for tgt in targets:
            def make_click(tid):
                return lambda ev: do_pick(tid)
            lst <= choice_row(tgt["name"], make_click(tgt["id"]))
        action <= lst

        document["app"].clear()
        document["app"] <= html.DIV([action, result], Class="grid")

    return pass_gate(
        f"Noc 🌙 • hráč {idx+1}/{len(alive)}",
        f"Telefón si zoberie {player['name']}. Zadaj PIN a odomkni. (Každý vyberie jedno meno.)",
        unlock
    )

def resolve_night(state):
    alive = alive_players(state)
    mafia_ids = [p["id"] for p in alive if p["role"] == "mafia"]
    votes = state["night"]["mafia_votes"]
    # collect only living mafia votes (some might be missing if a mafia didn't vote – treat as no kill)
    mafia_votes = [votes.get(str(mid)) for mid in mafia_ids if str(mid) in votes]

    kill_target = None
    if mafia_ids and len(mafia_votes) == len(mafia_ids):
        if state["settings"]["mafia_strict_unanimity"]:
            # all must match
            if len(set(mafia_votes)) == 1:
                kill_target = mafia_votes[0]
        else:
            # plurality; tie => no kill
            tally = {}
            for tid in mafia_votes:
                tally[tid] = tally.get(tid, 0) + 1
            mx = max(tally.values()) if tally else 0
            winners = [tid for tid, c in tally.items() if c == mx]
            if len(winners) == 1:
                kill_target = winners[0]

    # doctor save
    save_id = state["night"]["doctor_save"]
    if kill_target is not None and save_id == kill_target:
        kill_target = None

    # apply death
    state["last"]["night_dead"] = kill_target
    if kill_target is not None:
        victim = get_player(state, kill_target)
        if victim:
            victim["alive"] = False
            # first dead becomes osud option
            if state["settings"]["first_dead_osud"] and not state["osud"]["enabled"]:
                state["osud"] = {"enabled": True, "player_id": victim["id"]}

    # reset step index for next phase
    state["step_index"] = 0
    state["phase"] = "dawn"

def dawn_screen(state):
    set_subtitle(f"Ráno • Deň {state['day']}")
    dead_id = state["last"]["night_dead"]
    msg = "Nikto nezomrel."
    if dead_id is not None:
        msg = f"{get_player(state, dead_id)['name']} zomrel(a)."
    w = win_check(state)
    if w["over"]:
        state["phase"] = "end"
        save(state)
        return end_screen(state)

    root = html.DIV(Class="card grid center")
    root <= tag("Ráno")
    root <= html.DIV(msg, Class="big")
    if state["settings"]["first_dead_osud"] and state["osud"]["enabled"] and dead_id is not None:
        root <= para("Prvý mŕtvy sa stal Osudom. Mobil môže zostať u neho (admin panel je vpravo hore).", "small")
    root <= para("Diskusia prebieha mimo appky. Keď ste pripravení, zadajte odsúdeného.", "small")

    btn = html.BUTTON("Prejsť na deň (zadanie odsúdeného)", Class="")
    def go_day(ev=None):
        st = load()
        st["phase"] = "day_admin"
        st["step_index"] = 0
        save(st)
        render()
    btn.bind("click", go_day)
    root <= btn
    return root

def day_admin_screen(state):
    set_subtitle(f"Deň {state['day']} • administrácia")
    root = html.DIV(Class="grid")

    def unlock_admin():
        panel = html.DIV(Class="card grid")
        panel <= h2("Zadaj odsúdeného")
        panel <= para("Hlasovanie prebehlo mimo appky. Vyber odsúdeného zo zoznamu živých alebo zvoľ „Nikto“.", "small")

        alive = alive_players(state)
        lst = html.DIV(Class="list")

        def apply_judgement(target_id):
            state["last"]["day_dead"] = target_id
            reveal_mode = state["settings"]["reveal_after_judgement"]
            outcome = html.DIV(Class="card grid center")

            if target_id is not None:
                victim = get_player(state, target_id)
                victim["alive"] = False
                if state["settings"]["first_dead_osud"] and not state["osud"]["enabled"]:
                    state["osud"] = {"enabled": True, "player_id": victim["id"]}

                outcome <= tag("Odsúdený")
                outcome <= html.DIV(victim["name"], Class="big")

                if reveal_mode == "none":
                    outcome <= para("Rola nebola zverejnená (podľa nastavenia).", "small")
                elif reveal_mode == "side":
                    outcome <= para(f"Bol to: {side_label(victim['role'])}", "small")
                else:
                    outcome <= para(f"Rola: {role_label(victim['role'])}", "small")
            else:
                outcome <= tag("Odsúdený")
                outcome <= html.DIV("Nikto", Class="big")
                outcome <= para("Tento deň nebol nikto vyradený.", "small")

            w = win_check(state)
            if w["over"]:
                state["phase"] = "end"
                save(state)
                document["app"].clear()
                document["app"] <= end_screen(state)
                return

            # next night
            state["day"] += 1
            reset_night(state)
            state["phase"] = "night_turn"
            save(state)

            def next_night():
                render()
            outcome <= min_delay_button("Pokračovať na noc", state["settings"]["min_screen_ms"], next_night, cls="")

            document["app"].clear()
            document["app"] <= outcome

        # add "none" option
        lst <= choice_row("Nikto nebol odsúdený", lambda ev: apply_judgement(None))
        for p_ in alive:
            lst <= choice_row(p_["name"], lambda ev, pid=p_["id"]: apply_judgement(pid))
        panel <= lst

        document["app"].clear()
        document["app"] <= panel

    root <= pass_gate("Deň – admin PIN", "Zadaj PIN a podrž (zadanie odsúdeného).", unlock_admin)
    root <= card(tag("Poznámka"), para("Admin je chránený spoločným PIN-om, aby sa minimalizovali omyly/trolling.", "small"))
    return root

def end_screen(state):
    w = win_check(state)
    winner = "Mafia" if w.get("winner") == "mafia" else "Občania"
    set_subtitle("Koniec hry")

    root = html.DIV(Class="grid")
    head = html.DIV(Class="card grid center")
    head <= tag("Koniec")
    head <= html.DIV(f"{winner} vyhrali!", Class="big")
    head <= para("Roly ukazujeme až teraz.", "small")

    roles = html.DIV(Class="card grid")
    roles <= h2("Roly")
    lst = html.DIV(Class="list")
    for p_ in state["players"]:
        row = html.DIV(Class="choice")
        row <= html.SPAN(p_["name"])
        row <= html.SPAN(role_label(p_["role"]), Class="kbd")
        lst <= row
    roles <= lst

    btns = html.DIV(Class="card row")
    def new_same(ev=None):
        names = [p_["name"] for p_ in state["players"]]
        mafia_count = sum(1 for p_ in state["players"] if p_["role"] == "mafia")
        settings = state["settings"]
        st = new_game(names, state["pin"], mafia_count, settings)
        save(st)
        render()
    def back_setup(ev=None):
        clear_state()
        render()

    b1 = html.BUTTON("Nová hra (tie isté mená)")
    b2 = html.BUTTON("Späť na nastavenie", Class="secondary")
    b1.bind("click", new_same)
    b2.bind("click", back_setup)
    btns <= b1
    btns <= b2

    root <= head
    root <= roles
    root <= btns
    return root

def osud_panel(state):
    # optional panel (if first dead becomes osud enabled and triggered)
    if not (state.get("settings", {}).get("first_dead_osud") and state.get("osud", {}).get("enabled")):
        return card(tag("Osud"), para("Režim „Prvý mŕtvy = Osud“ nie je aktívny.", "small"))
    pid = state["osud"]["player_id"]
    osud_name = get_player(state, pid)["name"] if get_player(state, pid) else "?"
    panel = html.DIV(Class="card grid")
    panel <= h2("Osud")
    panel <= para(f"Osud: {osud_name}", "small")
    panel <= para("Toto je admin náhľad (použi ho iba technicky, nie na hranie).", "small")
    panel <= hr()
    # show roles + alive status
    lst = html.DIV(Class="list")
    for p_ in state["players"]:
        row = html.DIV(Class="choice")
        row <= html.SPAN(("🟢 " if p_["alive"] else "⚫ ") + p_["name"])
        row <= html.SPAN(role_label(p_["role"]), Class="kbd")
        lst <= row
    panel <= lst
    return panel

# -------- Render --------
def render():
    state = load()
    app = document["app"]
    app.clear()

    # header buttons
    _wire_install_about_button(state)
    _wire_osud_button(state)

    # subtitle (keep simple to avoid confusing counters)
    if not state:
        set_subtitle("Hostless PWA • Brython")
    else:
        ph = state.get("phase","")
        if ph == "setup":
            set_subtitle("Nastavenie hry")
        elif ph == "role_pass":
            set_subtitle("Rozdanie rolí")
        elif ph == "night_turn":
            set_subtitle("Noc 🌙")
        elif ph == "dawn":
            set_subtitle(f"Ráno • Deň {state.get('day',1)}")
        elif ph == "day_admin":
            set_subtitle(f"Deň {state.get('day',1)} • administrácia")
        elif ph == "end":
            set_subtitle("Koniec hry")

    # top buttons
    def on_reset(ev=None):
        if window.confirm("Naozaj resetovať hru?"):
            clear_state()
            render()
    document["btn_reset"].unbind("click")
    document["btn_reset"].bind("click", on_reset)

    def on_status(ev=None):
        st = load()
        if not st:
            toast("Bez hry")
            return
        alive = len(alive_players(st))
        toast(f"Živí: {alive}/{len(st['players'])} • Deň {st['day']} • Fáza: {st['phase']}")
    document["btn_status"].unbind("click")
    document["btn_status"].bind("click", on_status)

    def on_osud(ev=None):
        st = load()
        if not st:
            toast("Bez hry")
            return
        if not (st.get("settings", {}).get("first_dead_osud") and st.get("osud", {}).get("enabled")):
            toast("Osud: režim „Prvý mŕtvy = Osud“ nie je aktívny")
            return
        # Admin náhľad (len pre technické vedenie)
        app <= osud_panel(st)
    document["btn_osud"].unbind("click")
    document["btn_osud"].bind("click", on_osud)

    if not FACTS_READY:
        app <= card(tag("Načítavam…"), para("Pripájam mikro‑obsah (facts_chobotnica.json).", "small"))
        return

    if not state:
        app <= screen_setup()
        return

    phase = state.get("phase", "setup")
    if phase == "setup":
        app <= screen_setup()
    elif phase == "role_pass":
        app <= role_pass_screen(state)
        # bind start night button if present
        btn = document.select_one("#start_night")
        if btn:
            def start_night(ev=None):
                st = load()
                reset_night(st)
                st["phase"] = "night_turn"
                save(st)
                render()
            btn.bind("click", start_night)
    elif phase == "night_turn":
        app <= night_turn_screen(state)
    elif phase == "dawn":
        app <= dawn_screen(state)
    elif phase == "day_admin":
        app <= day_admin_screen(state)
    elif phase == "end":
        app <= end_screen(state)
    else:
        app <= card(tag("Chyba"), para("Neznáma fáza.", "small"))

# -------- Boot --------
load_facts()
render()