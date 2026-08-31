"""Run Browser — a small app that turns robot-run CSVs into an interactive
dashboard page.

Modules (each editable on its own):
    config.py    every tunable option and threshold
    analysis.py  the metrics: tracking, contacts, grasps, chunk profile
    template.py  the page: HTML, CSS, JS
    builder.py   glue: files -> analysis -> page
    app.py       the desktop window (folder/file picker)
"""
