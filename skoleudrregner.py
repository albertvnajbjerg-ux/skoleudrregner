import json
import os
from collections import defaultdict
from datetime import date, datetime, time, timedelta

from flask import Flask

app = Flask(__name__)

MANEDER = [
    "januar",
    "februar",
    "marts",
    "april",
    "maj",
    "juni",
    "juli",
    "august",
    "september",
    "oktober",
    "november",
    "december",
]

UGEDAGE = [
    "Mandag",
    "Tirsdag",
    "Onsdag",
    "Torsdag",
    "Fredag",
    "Lørdag",
    "Søndag",
]

SKOLEFERIE = [
    ("Juleferie", date(2025, 12, 20), date(2026, 1, 4)),
    ("Vinterferie", date(2026, 2, 7), date(2026, 2, 15)),
    ("Påskeferie", date(2026, 3, 28), date(2026, 4, 6)),
    ("Kristi Himmelfartsferie", date(2026, 5, 14), date(2026, 5, 17)),
    ("Pinseferie", date(2026, 5, 23), date(2026, 5, 25)),
    ("Grundlovsdag", date(2026, 6, 5), date(2026, 6, 5)),
    ("Sommerferie", date(2026, 6, 27), date(2026, 8, 10)),
    ("Efterårsferie", date(2026, 10, 10), date(2026, 10, 18)),
]

SOMMERFERIE_START = datetime(2026, 6, 27, 0, 0, 0)

skema = {
    0: [
        ("08:00", "08:45", "Matematik", "HE"),
        ("08:45", "09:30", "Matematik", "HE"),
        ("10:00", "10:45", "Madkundskab", "SB"),
        ("10:45", "11:30", "Madkundskab", "SB"),
        ("12:15", "13:00", "Dansk", "SU"),
        ("13:00", "13:45", "Kristendom", "Louise"),
        ("13:45", "14:30", "Matematik", "HE"),
    ],
    1: [
        ("08:00", "08:45", "Historie", "JS"),
        ("08:45", "09:30", "Tysk", "AE"),
        ("10:00", "10:45", "Dansk", "SU"),
        ("10:45", "11:30", "Dansk", "SU"),
        ("12:15", "13:00", "Natur/Teknologi", "Louise"),
        ("13:00", "13:45", "Natur/Teknologi", "Louise"),
    ],
    2: [
        ("08:00", "08:45", "Dansk", "SU"),
        ("08:45", "09:30", "Dansk", "SU"),
        ("10:00", "10:45", "Historie", "JS"),
        ("10:45", "11:30", "Kristendom", "Louise"),
        ("12:15", "13:00", "Matematik", "HE"),
        ("13:00", "13:45", "Engelsk", "AE"),
    ],
    3: [
        ("08:00", "08:45", "Matematik", "HE"),
        ("08:45", "09:30", "Tysk", "AE"),
        ("10:00", "10:45", "Engelsk", "AE"),
        ("10:45", "11:30", "Engelsk", "AE"),
        ("12:15", "13:00", "Dansk", "SU"),
        ("13:00", "13:45", "Klassetime", "SU + HE"),
    ],
    4: [
        ("08:00", "08:45", "Håndværk/Design", "LR"),
        ("08:45", "09:30", "Håndværk/Design", "LR"),
        ("10:00", "10:45", "Billedkunst", "SD"),
        ("10:45", "11:30", "Billedkunst", "SD"),
        ("12:15", "13:00", "Idræt", "SB"),
        ("13:00", "13:45", "Idræt", "SB"),
    ],
}


def tid_obj(tid_str):
    return datetime.strptime(tid_str, "%H:%M").time()


def format_dato(dato_obj):
    return f"{dato_obj.day}. {MANEDER[dato_obj.month - 1]} {dato_obj.year}"


def format_kort_dato(dato_obj):
    return f"{dato_obj.day}. {MANEDER[dato_obj.month - 1]}"


def format_date_range(start_dato, slut_dato):
    if start_dato == slut_dato:
        return format_dato(start_dato)
    return f"{format_dato(start_dato)} - {format_dato(slut_dato)}"


def split_teachers(teacher_text):
    return [teacher.strip() for teacher in teacher_text.split("+")]


def is_holiday(dato_obj):
    for _, start, slut in SKOLEFERIE:
        if start <= dato_obj <= slut:
            return True
    return False


def is_school_day(dato_obj):
    return dato_obj.weekday() < 5 and not is_holiday(dato_obj) and dato_obj < SOMMERFERIE_START.date()


def get_day_end(dato_obj):
    dagsplan = skema.get(dato_obj.weekday(), [])
    if not dagsplan:
        return datetime.combine(dato_obj, time.min)
    return datetime.combine(dato_obj, tid_obj(dagsplan[-1][1]))


def format_duration(delta):
    total_seconds = max(0, int(delta.total_seconds()))
    dage = total_seconds // 86400
    timer = (total_seconds % 86400) // 3600
    minutter = (total_seconds % 3600) // 60
    sekunder = total_seconds % 60
    return dage, timer, minutter, sekunder


def format_countdown_text(dage, timer, minutter, sekunder):
    return f"{dage}d {timer}t {minutter}m {sekunder}s"


def format_time_text_from_seconds(total_seconds):
    total_seconds = max(0, int(total_seconds))
    timer = total_seconds // 3600
    minutter = (total_seconds % 3600) // 60
    sekunder = total_seconds % 60
    return f"{timer}t {minutter}m {sekunder}s"


def format_day_time_text_from_seconds(total_seconds):
    total_seconds = max(0, int(total_seconds))
    dage = total_seconds // 86400
    timer = (total_seconds % 86400) // 3600
    minutter = (total_seconds % 3600) // 60
    sekunder = total_seconds % 60
    return f"{dage}d {timer}t {minutter}m {sekunder}s"


def get_upcoming_free_periods(fra_dato):
    perioder = []
    for navn, start, slut in SKOLEFERIE:
        if start >= fra_dato and start < SOMMERFERIE_START.date():
            perioder.append((navn, start, slut))
    return perioder


def get_next_free_day(fra_tidspunkt):
    check_dato = fra_tidspunkt.date()
    if is_holiday(check_dato):
        return check_dato

    check_dato += timedelta(days=1)
    while check_dato <= SOMMERFERIE_START.date():
        if is_holiday(check_dato):
            return check_dato
        check_dato += timedelta(days=1)
    return None


def get_holiday_name_for_date(dato_obj):
    for navn, start, slut in SKOLEFERIE:
        if start <= dato_obj <= slut:
            return navn
    return "Fridag"


def get_time_until_next_free_day(fra_tidspunkt):
    next_free_day = get_next_free_day(fra_tidspunkt)
    if not next_free_day:
        return None, 0, 0, 0, 0

    next_free_start = datetime.combine(next_free_day, time.min)
    dage, timer, minutter, sekunder = format_duration(next_free_start - fra_tidspunkt)
    return next_free_day, dage, timer, minutter, sekunder


def get_school_days_until_summer(nu):
    remaining_days = 0
    check_dato = nu.date()

    while check_dato < SOMMERFERIE_START.date():
        if is_school_day(check_dato):
            if check_dato > nu.date():
                remaining_days += 1
            elif nu < get_day_end(check_dato):
                remaining_days += 1
        check_dato += timedelta(days=1)

    return remaining_days


def get_school_time_until_summer(nu):
    remaining_seconds = 0
    check_dato = nu.date()

    while check_dato < SOMMERFERIE_START.date():
        if is_school_day(check_dato):
            for start, slut, _, _ in skema.get(check_dato.weekday(), []):
                lektion_start = datetime.combine(check_dato, tid_obj(start))
                lektion_slut = datetime.combine(check_dato, tid_obj(slut))
                if lektion_slut <= nu:
                    continue

                remaining_seconds += int((lektion_slut - max(nu, lektion_start)).total_seconds())

        check_dato += timedelta(days=1)

    return remaining_seconds


def get_next_school_day_end(fra_tidspunkt):
    check_dato = fra_tidspunkt.date()

    while check_dato < SOMMERFERIE_START.date():
        if is_school_day(check_dato):
            day_end = get_day_end(check_dato)
            if check_dato > fra_tidspunkt.date() or day_end > fra_tidspunkt:
                return day_end
        check_dato += timedelta(days=1)

    return None


def get_teacher_counts_until_summer(nu):
    teacher_seconds = defaultdict(int)
    check_dato = nu.date()

    while check_dato < SOMMERFERIE_START.date():
        if is_school_day(check_dato):
            for start, slut, _, lærer in skema.get(check_dato.weekday(), []):
                lektion_start = datetime.combine(check_dato, tid_obj(start))
                lektion_slut = datetime.combine(check_dato, tid_obj(slut))
                if lektion_slut <= nu:
                    continue

                remaining_seconds = int((lektion_slut - max(nu, lektion_start)).total_seconds())

                for navn in split_teachers(lærer):
                    teacher_seconds[navn] += remaining_seconds

        check_dato += timedelta(days=1)

    return dict(sorted(teacher_seconds.items(), key=lambda item: (-item[1], item[0])))


def get_today_schedule_html(nu):
    dag = nu.weekday()
    dagens_html = ""
    current_subject = "Fri lige nu"
    current_teacher = ""
    next_subject = "Ingen flere fag i dag"
    next_subject_time = "Ingen flere fag i dag"
    next_subject_iso = ""
    tid_til_fri = "0t 0m 0s"

    if is_holiday(nu.date()):
        return (
            "<p class='status-message'>🌴 Skolen holder fri i dag</p>",
            "Ferie",
            "",
            "-",
            "Feriedag",
            "",
            "Nyd fridagen",
        )

    if dag >= 5:
        return (
            "<p class='status-message'>🎉 Det er weekend</p>",
            "Weekend",
            "",
            "-",
            "Weekend",
            "",
            "Weekendtid",
        )

    dagsplan = skema.get(dag, [])
    if not dagsplan:
        return "<p class='status-message'>Ingen fag i dag</p>", "Fri", "", "-", "Ingen skole i dag", "", "Ingen skole i dag"

    slut_dag = datetime.combine(nu.date(), tid_obj(dagsplan[-1][1]))
    if slut_dag > nu:
        timer, minutter, sekunder = 0, 0, 0
        _, timer, minutter, sekunder = format_duration(slut_dag - nu)
        tid_til_fri = f"{timer}t {minutter}m {sekunder}s"
    else:
        tid_til_fri = "Skoledagen er slut"

    next_subject = "Ingen flere fag i dag"

    for i, lektion in enumerate(dagsplan):
        start, slut, fag, lærer = lektion
        start_dt = datetime.combine(nu.date(), tid_obj(start))
        slut_dt = datetime.combine(nu.date(), tid_obj(slut))
        aktiv = ""

        if start_dt <= nu <= slut_dt:
            aktiv = "active"
            current_subject = fag
            current_teacher = lærer
            if i + 1 < len(dagsplan):
                next_subject = dagsplan[i + 1][2]
                next_subject_time = f"Starter kl. {dagsplan[i + 1][0]}"
                next_subject_iso = datetime.combine(nu.date(), tid_obj(dagsplan[i + 1][0])).isoformat()
        elif nu < start_dt and current_subject == "Fri lige nu":
            current_subject = "Pause før næste time"
            current_teacher = ""
            next_subject = fag
            next_subject_time = f"Starter kl. {start}"
            next_subject_iso = start_dt.isoformat()

        dagens_html += f"""
        <div class="lesson {aktiv}">
            <div>
                <strong>{fag}</strong>
                <span class="teacher">{lærer}</span>
            </div>
            <div class="time">{start} - {slut}</div>
        </div>
        """

    if nu > slut_dag:
        current_subject = "Fri efter skole"
        current_teacher = ""

    return dagens_html, current_subject, current_teacher, next_subject, next_subject_time, next_subject_iso, tid_til_fri


def build_week_schedule():
    sections = []
    for dag_num in range(5):
        dag_navn = UGEDAGE[dag_num]
        lektioner_html = ""

        for start, slut, fag, lærer in skema.get(dag_num, []):
            lektioner_html += f"""
            <div class="week-lesson">
                <div>
                    <strong>{fag}</strong>
                    <span class="teacher">{lærer}</span>
                </div>
                <div class="time">{start} - {slut}</div>
            </div>
            """

        sections.append(
            f"""
            <button class="accordion-button" type="button" onclick="toggleDay({dag_num})">
                <span>{dag_navn}</span>
                <span class="accordion-icon">+</span>
            </button>
            <div id="day-{dag_num}" class="accordion-panel">
                {lektioner_html}
            </div>
            """
        )

    return "\n".join(sections)


def build_teacher_cards(nu):
    cards = []
    active_teachers = set()

    if nu.weekday() < 5 and not is_holiday(nu.date()):
        for start, slut, _, lærer in skema.get(nu.weekday(), []):
            start_dt = datetime.combine(nu.date(), tid_obj(start))
            slut_dt = datetime.combine(nu.date(), tid_obj(slut))
            if start_dt <= nu <= slut_dt:
                active_teachers.update(split_teachers(lærer))

    for lærer, sekunder in get_teacher_counts_until_summer(nu).items():
        is_active = "true" if lærer in active_teachers else "false"
        cards.append(
            f"""
            <div class="teacher-card">
                <div class="teacher-name">{lærer}</div>
                <div class="teacher-count" data-seconds="{sekunder}" data-active="{is_active}">{format_time_text_from_seconds(sekunder)}</div>
                <div class="teacher-label">undervisning tilbage</div>
            </div>
            """
        )
    return "\n".join(cards)


def build_free_period_list(nu):
    items = []
    for navn, start, slut in get_upcoming_free_periods(nu.date()):
        items.append(
            f"""
            <div class="holiday-item">
                <strong>{navn}</strong>
                <span>{format_date_range(start, slut)}</span>
            </div>
            """
        )
    if not items:
        return "<p class='small'>Der er ingen ekstra fridage tilbage før sommerferien.</p>"
    return "\n".join(items)


@app.route("/")
def home():
    nu = datetime.now()
    dag_index = nu.weekday()
    dagens_navn = UGEDAGE[dag_index]

    dagens_html, current_subject, current_teacher, next_subject, next_subject_time, next_subject_iso, tid_til_fri = get_today_schedule_html(nu)
    next_free_day, next_free_days, next_free_hours, next_free_minutes, next_free_seconds = get_time_until_next_free_day(nu)
    next_free_text = format_kort_dato(next_free_day) if next_free_day else "Ingen fundet"
    next_free_name = get_holiday_name_for_date(next_free_day) if next_free_day else "Ingen kommende fridag"
    next_free_iso = datetime.combine(next_free_day, time.min).isoformat() if next_free_day else ""

    dage_til_sommer, timer_til_sommer, min_til_sommer, sek_til_sommer = format_duration(SOMMERFERIE_START - nu)
    uger_til_sommer = dage_til_sommer // 7
    total_sekunder_til_sommer = int((SOMMERFERIE_START - nu).total_seconds())
    total_timer_til_sommer = total_sekunder_til_sommer // 3600
    total_minutter_til_sommer = total_sekunder_til_sommer // 60
    school_days_left = get_school_days_until_summer(nu)
    next_school_day_end = get_next_school_day_end(nu)
    next_school_day_end_iso = next_school_day_end.isoformat() if next_school_day_end else ""
    day_end = None
    if dag_index < 5 and not is_holiday(nu.date()):
        potential_day_end = get_day_end(nu.date())
        if potential_day_end > nu:
            day_end = potential_day_end
    day_end_iso = day_end.isoformat() if day_end else ""

    free_period_html = build_free_period_list(nu)
    teacher_cards_html = build_teacher_cards(nu)
    week_schedule_html = build_week_schedule()

    html = f"""
    <html>
    <head>
        <title>Skole Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            :root {{
                --bg: #0a1220;
                --bg-soft: #111c30;
                --card: rgba(15, 28, 48, 0.92);
                --line: rgba(122, 164, 255, 0.22);
                --text: #edf4ff;
                --muted: #99accf;
                --accent: #7cf3c8;
                --accent-2: #74b9ff;
                --warm: #ffd36b;
            }}

            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                min-height: 100vh;
                color: var(--text);
                font-family: "Segoe UI", Arial, sans-serif;
                background:
                    radial-gradient(circle at top left, rgba(116, 185, 255, 0.24), transparent 30%),
                    radial-gradient(circle at top right, rgba(124, 243, 200, 0.18), transparent 26%),
                    linear-gradient(160deg, #08111e 0%, #0c1628 48%, #132443 100%);
                padding: 24px;
            }}

            .page {{
                max-width: 1300px;
                margin: 0 auto;
            }}

            h1 {{
                margin: 0 0 10px;
                font-size: clamp(30px, 4vw, 48px);
                color: white;
            }}

            .subtitle {{
                color: var(--muted);
                margin-bottom: 24px;
                font-size: 18px;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 18px;
            }}

            .card {{
                background: var(--card);
                border: 1px solid var(--line);
                border-radius: 24px;
                padding: 22px;
                backdrop-filter: blur(12px);
                box-shadow: 0 16px 50px rgba(0, 0, 0, 0.25);
            }}

            .title {{
                font-size: 14px;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: var(--accent);
                margin-bottom: 12px;
            }}

            .big {{
                font-size: clamp(28px, 3vw, 40px);
                font-weight: 700;
                line-height: 1.1;
            }}

            .small {{
                color: var(--muted);
                margin-top: 10px;
                font-size: 16px;
            }}

            .countdown {{
                color: var(--warm);
                font-size: 26px;
                font-weight: 700;
                margin-top: 8px;
            }}

            .section {{
                margin-top: 22px;
            }}

            .lesson,
            .week-lesson,
            .holiday-item {{
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 16px;
                padding: 14px 16px;
                margin-bottom: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 16px;
            }}

            .lesson strong,
            .week-lesson strong,
            .holiday-item strong {{
                display: block;
                font-size: 18px;
            }}

            .teacher {{
                display: block;
                color: var(--muted);
                margin-top: 4px;
            }}

            .time {{
                color: var(--accent-2);
                white-space: nowrap;
                font-weight: 600;
            }}

            .active {{
                border-color: rgba(124, 243, 200, 0.8);
                box-shadow: 0 0 0 1px rgba(124, 243, 200, 0.2), 0 0 24px rgba(124, 243, 200, 0.18);
            }}

            .status-message {{
                text-align: center;
                font-size: 24px;
                color: var(--warm);
                margin: 10px 0 0;
            }}

            .free-days {{
                display: grid;
                gap: 10px;
            }}

            .accordion {{
                display: grid;
                gap: 12px;
            }}

            .accordion-button {{
                width: 100%;
                border: 1px solid var(--line);
                background: rgba(255, 255, 255, 0.05);
                color: var(--text);
                border-radius: 18px;
                padding: 16px 18px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 18px;
                font-weight: 700;
                cursor: pointer;
            }}

            .accordion-button.active-button {{
                border-color: rgba(116, 185, 255, 0.7);
                background: rgba(116, 185, 255, 0.12);
            }}

            .accordion-icon {{
                color: var(--accent);
                font-size: 28px;
                line-height: 1;
            }}

            .accordion-panel {{
                display: none;
                padding: 2px 2px 6px;
            }}

            .accordion-panel.open {{
                display: block;
            }}

            .teachers-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 14px;
            }}

            .teacher-card {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 18px;
                padding: 18px 14px;
                text-align: center;
            }}

            .teacher-name {{
                font-size: 18px;
                font-weight: 700;
            }}

            .teacher-count {{
                font-size: 34px;
                font-weight: 800;
                color: var(--accent);
                margin-top: 8px;
            }}

            .teacher-label {{
                color: var(--muted);
                font-size: 14px;
            }}

            .fun-stat {{
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                padding: 8px 0;
            }}
            .fun-stat .big {{
                font-size: 24px;
            }}

            @media (max-width: 720px) {{
                body {{
                    padding: 16px;
                }}

                .lesson,
                .week-lesson,
                .holiday-item {{
                    flex-direction: column;
                    align-items: flex-start;
                }}

                .time {{
                    white-space: normal;
                }}
            }}
        </style>
        <script>
            function setOpenDay(dayIndex) {{
                const panels = document.querySelectorAll('.accordion-panel');
                const buttons = document.querySelectorAll('.accordion-button');

                panels.forEach(panel => panel.classList.remove('open'));
                buttons.forEach(button => {{
                    button.classList.remove('active-button');
                    button.querySelector('.accordion-icon').textContent = '+';
                }});

                if (dayIndex >= 0 && dayIndex < panels.length) {{
                    const target = document.getElementById(`day-${{dayIndex}}`);
                    const targetButton = buttons[dayIndex];
                    target.classList.add('open');
                    targetButton.classList.add('active-button');
                    targetButton.querySelector('.accordion-icon').textContent = '−';
                }}
            }}

            function toggleDay(dayIndex) {{
                const target = document.getElementById(`day-${{dayIndex}}`);
                const isOpen = target.classList.contains('open');

                if (isOpen) {{
                    localStorage.removeItem('openScheduleDay');
                    setOpenDay(-1);
                    return;
                }}

                localStorage.setItem('openScheduleDay', String(dayIndex));
                setOpenDay(dayIndex);
            }}

            function formatRemaining(targetDate) {{
                const diffMs = targetDate.getTime() - Date.now();
                if (diffMs <= 0) {{
                    return {{ days: 0, hours: 0, minutes: 0, seconds: 0, expired: true }};
                }}

                const totalSeconds = Math.floor(diffMs / 1000);
                const days = Math.floor(totalSeconds / 86400);
                const hours = Math.floor((totalSeconds % 86400) / 3600);
                const minutes = Math.floor((totalSeconds % 3600) / 60);
                const seconds = totalSeconds % 60;
                return {{ days, hours, minutes, seconds, expired: false }};
            }}

            function bindCountdown(elementId, options = {{}}) {{
                const element = document.getElementById(elementId);
                if (!element) {{
                    return;
                }}

                const targetIso = element.dataset.target;
                if (!targetIso) {{
                    return;
                }}

                const targetDate = new Date(targetIso);
                const showDays = options.showDays !== false;
                const expiredText = options.expiredText || '0d 0t 0m 0s';

                function render() {{
                    const remaining = formatRemaining(targetDate);

                    if (remaining.expired) {{
                        element.textContent = expiredText;
                        return;
                    }}

                    if (showDays) {{
                        element.textContent = `${{remaining.days}}d ${{remaining.hours}}t ${{remaining.minutes}}m ${{remaining.seconds}}s`;
                    }} else {{
                        const totalHours = remaining.days * 24 + remaining.hours;
                        element.textContent = `${{totalHours}}t ${{remaining.minutes}}m ${{remaining.seconds}}s`;
                    }}
                }}

                render();
                setInterval(render, 1000);
            }}

            function bindTeacherTimers() {{
                const elements = document.querySelectorAll('.teacher-count[data-seconds]');

                function render() {{
                    elements.forEach(element => {{
                        const currentSeconds = Math.max(0, Number(element.dataset.seconds || '0'));
                        const isActive = element.dataset.active === 'true';
                        const hours = Math.floor(currentSeconds / 3600);
                        const minutes = Math.floor((currentSeconds % 3600) / 60);
                        const seconds = currentSeconds % 60;
                        element.textContent = `${{hours}}t ${{minutes}}m ${{seconds}}s`;
                        if (isActive && currentSeconds > 0) {{
                            element.dataset.seconds = String(currentSeconds - 1);
                        }}
                    }});
                }}

                render();
                setInterval(render, 1000);
            }}

            function updateClock() {{
                const now = new Date();
                document.getElementById('live-clock').textContent =
                    String(now.getHours()).padStart(2, '0') + ':' +
                    String(now.getMinutes()).padStart(2, '0') + ':' +
                    String(now.getSeconds()).padStart(2, '0');
            }}

            const SOMMERFERIE_START_ISO = "{SOMMERFERIE_START.isoformat()}";

            function renderSummerFunStats() {{
                const targetDate = new Date(SOMMERFERIE_START_ISO);

                function tick() {{
                    const diffMs = targetDate.getTime() - Date.now();
                    const s = Math.max(0, Math.floor(diffMs / 1000));

                    const weeksEl = document.getElementById('summer-weeks');
                    const hoursEl = document.getElementById('stat-hours');
                    const minsEl = document.getElementById('stat-minutes');
                    const secsEl = document.getElementById('stat-seconds');

                    if (weeksEl) weeksEl.textContent = Math.floor(s / 604800);
                    if (hoursEl) hoursEl.textContent = Math.floor(s / 3600).toLocaleString();
                    if (minsEl) minsEl.textContent = Math.floor(s / 60).toLocaleString();
                    if (secsEl) secsEl.textContent = s.toLocaleString();
                }}

                tick();
                setInterval(tick, 1000);
            }}

            window.onload = () => {{
                const todayIndex = {min(max(dag_index, 0), 4)};
                const savedValue = localStorage.getItem('openScheduleDay');
                const savedIndex = savedValue === null ? todayIndex : Number(savedValue);
                setOpenDay(Number.isInteger(savedIndex) ? savedIndex : todayIndex);
                bindCountdown('next-subject-countdown', {{ showDays: false, expiredText: '0t 0m 0s' }});
                bindCountdown('time-until-free', {{ showDays: false, expiredText: 'Skoledagen er slut' }});
                bindCountdown('next-free-countdown', {{ showDays: true, expiredText: '0d 0t 0m 0s' }});
                bindCountdown('summer-countdown', {{ showDays: true, expiredText: 'Sommerferie!' }});
                bindCountdown('school-days-countdown', {{ showDays: true, expiredText: '0d 0t 0m 0s' }});
                bindTeacherTimers();
                renderSummerFunStats();
                updateClock();
                setInterval(updateClock, 1000);
            }};
        </script>
    </head>
    <body>
        <div class="page">
            <h1>Skole Dashboard</h1>
            <div class="subtitle">
                {dagens_navn} • {format_dato(nu.date())} kl. <span id="live-clock">{nu.strftime("%H:%M:%S")}</span>
            </div>

            <div class="grid">
                <div class="card">
                    <div class="title">Lige nu</div>
                    <div class="big">{current_subject}</div>
                    <div class="small">{current_teacher}</div>
                </div>

                <div class="card">
                    <div class="title">Næste fag</div>
                    <div class="big">{next_subject}</div>
                    <div class="small">{next_subject_time}</div>
                    <div class="countdown" id="next-subject-countdown" data-target="{next_subject_iso}">0t 0m 0s</div>
                </div>

                <div class="card">
                    <div class="title">Tid til fri i dag</div>
                    <div class="big" id="time-until-free" data-target="{day_end_iso}">{tid_til_fri}</div>
                </div>

                <div class="card">
                    <div class="title">Næste ferie/fridag</div>
                    <div class="big">{next_free_text}</div>
                    <div class="small">{next_free_name}</div>
                    <div class="countdown" id="next-free-countdown" data-target="{next_free_iso}">{format_countdown_text(next_free_days, next_free_hours, next_free_minutes, next_free_seconds)}</div>
                </div>

                <div class="card">
                    <div class="title">Tid til sommerferien</div>
                    <div class="big">{dage_til_sommer} dage</div>
                    <div class="small"><span id="summer-weeks">{uger_til_sommer}</span> uger</div>
                    <div class="countdown" id="summer-countdown" data-target="{SOMMERFERIE_START.isoformat()}">{timer_til_sommer}t {min_til_sommer}m {sek_til_sommer}s</div>
                </div>

                <div class="card">
                    <div class="title">Skoledage til sommerferien</div>
                    <div class="big">{school_days_left}</div>
                    <div class="countdown" id="school-days-countdown" data-target="{next_school_day_end_iso}">{format_countdown_text(*format_duration(next_school_day_end - nu)) if next_school_day_end else "0d 0t 0m 0s"}</div>
                    <div class="small">Tid til der er 1 skoledag mindre</div>
                </div>
            </div>

            <div class="section card">
                <div class="title">Sjove nedtællinger</div>
                <div id="summer-fun-stats">
                    <div class="fun-stat">
                        <span class="big" id="stat-hours">{total_timer_til_sommer:,}</span>
                        <span class="small">timer til sommerferien</span>
                    </div>
                    <div class="fun-stat">
                        <span class="big" id="stat-minutes">{total_minutter_til_sommer:,}</span>
                        <span class="small">minutter til sommerferien</span>
                    </div>
                    <div class="fun-stat">
                        <span class="big" id="stat-seconds">{total_sekunder_til_sommer:,}</span>
                        <span class="small">sekunder til sommerferien</span>
                    </div>
                </div>
            </div>

            <div class="section card">
                <div class="title">Dagens skema</div>
                {dagens_html}
            </div>

            <div class="section card">
                <div class="title">Fridage før sommerferien</div>
                <div class="free-days">{free_period_html}</div>
            </div>

            <div class="section card">
                <div class="title">Ugens skema</div>
                <div class="accordion">{week_schedule_html}</div>
            </div>

            <div class="section card">
                <div class="title">Lærere til sommerferien</div>
                <div class="small">Resterende undervisningstid med hver lærer fra nu og frem til sommerferien.</div>
                <div class="teachers-grid" style="margin-top: 16px;">{teacher_cards_html}</div>
            </div>
        </div>
    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    host = os.getenv("SKOLEUDREGNER_HOST", "127.0.0.1")
    port = int(os.getenv("SKOLEUDREGNER_PORT", "5001"))
    app.run(host=host, port=port, debug=False)
