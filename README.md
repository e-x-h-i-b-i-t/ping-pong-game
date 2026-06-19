# Neon Ping Pong

A polished, high-performance, neon-themed Ping-Pong game written in Python using `tkinter` and managed with `uv`.

Now featuring an **AI Mode with Reinforcement Learning** that learns dynamically from matches against human players, alongside continuous self-play training and customizable round limits.

---

## Features

* **AI Opponent with Reinforcement Learning**: 
  - Implements a pure-Python Tabular Q-learning agent.
  - Dynamically discretizes relative positions, ball column slices, and velocity signs into state keys.
  - Continuous real-time updates and persistence in `ai_model.json`.
  - Supports exploration rate ($\epsilon$) decay over completed matches.
* **Continuous AI Self-Play Training**:
  - Headless-friendly training mode with up to 10x acceleration.
  - Automatically resets points back to `0 - 0` and serves immediately upon match completion to support unattended training loops.
* **Customizable Round Limits**:
  - Choose between `3`, `5`, `10`, `15`, or `21` rounds dynamically in the start menu.
  - The default limit is **5 rounds**.
* **Visual Polish & Particle Effects**:
  - Ambient drifting starfield particle system.
  - High-speed motion blur trail on the ball.
  - Contact spark debris bursts.
  - Fullscreen toggle via `F` / `F11`.
* **Zero-Lag Input Engine**: Double-buffered event binds track pressed states to eliminate OS keyboard repeat delay.

---

## How to Run the Game

This project runs inside a `uv` virtual environment.

### 1. Requirements
Ensure you have `uv` installed. If not:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Launching the Game
To run natively:
```bash
uv run python main.py
```
This command automatically sets up the environment, resolves dependencies, and starts the GUI.

---

## Control Layout

### Start Menu Controls
* **Navigate Options**: `W` / `S` or `Up` / `Down` arrows.
* **Cycle Round Limits**: Highlighting the `ROUND LIMIT` option and pressing `A` / `D` or `Left` / `Right` arrows (or `Space`) cycles target points (`3`, `5`, `10`, `15`, `21`).
* **Start Match**: Select a mode (`PVP`, `PLAYER VS AI`, `AI SELF-PLAY TRAINING`) and press `Spacebar`. Alternatively, press number keys `1`, `2`, or `3` to launch directly.

### Gameplay Controls

| Action | Player 1 (Left Paddle) | Player 2 (Right Paddle / AI) | Global / Training Controls |
| :--- | :--- | :--- | :--- |
| **Move Up** | `W` | `Up Arrow` (In PVP) | - |
| **Move Down** | `S` | `Down Arrow` (In PVP) | - |
| **Pause / Resume** | - | - | `Spacebar` |
| **Menu / Back** | - | - | `M` (When Paused or Game Over) |
| **Restart Game** | - | - | `R` (When Paused or Game Over) |
| **Cycle Window Sizes**| - | - | `V` |
| **Toggle Fullscreen** | - | - | `F` or `F11` |
| **Change Training Speed** | - | - | `+` / `-` keys (In Training Mode) |
| **Exit Game** | - | - | `Escape` or `Q` (Saves model weights) |
