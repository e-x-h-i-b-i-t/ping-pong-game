import tkinter as tk
import math
import random
from rl_agent import RLAgent

# Game constants
FPS = 60

class Paddle:
    def __init__(self, canvas, x, y, width, height, color, glow_color, speed):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.speed = speed
        
        # Draw glow rectangle underneath
        self.glow_id = self.canvas.create_rectangle(
            x - 3, y - 3, x + width + 3, y + height + 3,
            fill="", outline=glow_color, width=3
        )
        # Draw main paddle
        self.rect_id = self.canvas.create_rectangle(
            x, y, x + width, y + height,
            fill=color, outline="#ffffff", width=1.5
        )

    def move(self, dy, min_y, max_y):
        # Get coordinates of main paddle
        x1, y1, x2, y2 = self.canvas.coords(self.rect_id)
        
        # Adjust dy if it exceeds boundaries
        if dy < 0:  # Upwards
            if y1 + dy < min_y:
                dy = min_y - y1
        elif dy > 0:  # Downwards
            if y2 + dy > max_y:
                dy = max_y - y2
                
        if dy != 0:
            self.canvas.move(self.rect_id, 0, dy)
            self.canvas.move(self.glow_id, 0, dy)

    def reset_position(self, x, y):
        # Move paddle back to its starting coordinate
        self.canvas.coords(self.rect_id, x, y, x + self.width, y + self.height)
        self.canvas.coords(self.glow_id, x - 3, y - 3, x + self.width + 3, y + self.height + 3)

    def resize(self, x, y, width, height, speed):
        self.width = width
        self.height = height
        self.speed = speed
        self.canvas.coords(self.rect_id, x, y, x + width, y + height)
        self.canvas.coords(self.glow_id, x - 3, y - 3, x + width + 3, y + height + 3)


class Ball:
    def __init__(self, canvas, x, y, r, color, glow_color, base_speed):
        self.canvas = canvas
        self.r = r
        self.dx = 0
        self.dy = 0
        self.base_speed = base_speed
        
        # Draw glow circle
        self.glow_id = self.canvas.create_oval(
            x - r - 3, y - r - 3, x + r + 3, y + r + 3,
            fill="", outline=glow_color, width=3
        )
        # Draw main ball
        self.rect_id = self.canvas.create_oval(
            x - r, y - r, x + r, y + r,
            fill=color, outline="#ffffff", width=1.5
        )

    def reset(self, x, y):
        self.dx = 0
        self.dy = 0
        self.canvas.coords(self.rect_id, x - self.r, y - self.r, x + self.r, y + self.r)
        self.canvas.coords(self.glow_id, x - self.r - 3, y - self.r - 3, x + self.r + 3, y + self.r + 3)

    def serve(self, direction):
        # direction: 1 (right) or -1 (left)
        self.dx = direction * self.base_speed
        # Random starting vertical direction
        self.dy = random.choice([-3.0, -1.5, 1.5, 3.0])

    def move(self):
        self.canvas.move(self.rect_id, self.dx, self.dy)
        self.canvas.move(self.glow_id, self.dx, self.dy)

    def get_coords(self):
        x1, y1, x2, y2 = self.canvas.coords(self.rect_id)
        return (x1 + x2) / 2, (y1 + y2) / 2

    def resize(self, x, y, r, base_speed):
        self.r = r
        self.base_speed = base_speed
        self.canvas.coords(self.rect_id, x - r, y - r, x + r, y + r)
        self.canvas.coords(self.glow_id, x - r - 3, y - r - 3, x + r + 3, y + r + 3)



class PingPongGame:
    STATE_START = "START"
    STATE_PLAYING = "PLAYING"
    STATE_PAUSED = "PAUSED"
    STATE_GAMEOVER = "GAMEOVER"

    def __init__(self, root):
        self.root = root
        self.root.title("Neon Ping Pong")
        
        # Windowed Mode Setup (resizable, default 1400x900)
        self.width = 1400
        self.height = 900
        
        # Dynamic playable arena offsets (relative to screen height)
        self.top_offset = int(self.height * 0.08)
        self.bottom_offset = int(self.height * 0.04)
        
        # Center the window on the screen
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x_coord = (screen_w - self.width) // 2
        y_coord = (screen_h - self.height) // 2
        self.root.geometry(f"{self.width}x{self.height}+{x_coord}+{y_coord}")
        self.root.resizable(False, False)

        # Dynamic Scaling factors
        self.paddle_width = max(15, int(self.width * 0.012))
        self.paddle_height = max(100, int(self.height * 0.2))
        self.ball_radius = max(8, int(self.width * 0.008))
        self.ball_base_speed = max(9.0, self.width / 140.0)
        self.paddle_speed = max(10.0, self.height / 75.0)

        # Home Positions for Paddles (centered vertically within playable arena limits)
        self.p1_home_x = int(self.width * 0.05)
        self.p2_home_x = int(self.width * 0.95) - self.paddle_width
        self.p_home_y = self.top_offset + (self.height - self.top_offset - self.bottom_offset - self.paddle_height) // 2

        # Setup Canvas
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="#0d0e15", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Score Tracking
        self.p1_score = 0
        self.p2_score = 0
        self.state = self.STATE_START
        self.ball_active = False
        self.particles = []
        self.trail = []
        self.stars = []
        self.overlay_ids = []
        self.blink_text_id = None
        self.blink_state = True

        # RL Agent Setup
        self.agent = RLAgent()
        self.menu_selection = 1  # Default to VS AI mode
        self.game_mode = "AI"    # PVP, AI, or TRAIN
        self.winning_score = 5   # Dynamic winning score limit (default: 5 rounds)
        self.training_speed = 3   # Acceleration multiplier for training
        self.last_state = None
        self.last_action = None
        self.telemetry_ids = []

        # Input keys state
        self.keys_pressed = {
            "w": False,
            "s": False,
            "up": False,
            "down": False
        }

        # Color palette definition for trails
        self.TRAIL_COLORS = [
            "#ccff00", "#b3e000", "#99c200", "#80a300", 
            "#668200", "#4d6100", "#334100", "#1a2000"
        ]

        self.setup_background_stars()
        self.setup_arena()
        self.create_game_objects()
        self.bind_events()
        
        # Start core loops
        self.toggle_blink()
        self.draw_overlay()
        self.tick()

    def setup_background_stars(self):
        # Create drifting ambient space particles
        for _ in range(40):
            sx = random.randint(0, self.width)
            sy = random.randint(25, self.height - 25)
            r = random.randint(1, 3)
            # Faint neon blue/purple stars
            color = random.choice(["#141624", "#1b1d30", "#21243d"])
            sid = self.canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill=color, outline="")
            self.stars.append({
                "id": sid,
                "speed": random.uniform(0.3, 1.2),
                "r": r
            })

    def setup_arena(self):
        # Draw background scores (large, faint digits)
        self.bg_score_p1 = self.canvas.create_text(
            self.width // 4, self.height // 2, text="0", font=("Helvetica", -int(self.height * 0.22), "bold"),
            fill="#161823", state="normal"
        )
        self.bg_score_p2 = self.canvas.create_text(
            3 * self.width // 4, self.height // 2, text="0", font=("Helvetica", -int(self.height * 0.22), "bold"),
            fill="#161823", state="normal"
        )

        # Draw central divider (net)
        self.net_id = self.canvas.create_line(
            self.width // 2, self.top_offset, self.width // 2, self.height - self.bottom_offset,
            fill="#1d2030", dash=(15, 15), width=3
        )

        # Draw borders (top and bottom limits)
        self.border_top_id = self.canvas.create_line(20, self.top_offset, self.width - 20, self.top_offset, fill="#252836", width=3)
        self.border_bottom_id = self.canvas.create_line(20, self.height - self.bottom_offset, self.width - 20, self.height - self.bottom_offset, fill="#252836", width=3)

    def create_game_objects(self):
        # Create left paddle off-screen for slide-in animation
        self.paddle_left = Paddle(
            self.canvas,
            x=-100, y=self.p_home_y,
            width=self.paddle_width, height=self.paddle_height,
            color="#00f0ff", glow_color="#005b66",
            speed=self.paddle_speed
        )
        
        # Create right paddle off-screen for slide-in animation
        self.paddle_right = Paddle(
            self.canvas,
            x=self.width + 100, y=self.p_home_y,
            width=self.paddle_width, height=self.paddle_height,
            color="#ff007f", glow_color="#8a0043",
            speed=self.paddle_speed
        )

        # Ball (Retro Yellow-Green)
        self.ball = Ball(
            self.canvas,
            x=self.width // 2, y=self.height // 2,
            r=self.ball_radius,
            color="#ccff00", glow_color="#6b8000",
            base_speed=self.ball_base_speed
        )

    def bind_events(self):
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        
        # Exit binds (Escape or Q keys) via self.on_exit
        self.root.bind("<Escape>", lambda e: self.on_exit())
        self.root.bind("<q>", lambda e: self.on_exit())
        self.root.bind("<Q>", lambda e: self.on_exit())
        
        # Handle standard OS window manager "X" close button
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        
        self.canvas.focus_set()


    def on_key_press(self, event):
        key = event.keysym.lower()
        
        # If in start screen, capture menu selection keys
        if self.state == self.STATE_START:
            if key in ["w", "up"]:
                self.menu_selection = (self.menu_selection - 1) % 4
                self.draw_menu()
                return
            elif key in ["s", "down"]:
                self.menu_selection = (self.menu_selection + 1) % 4
                self.draw_menu()
                return
            elif key in ["a", "left"] and self.menu_selection == 3:
                presets = [3, 5, 10, 15, 21]
                idx = presets.index(self.winning_score)
                self.winning_score = presets[(idx - 1) % len(presets)]
                self.draw_menu()
                return
            elif key in ["d", "right"] and self.menu_selection == 3:
                presets = [3, 5, 10, 15, 21]
                idx = presets.index(self.winning_score)
                self.winning_score = presets[(idx + 1) % len(presets)]
                self.draw_menu()
                return
            elif key in ["1", "2", "3"]:
                self.menu_selection = int(key) - 1
                self.draw_menu()
                self.handle_space_press()
                return

        # Training speed control
        if self.state == self.STATE_PLAYING and self.game_mode == "TRAIN":
            if key in ["plus", "equal", "kp_add"]:
                self.training_speed = min(10, self.training_speed + 1)
                self.update_telemetry()
                return
            elif key in ["minus", "underscore", "kp_subtract"]:
                self.training_speed = max(1, self.training_speed - 1)
                self.update_telemetry()
                return

        # Return to main menu from pause/gameover
        if key == "m" and self.state in [self.STATE_PAUSED, self.STATE_GAMEOVER]:
            self.return_to_menu()
            return

        if key in self.keys_pressed:
            self.keys_pressed[key] = True
        elif event.keysym == "Up":
            self.keys_pressed["up"] = True
        elif event.keysym == "Down":
            self.keys_pressed["down"] = True
        
        # Handle state transition key triggers
        if event.keysym == "space":
            self.handle_space_press()
        elif key == "r":
            if self.state in [self.STATE_PAUSED, self.STATE_GAMEOVER]:
                self.reset_game()

    def on_key_release(self, event):
        key = event.keysym.lower()
        if key in self.keys_pressed:
            self.keys_pressed[key] = False
        elif event.keysym == "Up":
            self.keys_pressed["up"] = False
        elif event.keysym == "Down":
            self.keys_pressed["down"] = False

    def handle_space_press(self):
        if self.state == self.STATE_START:
            if self.menu_selection == 3:
                presets = [3, 5, 10, 15, 21]
                idx = presets.index(self.winning_score)
                self.winning_score = presets[(idx + 1) % len(presets)]
                self.draw_menu()
                return
                
            # Set mode based on menu selection
            if self.menu_selection == 0:
                self.game_mode = "PVP"
            elif self.menu_selection == 1:
                self.game_mode = "AI"
            else:
                self.game_mode = "TRAIN"
                
            self.clear_overlay()
            self.last_state = None
            self.last_action = None
            self.state = self.STATE_PLAYING
            
            # Setup HUD telemetry
            self.draw_telemetry()
            self.trigger_serve(random.choice([-1, 1]))
        elif self.state == self.STATE_PLAYING:
            self.state = self.STATE_PAUSED
            self.draw_overlay()
        elif self.state == self.STATE_PAUSED:
            self.clear_overlay()
            self.state = self.STATE_PLAYING

    def reset_game(self):
        self.p1_score = 0
        self.p2_score = 0
        self.canvas.itemconfig(self.bg_score_p1, text="0")
        self.canvas.itemconfig(self.bg_score_p2, text="0")
        
        self.paddle_left.reset_position(self.p1_home_x, self.p_home_y)
        self.paddle_right.reset_position(self.p2_home_x, self.p_home_y)
        
        self.clear_overlay()
        self.last_state = None
        self.last_action = None
        self.state = self.STATE_PLAYING
        
        self.draw_telemetry()
        self.trigger_serve(random.choice([-1, 1]))

    def trigger_serve(self, direction):
        self.ball_active = False
        self.ball.reset(self.width // 2, self.height // 2)
        self.last_state = None
        self.last_action = None
        
        # Serve faster in training mode to maximize match throughput
        delay = 200 if self.game_mode == "TRAIN" else 1000
        self.root.after(delay, lambda: self.serve_ball(direction))

    def serve_ball(self, direction):
        if self.state == self.STATE_PLAYING:
            self.ball.serve(direction)
            self.ball_active = True

    def update_paddles(self):
        # Update Left Paddle
        if self.game_mode == "TRAIN":
            # Heuristic for left paddle: only track ball when it is approaching (ball_dx < 0).
            # Tracking at all times makes the opponent unrealistically perfect and skews training.
            bx, by = self.ball.get_coords()
            ball_dx = self.ball.dx
            if ball_dx < 0:  # ball moving toward left paddle
                px1, py1, px2, py2 = self.canvas.coords(self.paddle_left.rect_id)
                py_mid = (py1 + py2) / 2.0
                if by < py_mid - 15:
                    self.paddle_left.move(-self.paddle_left.speed, self.top_offset + 2, self.height - self.bottom_offset - 2)
                elif by > py_mid + 15:
                    self.paddle_left.move(self.paddle_left.speed, self.top_offset + 2, self.height - self.bottom_offset - 2)
        else:
            if self.keys_pressed["w"]:
                self.paddle_left.move(-self.paddle_left.speed, self.top_offset + 2, self.height - self.bottom_offset - 2)
            if self.keys_pressed["s"]:
                self.paddle_left.move(self.paddle_left.speed, self.top_offset + 2, self.height - self.bottom_offset - 2)

        # Update Right Paddle
        if self.game_mode in ["AI", "TRAIN"]:
            bx, by = self.ball.get_coords()
            ball_dx, ball_dy = self.ball.dx, self.ball.dy
            px1, py1, px2, py2 = self.canvas.coords(self.paddle_right.rect_id)
            
            state_str = self.agent.get_state(bx, by, ball_dx, ball_dy, py1, self.paddle_height, self.width, self.height)
            action = self.agent.choose_action(state_str, explore=True)
            
            # Store state and action for the update phase
            self.last_state = state_str
            self.last_action = action
            
            if action == 1:    # UP
                self.paddle_right.move(-self.paddle_right.speed, self.top_offset + 2, self.height - self.bottom_offset - 2)
            elif action == 2:  # DOWN
                self.paddle_right.move(self.paddle_right.speed, self.top_offset + 2, self.height - self.bottom_offset - 2)
            
            # If paddle was blocked by boundary, the action effectively became STAY.
            # Correct last_action so the Q-table records what actually happened.
            ax1, ay1, ax2, ay2 = self.canvas.coords(self.paddle_right.rect_id)
            if abs(ay1 - py1) < 0.5:  # paddle didn't actually move
                self.last_action = 0  # correct to STAY
        else:
            if self.keys_pressed["up"]:
                self.paddle_right.move(-self.paddle_right.speed, self.top_offset + 2, self.height - self.bottom_offset - 2)
            if self.keys_pressed["down"]:
                self.paddle_right.move(self.paddle_right.speed, self.top_offset + 2, self.height - self.bottom_offset - 2)

    def check_collisions(self):
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball.rect_id)
        bx = (bx1 + bx2) / 2
        by = (by1 + by2) / 2
        r = self.ball.r

        # 1. Wall Collisions (Top border at Y=top_offset, Bottom border at HEIGHT-bottom_offset)
        if by1 <= self.top_offset + 3 and self.ball.dy < 0:
            self.ball.dy = -self.ball.dy
            # Snap ball back inside the top border so high-speed balls don't clip through
            overlap = (self.top_offset + 3) - by1
            self.canvas.move(self.ball.rect_id, 0, overlap)
            self.canvas.move(self.ball.glow_id, 0, overlap)
            self.spawn_particles(bx, self.top_offset + 3, "#ccff00", count=6)
        elif by2 >= self.height - self.bottom_offset - 3 and self.ball.dy > 0:
            self.ball.dy = -self.ball.dy
            # Snap ball back inside the bottom border
            overlap = by2 - (self.height - self.bottom_offset - 3)
            self.canvas.move(self.ball.rect_id, 0, -overlap)
            self.canvas.move(self.ball.glow_id, 0, -overlap)
            self.spawn_particles(bx, self.height - self.bottom_offset - 3, "#ccff00", count=6)

        # 2. Paddle Collisions
        px1_l, py1_l, px2_l, py2_l = self.canvas.coords(self.paddle_left.rect_id)
        px1_r, py1_r, px2_r, py2_r = self.canvas.coords(self.paddle_right.rect_id)

        # Left Paddle Collision
        if self.ball.dx < 0:
            if bx1 <= px2_l and bx2 >= px1_l and by2 >= py1_l and by1 <= py2_l:
                # Snap ball to front of paddle
                new_x1 = px2_l
                new_x2 = px2_l + 2 * r
                new_y1 = by - r
                new_y2 = by + r
                self.canvas.coords(self.ball.rect_id, new_x1, new_y1, new_x2, new_y2)
                self.canvas.coords(self.ball.glow_id, new_x1 - 3, new_y1 - 3, new_x2 + 3, new_y2 + 3)

                # Rebound physics based on intersection position
                py_mid = (py1_l + py2_l) / 2
                hit_pos = (by - py_mid) / (self.paddle_height / 2)
                hit_pos = max(-1.0, min(1.0, hit_pos))

                speed = math.sqrt(self.ball.dx**2 + self.ball.dy**2)
                speed = min(speed * 1.06, self.width / 50.0)  # Scale max speed cap with width

                angle = hit_pos * 0.95  # Max angle ~55 degrees
                self.ball.dx = speed * math.cos(angle)
                self.ball.dy = speed * math.sin(angle)

                self.spawn_particles(px2_l, by, "#00f0ff", count=12)

        # Right Paddle Collision
        if self.ball.dx > 0:
            if bx2 >= px1_r and bx1 <= px2_r and by2 >= py1_r and by1 <= py2_r:
                # Snap ball to front of paddle
                new_x1 = px1_r - 2 * r
                new_x2 = px1_r
                new_y1 = by - r
                new_y2 = by + r
                self.canvas.coords(self.ball.rect_id, new_x1, new_y1, new_x2, new_y2)
                self.canvas.coords(self.ball.glow_id, new_x1 - 3, new_y1 - 3, new_x2 + 3, new_y2 + 3)

                # Rebound physics based on intersection position
                py_mid = (py1_r + py2_r) / 2
                hit_pos = (by - py_mid) / (self.paddle_height / 2)
                hit_pos = max(-1.0, min(1.0, hit_pos))

                speed = math.sqrt(self.ball.dx**2 + self.ball.dy**2)
                speed = min(speed * 1.06, self.width / 50.0)

                angle = hit_pos * 0.95
                self.ball.dx = -speed * math.cos(angle)
                self.ball.dy = speed * math.sin(angle)

                self.spawn_particles(px1_r, by, "#ff007f", count=12)

                # RL Hit Reward (+15)
                if self.game_mode in ["AI", "TRAIN"] and self.last_state is not None and self.last_action is not None:
                    next_state_str = self.agent.get_state(bx, by, self.ball.dx, self.ball.dy, px1_r, self.paddle_height, self.width, self.height)
                    self.agent.update(self.last_state, self.last_action, 15.0, next_state_str)
                    self.last_state = None
                    self.last_action = None

        # 3. Scoring conditions
        if bx2 < 0:
            self.score_player(2)
        elif bx1 > self.width:
            self.score_player(1)

    def score_player(self, player_num):
        self.ball_active = False

        # RL Scoring Reward (Win: +20, Loss: -25)
        if self.game_mode in ["AI", "TRAIN"] and self.last_state is not None and self.last_action is not None:
            bx, by = self.ball.get_coords()
            ball_dx, ball_dy = self.ball.dx, self.ball.dy
            px1, py1, px2, py2 = self.canvas.coords(self.paddle_right.rect_id)
            next_state_str = self.agent.get_state(bx, by, ball_dx, ball_dy, py1, self.paddle_height, self.width, self.height)
            
            reward = -25.0 if player_num == 1 else 20.0
            self.agent.update(self.last_state, self.last_action, reward, next_state_str)
            self.last_state = None
            self.last_action = None

        if player_num == 1:
            self.p1_score += 1
            self.canvas.itemconfig(self.bg_score_p1, text=str(self.p1_score))
            self.score_flash("#00f0ff")  # Flash cyan for Player 1 point
            self.spawn_particles(self.width - 25, self.height // 2, "#00f0ff", count=35)
        else:
            self.p2_score += 1
            self.canvas.itemconfig(self.bg_score_p2, text=str(self.p2_score))
            self.score_flash("#ff007f")  # Flash pink for Player 2 point
            self.spawn_particles(25, self.height // 2, "#ff007f", count=35)

        if self.p1_score >= self.winning_score or self.p2_score >= self.winning_score:
            if self.game_mode == "TRAIN":
                # Continuous loop for training mode:
                # Record game statistics & persist model weights
                self.agent.record_game_end(won=(self.p2_score >= self.winning_score))
                # Reset scores for the next game
                self.p1_score = 0
                self.p2_score = 0
                self.canvas.itemconfig(self.bg_score_p1, text="0")
                self.canvas.itemconfig(self.bg_score_p2, text="0")
                # Serve the ball and continue the tick loop immediately without entering STATE_GAMEOVER
                direction = random.choice([-1, 1])
                self.trigger_serve(direction)
            else:
                self.state = self.STATE_GAMEOVER
                if self.game_mode == "AI":
                    self.agent.record_game_end(won=(self.p2_score >= self.winning_score))
                self.draw_overlay()
        else:
            direction = -1 if player_num == 2 else 1
            self.trigger_serve(direction)

    def score_flash(self, color):
        # Visual flashy feedback
        self.canvas.config(bg=color)
        self.root.after(80, lambda: self.canvas.config(bg="#0d0e15"))

    def spawn_particles(self, x, y, color, count=10):
        for _ in range(count):
            px = x + random.uniform(-8, 8)
            py = y + random.uniform(-8, 8)
            r = random.randint(2, 5)
            pid = self.canvas.create_oval(
                px - r, py - r, px + r, py + r,
                fill=color, outline=""
            )
            p_dx = random.uniform(-5, 5)
            p_dy = random.uniform(-5, 5)
            life = random.randint(15, 30)  # Lifespan in frames
            self.particles.append({
                "id": pid,
                "dx": p_dx,
                "dy": p_dy,
                "life": life
            })

    def update_particles(self):
        alive_particles = []
        for p in self.particles:
            p["life"] -= 1
            if p["life"] > 0:
                self.canvas.move(p["id"], p["dx"], p["dy"])
                alive_particles.append(p)
            else:
                self.canvas.delete(p["id"])
        self.particles = alive_particles

    def update_background_stars(self):
        for s in self.stars:
            # Move stars slowly to the right
            self.canvas.move(s["id"], s["speed"], 0)
            
            # Get coordinates
            x1, y1, x2, y2 = self.canvas.coords(s["id"])
            if x1 > self.width:
                # Wrap back to left side
                self.canvas.coords(s["id"], -s["r"]*2, y1, 0, y2)
            
            # Ensure stars stay stacked in the absolute background
            self.canvas.tag_lower(s["id"])

    def update_intro_paddles(self):
        # Ease paddles in to home coordinates during START menu state
        # Left paddle
        x1_l, y1_l, x2_l, y2_l = self.canvas.coords(self.paddle_left.rect_id)
        diff_l = self.p1_home_x - x1_l
        if abs(diff_l) > 0.5:
            move_x = diff_l * 0.08
            self.canvas.move(self.paddle_left.rect_id, move_x, 0)
            self.canvas.move(self.paddle_left.glow_id, move_x, 0)

        # Right paddle
        x1_r, y1_r, x2_r, y2_r = self.canvas.coords(self.paddle_right.rect_id)
        diff_r = self.p2_home_x - x1_r
        if abs(diff_r) > 0.5:
            move_x = diff_r * 0.08
            self.canvas.move(self.paddle_right.rect_id, move_x, 0)
            self.canvas.move(self.paddle_right.glow_id, move_x, 0)

    def update_ball_trail(self):
        # Add new trail segment
        if self.ball_active and self.state == self.STATE_PLAYING:
            bx1, by1, bx2, by2 = self.canvas.coords(self.ball.rect_id)
            tid = self.canvas.create_oval(
                bx1, by1, bx2, by2,
                fill=self.TRAIL_COLORS[0], outline=""
            )
            # Insert behind main ball elements
            self.canvas.tag_lower(tid, self.ball.rect_id)
            self.trail.append({"id": tid, "age": 0})

        # Update aging segments
        alive_trail = []
        for t in self.trail:
            t["age"] += 1
            if t["age"] < len(self.TRAIL_COLORS):
                # Update color to faded neon shade
                self.canvas.itemconfig(t["id"], fill=self.TRAIL_COLORS[t["age"]])
                alive_trail.append(t)
            else:
                self.canvas.delete(t["id"])
        self.trail = alive_trail

    def game_step(self):
        self.update_paddles()
        if self.ball_active:
            self.ball.move()
            self.check_collisions()
            
            # RL Agent step update (shaping reward)
            if self.game_mode in ["AI", "TRAIN"] and self.last_state is not None and self.last_action is not None:
                bx, by = self.ball.get_coords()
                ball_dx, ball_dy = self.ball.dx, self.ball.dy
                px1, py1, px2, py2 = self.canvas.coords(self.paddle_right.rect_id)
                next_state_str = self.agent.get_state(bx, by, ball_dx, ball_dy, py1, self.paddle_height, self.width, self.height)
                
                # Shaping reward: penalise misalignment ONLY when ball is approaching (dx > 0).
                # When ball moves away, still call update() with reward=0 so Q-values for
                # those states converge via Bellman propagation instead of staying frozen at 0.0.
                if ball_dx > 0:
                    reward = -0.01 * abs(by - (py1 + self.paddle_height / 2.0)) / (self.height / 2.0)
                else:
                    reward = 0.0
                self.agent.update(self.last_state, self.last_action, reward, next_state_str)

    def draw_telemetry(self):
        self.clear_telemetry()
        if self.game_mode not in ["AI", "TRAIN"]:
            return
            
        # Subtle horizontal divider at Y=top_offset
        self.telemetry_border_id = self.canvas.create_line(
            0, self.top_offset, self.width, self.top_offset, fill="#1d2030", width=1.5
        )
        self.telemetry_ids.append(self.telemetry_border_id)
        
        telemetry_y = self.top_offset // 2
        telemetry_font_size = -max(12, int(self.height * 0.022))
        
        mode_str = "PLAYER VS AI (RL)" if self.game_mode == "AI" else f"AI SELF-PLAY ({self.training_speed}x)"
        self.tel_mode_id = self.canvas.create_text(
            self.width * 0.15, telemetry_y, text=f"MODE: {mode_str}",
            font=("Courier", telemetry_font_size, "bold"), fill="#00f0ff"
        )
        self.telemetry_ids.append(self.tel_mode_id)
        
        self.tel_games_id = self.canvas.create_text(
            self.width * 0.42, telemetry_y, text=f"GAMES: {self.agent.games_played}",
            font=("Courier", telemetry_font_size, "bold"), fill="#ffffff"
        )
        self.telemetry_ids.append(self.tel_games_id)
        
        win_rate = self.agent.get_win_rate()
        self.tel_winrate_id = self.canvas.create_text(
            self.width * 0.65, telemetry_y, text=f"AI WIN RATE: {win_rate:.1f}%",
            font=("Courier", telemetry_font_size, "bold"), fill="#ccff00"
        )
        self.telemetry_ids.append(self.tel_winrate_id)
        
        self.tel_epsilon_id = self.canvas.create_text(
            self.width * 0.88, telemetry_y, text=f"EXPLORING (EPS): {self.agent.epsilon*100:.1f}%",
            font=("Courier", telemetry_font_size, "bold"), fill="#ff007f"
        )
        self.telemetry_ids.append(self.tel_epsilon_id)

    def update_telemetry(self):
        if self.game_mode not in ["AI", "TRAIN"]:
            return
        if not self.telemetry_ids:
            self.draw_telemetry()
            return
            
        mode_str = "PLAYER VS AI (RL)" if self.game_mode == "AI" else f"AI SELF-PLAY ({self.training_speed}x)"
        self.canvas.itemconfig(self.tel_mode_id, text=f"MODE: {mode_str}")
        self.canvas.itemconfig(self.tel_games_id, text=f"GAMES: {self.agent.games_played}")
        win_rate = self.agent.get_win_rate()
        self.canvas.itemconfig(self.tel_winrate_id, text=f"AI WIN RATE: {win_rate:.1f}%")
        self.canvas.itemconfig(self.tel_epsilon_id, text=f"EXPLORING (EPS): {self.agent.epsilon*100:.1f}%")

    def clear_telemetry(self):
        for tel_id in self.telemetry_ids:
            self.canvas.delete(tel_id)
        self.telemetry_ids.clear()

    def draw_menu(self):
        # Clear previous menu items from overlay
        if hasattr(self, 'menu_text_ids'):
            for item_id in self.menu_text_ids:
                self.canvas.delete(item_id)
                if item_id in self.overlay_ids:
                    self.overlay_ids.remove(item_id)
        self.menu_text_ids = []

        options = [
            "PLAYER VS PLAYER",
            "PLAYER VS AI (RL)",
            "AI SELF-PLAY TRAINING",
            f"ROUND LIMIT: < {self.winning_score} >"
        ]
        
        y_start = self.height * 0.40
        y_gap = self.height * 0.075
        
        for i, text in enumerate(options):
            is_selected = (self.menu_selection == i)
            # Neon color schemes for selected options
            color = "#00f0ff" if is_selected else "#4a4e69"
            prefix = "::  " if is_selected else "    "
            suffix = "  ::" if is_selected else "    "
            font_weight = "bold" if is_selected else "normal"
            
            # Glow shadow underneath
            if is_selected:
                glow_id = self.canvas.create_text(
                    self.width // 2, y_start + i * y_gap + 2,
                    text=prefix + text + suffix,
                    font=("Helvetica", -int(self.height * 0.036), "bold"),
                    fill="#002b2f"
                )
                self.menu_text_ids.append(glow_id)
                self.overlay_ids.append(glow_id)
                
            txt_id = self.canvas.create_text(
                self.width // 2, y_start + i * y_gap,
                text=prefix + text + suffix,
                font=("Helvetica", -int(self.height * 0.036), font_weight),
                fill=color
            )
            self.menu_text_ids.append(txt_id)
            self.overlay_ids.append(txt_id)

    def return_to_menu(self):
        self.state = self.STATE_START
        self.p1_score = 0
        self.p2_score = 0
        self.canvas.itemconfig(self.bg_score_p1, text="0")
        self.canvas.itemconfig(self.bg_score_p2, text="0")
        
        # Reset paddles and ball
        self.paddle_left.reset_position(self.p1_home_x, self.p_home_y)
        self.paddle_right.reset_position(self.p2_home_x, self.p_home_y)
        self.ball.reset(self.width // 2, self.height // 2)
        self.ball_active = False
        
        self.clear_telemetry()
        self.draw_overlay()

    def on_exit(self):
        if self.game_mode in ["AI", "TRAIN"]:
            self.agent.save_model()
        self.root.destroy()

    def draw_overlay(self):
        self.clear_overlay()
        
        if self.state == self.STATE_START:
            # Game Title
            t1 = self.canvas.create_text(
                self.width // 2, self.height * 0.22, text="NEON PING PONG",
                font=("Helvetica", -int(self.height * 0.09), "bold"), fill="#002f33"
            )
            t2 = self.canvas.create_text(
                self.width // 2, self.height * 0.215, text="NEON PING PONG",
                font=("Helvetica", -int(self.height * 0.09), "bold"), fill="#00f0ff"
            )
            self.overlay_ids.extend([t1, t2])

            # Interactive Menu
            self.draw_menu()

            # Instructions footer
            inst = self.canvas.create_text(
                self.width // 2, self.height * 0.81, 
                text="START: SPACE  |  NAVIGATE: W/S  |  CHANGE ROUNDS: A/D OR LEFT/RIGHT",
                font=("Courier", -int(self.height * 0.021), "bold"), fill="#ffffff"
            )
            exit_inst = self.canvas.create_text(
                self.width // 2, self.height * 0.88, 
                text="PRESS ESC OR 'Q' TO EXIT",
                font=("Courier", -int(self.height * 0.019), "bold"), fill="#888888"
            )
            self.overlay_ids.extend([inst, exit_inst])

        elif self.state == self.STATE_PAUSED:
            t_paused = self.canvas.create_text(
                self.width // 2, self.height * 0.35, text="GAME PAUSED",
                font=("Helvetica", -int(self.height * 0.08), "bold"), fill="#ffffff"
            )
            self.blink_text_id = self.canvas.create_text(
                self.width // 2, self.height * 0.49, text="PRESS SPACEBAR TO RESUME",
                font=("Helvetica", -int(self.height * 0.035), "bold"), fill="#ff007f"
            )
            t_restart = self.canvas.create_text(
                self.width // 2, self.height * 0.62, text="PRESS 'R' TO RESTART   |   'M' FOR MAIN MENU   |   ESC TO EXIT",
                font=("Courier", -int(self.height * 0.022), "bold"), fill="#888888"
            )
            self.overlay_ids.extend([t_paused, self.blink_text_id, t_restart])

        elif self.state == self.STATE_GAMEOVER:
            winner_text = "PLAYER 1 WINS!" if self.p1_score >= self.winning_score else "PLAYER 2 WINS!"
            winner_color = "#00f0ff" if self.p1_score >= self.winning_score else "#ff007f"
            
            # Adjust text for AI modes
            if self.game_mode in ["AI", "TRAIN"]:
                if self.p2_score >= self.winning_score:
                    winner_text = "AI OPPONENT WINS!"
                    winner_color = "#ff007f"
                else:
                    winner_text = "YOU WIN!"
                    winner_color = "#00f0ff"
            
            t_winner = self.canvas.create_text(
                self.width // 2, self.height * 0.38, text=winner_text,
                font=("Helvetica", -int(self.height * 0.09), "bold"), fill=winner_color
            )
            t_prompt = self.canvas.create_text(
                self.width // 2, self.height * 0.55, text="PRESS 'R' TO PLAY AGAIN   |   'M' FOR MAIN MENU   |   ESC TO EXIT",
                font=("Helvetica", -int(self.height * 0.032), "bold"), fill="#ffffff"
            )
            self.overlay_ids.extend([t_winner, t_prompt])

    def clear_overlay(self):
        for item_id in self.overlay_ids:
            self.canvas.delete(item_id)
        self.overlay_ids.clear()
        self.blink_text_id = None

    def toggle_blink(self):
        if self.state in [self.STATE_START, self.STATE_PAUSED]:
            if self.blink_text_id is not None:
                self.blink_state = not self.blink_state
                new_state = "normal" if self.blink_state else "hidden"
                try:
                    self.canvas.itemconfig(self.blink_text_id, state=new_state)
                except Exception:
                    pass
        self.root.after(500, self.toggle_blink)

    def tick(self):
        # Starfield movement (independent of game state)
        self.update_background_stars()

        if self.state == self.STATE_START:
            # Animate entry of paddles
            self.update_intro_paddles()

        elif self.state == self.STATE_PLAYING:
            if self.game_mode == "TRAIN" and self.ball_active:
                for _ in range(self.training_speed):
                    if self.ball_active and self.state == self.STATE_PLAYING:
                        self.game_step()
                        self.update_ball_trail()
                        self.update_particles()
            else:
                self.game_step()
                self.update_ball_trail()
                self.update_particles()
                
            self.update_telemetry()
            
        elif self.state in [self.STATE_PAUSED, self.STATE_GAMEOVER]:
            # Keep fading trails and particles alive
            self.update_ball_trail()
            self.update_particles()
        
        self.root.after(1000 // FPS, self.tick)


def main():
    root = tk.Tk()
    game = PingPongGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
