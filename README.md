# Farming Empire

A 2D management game built with **Python 3.12.10**, **Arcade 3.3.2**, and **SQLite**. You plant crops, place and upgrade factories (in Level 2), activate employees who move with **BFS** pathfinding to harvest fully grown crops, and gain periodic rewards every **60 seconds**. The game saves and loads complete snapshots to a local SQLite database.

---

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running the Game](#running-the-game)
- [How to Play](#how-to-play)
- [Mechanics & Rules](#mechanics--rules)
- [Save / Load](#save--load)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Credits](#credits)
- [License](#license)
- [Contact](#contact)

---

## Overview

**Farming Empire** is a single-player desktop game that demonstrates clean OOP design, a correct graph algorithm (BFS), resource management, and reliable persistence. The playfield is a centered **8×8 grid** with a fixed **Home** tile at **(0,0)** for employees. UI panels show resources, crops/factories, level goals, and available operations.

Key points:
- Auto-harvest runs every **60 seconds** and adds periodic rewards.
- Employees use **BFS** to take the shortest path to the assigned fully grown crop, harvest it, and return home.
- Level 1 focuses on crops. Level 2 unlocks factory placement, replacement, and upgrades.

---

## Features

- Centered **8×8** play grid with four UI panels (top resources, left crops/factories and Save/Quit, right instructions/goals, bottom operations).
- Crops: plant and replace; growth cycle ~50 seconds; after harvest the tile hides for ~2 seconds and then restarts growth.
- Factories: place, replace (immediate +3/+3/+3), and upgrade (L1→L2 increases periodic rewards).
- Employees: activate via Home, walk with BFS, harvest animation at the target, return to Home.
- Timers: 60-second global tick for periodic rewards; smooth per-frame movement and harvest animations.
- Persistence: register/login; save, list, and load snapshots (grid/resources/baselines/level) in SQLite.
- Clear separation: Views (UI) ↔ GameState (rules) ↔ SQLite (saves).

---

## Tech Stack

- Language: Python **3.12.10**
- 2D Framework: Arcade **3.3.2**
- Database: SQLite (**sqlite3** module)
- Imaging: Pillow (via Arcade)
- OS/Runtime: Desktop (tested on Windows; local only, no servers)

Dependencies are listed in `requirements.txt`.

---

## Project Structure

FarmingEmpire/
├─ main.py
├─ assets/
│ ├─ images/
│ └─ sounds/
├─ auth/
│ ├─ login.py
│ ├─ register.py
│ └─ user_model.py
├─ database/
│ ├─ db_setup.py
│ └─ game_data.db # auto-created at runtime if missing
├─ game/
│ ├─ banimations.py
│ ├─ cell.py
│ ├─ crops.py
│ ├─ employees.py
│ ├─ factories.py
│ ├─ game_state.py
│ └─ resources.py
├─ ui/
│ ├─ animations.py
│ ├─ drawing_helpers.py
│ ├─ game_menu_view.py
│ ├─ game_ui_utils.py
│ ├─ game_window.py
│ ├─ icons.py
│ ├─ login_view.py
│ ├─ menu_view.py
│ ├─ register_view.py
│ ├─ saves_view.py
│ └─ theme.py
├─ requirements.txt
└─ README.md


Assets: place PNG sprites in `assets/images/`. The employee sprite sheet should be a grid (2 columns × 12 rows); the game uses the **first 16 frames** for walking/harvesting. Include crop growth stage images and a Home icon.

---

## Setup & Installation

### 1) Create a virtual environment

Windows (PowerShell):
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1

macOS / Linux:

python3.12 -m venv .venv
source .venv/bin/activate

2) Install dependencies

pip install -r requirements.txt

3) First run creates the database

The game creates database/game_data.db at first run if it does not exist.
Running the Game

From the project root (with the virtual environment activated):

python main.py

An Arcade window titled “Farming Empire” will open.
How to Play

    Register or Login from the menu.

    Start New Game (or Load Game if you have a save).

    Level 1:

        Use Plant Crop on empty tiles (cost: 2/2/2 food/water/coins).

        Replace Crop to remove a crop (cost: 1/1/1).

        Reach Level 1 goals (plant ≥10 crops and earn ≥60 of each since L1 start) to unlock Level 2.

    Level 2:

        Place Factory (cost: 5/5/5), Replace Factory (instant +3/+3/+3), Upgrade Factory (cost: 10 × level; L1→L2 raises periodic reward).

        Employees: click Home (0,0) to arm → click a fully grown crop to assign a worker.

    Auto-harvest: every 60 seconds, rewards are added and a message lists the gains.

    Save at any time from the left panel. Quit via the UI.

Controls: mouse click on UI buttons and grid tiles.
Mechanics & Rules

    Grid: 8×8; the Home tile at (0,0) cannot host crops/factories.

    Costs: plant (2/2/2), replace crop (1/1/1), place factory (5/5/5), upgrade factory (10 × current level).

    Rewards: replace factory gives +3/+3/+3 immediately; periodic rewards on the 60s tick (factories: 2/2/2 at L1, 3/3/3 at L2).

    Growth: crops take about 50 seconds to fully grow; after harvest, the tile is invisible about 2 seconds, then restarts growth.

    Employees: +1 after two factory placements, −1 after two factory removals (not below 0). Typically, at most five workers are assigned at once for clarity.

    Pathfinding: BFS (4-directional) through empty tiles to the target crop; shortest path in an unweighted grid.

    Resource safety: all spending is guarded; counts never go negative.

Save / Load

    Save writes a full snapshot: level, resources, 8×8 grid, and per-level baselines.

    List Saves shows your saves (newest first).

    Load restores the snapshot exactly (including level and resources).

Database schema (simplified):

users(id PK, username UNIQUE, email, password)
saves(id PK, username, level, resources TEXT, grid TEXT, level1_start TEXT, level2_start TEXT, save_time DEFAULT CURRENT_TIMESTAMP)

Notes:

    Passwords are stored in plain text in this academic build.

    The link saves.username → users.username is enforced in code (no explicit foreign key).

Known Limitations

    Passwords are plain text (acceptable for course scope; to be hashed/salted in a production build).

    Saves store the grid/resources/baselines as JSON strings (good for snapshots; not ideal for SQL analytics).

    No explicit foreign key from saves.username to users.username (enforced in application logic).

    Basic BFS pathfinding; no collision avoidance between multiple workers (acceptable at 8×8 scale).

    No automated unit tests in the repository; testing is manual (see project report).

Roadmap

    Hash and salt passwords (e.g., bcrypt) and add login throttling.

    Add a foreign key for saves and consider normalizing grid cells for analytics.

    Switch to A* for larger/weighted maps; introduce a job queue with priorities and simple collision avoidance.

    Autosave, configurable save-slot limit, optional cloud sync.

    UX improvements: tutorial, tooltips, adjustable speeds, accessibility palette.

Credits

    Author: Umm E Farwa Leelani (etu55983)

    Professor: Huygens Adrien

    Institution: Henallux (academic project)

    Thanks: Open-source communities behind Python, Arcade, and SQLite.

License

Copyright © 2025 Umm E Farwa Leelani
This repository is provided for academic use. You may read and run the game locally. For other uses, please contact the author.
Contact

    Name: Umm E Farwa Leelani (etu55983)

    Email: etu55983@henallux.be