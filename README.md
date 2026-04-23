🖥️ OLED Animation — Be My Baby
A Python simulation of a 128×64 OLED display running a cute animated face that lip-syncs to "Be My Baby" lyrics — all rendered pixel-by-pixel using Pygame.
No real hardware needed — runs on any laptop or PC!

✨ Features

📺 Simulated SSD1306 OLED screen with scanlines & pixel grid
🐾 Animated "pookie" face with 7+ eye expressions (uwu, heart, sparkle, wink...)
🎵 Synced lyrics that slide in with smooth transitions
💕 Floating hearts, twinkling stars & heartbeat pulse in the background
🎼 Animated music notes during intro
🖥️ Works on any screen size — auto-scales the display


🚀 Getting Started
1. Clone the repo
bashgit clone https://github.com/Aiden-Ferns/oled-animation.git
cd oled-animation
2. Install dependencies
bashpip install -r requirements.txt
3. Run it
bashpython Oled_animation.py

🎮 Controls
KeyActionGToggle pixel gridPPause / ResumeQ or EscQuit

🛠️ Customization
Want to change the song? Open Oled_animation.py and find the LYRICS list:
pythonLYRICS = [
    ( 8, "the night we met"),
    (10, "i needed you so"),
    ...
]
Each entry is (seconds_from_start, "lyric text") — swap them out for any song!

📦 Requirements

Python 3.7+
pygame


📸 Preview

A 128×64 pixel OLED simulator with a glowing bluish screen, PCB board design, pin headers, and a cute animated face reacting to lyrics.


Made with 💕 by Aiden-Ferns
