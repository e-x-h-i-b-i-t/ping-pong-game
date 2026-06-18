import json
import os
import random

class RLAgent:
    def __init__(self, filename="ai_model.json", alpha=0.1, gamma=0.98, epsilon=0.2, epsilon_decay=0.9995, epsilon_min=0.05):
        self.filename = filename
        self.alpha = alpha          # Learning rate
        self.gamma = gamma          # Discount factor
        self.epsilon = epsilon      # Exploration rate
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        # Q-table: key (state string) -> list of 3 floats [Q(STAY), Q(UP), Q(DOWN)]
        self.q_table = {}
        
        # Statistics & Analytics
        self.games_played = 0
        self.ai_wins = 0
        self.ai_losses = 0
        self.total_rewards_history = []
        self.current_game_reward = 0.0

        # Load existing model if available
        self.load_model()

    def get_state(self, ball_x, ball_y, ball_dx, ball_dy, paddle_y, paddle_height, screen_width, screen_height):
        # Calculate paddle center Y
        paddle_center_y = paddle_y + paddle_height / 2.0
        
        # Discretize relative Y distance (ball Y - paddle center Y)
        # Using a bin size of paddle_height / 3.0 to keep bins reasonably sized
        relative_y = ball_y - paddle_center_y
        bin_y = int(relative_y / max(10, paddle_height / 3.0))
        bin_y = max(-6, min(6, bin_y))  # Clamp to range [-6, 6]
        
        # Discretize ball X position (split screen into 8 vertical columns)
        bin_x = int(ball_x / max(10, screen_width / 8.0))
        bin_x = max(0, min(7, bin_x))
        
        # Sign of ball velocities
        dx_sign = 1 if ball_dx > 0 else -1
        dy_sign = 1 if ball_dy > 0 else (-1 if ball_dy < 0 else 0)
        
        # State key representation
        return f"{bin_y},{bin_x},{dx_sign},{dy_sign}"

    def get_q_values(self, state_str):
        if state_str not in self.q_table:
            self.q_table[state_str] = [0.0, 0.0, 0.0]  # STAY, UP, DOWN
        return self.q_table[state_str]

    def choose_action(self, state_str, explore=True):
        q_values = self.get_q_values(state_str)
        
        # Epsilon-greedy exploration
        if explore and random.random() < self.epsilon:
            return random.choice([0, 1, 2])
            
        # Exploit: find max Q-value
        max_q = max(q_values)
        # Handle ties randomly to ensure unbiased movement
        actions_with_max_q = [i for i, q in enumerate(q_values) if q == max_q]
        return random.choice(actions_with_max_q)

    def update(self, state_str, action, reward, next_state_str):
        q_values = self.get_q_values(state_str)
        next_q_values = self.get_q_values(next_state_str)
        
        # Bellman equation update
        best_next_q = max(next_q_values)
        target = reward + self.gamma * best_next_q
        q_values[action] += self.alpha * (target - q_values[action])
        
        self.current_game_reward += reward

    def decay_epsilon(self):
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            self.epsilon = max(self.epsilon_min, self.epsilon)

    def record_game_end(self, won):
        self.games_played += 1
        if won:
            self.ai_wins += 1
        else:
            self.ai_losses += 1
        self.total_rewards_history.append(self.current_game_reward)
        # Cap reward history length to prevent memory leaks
        if len(self.total_rewards_history) > 100:
            self.total_rewards_history.pop(0)
        
        self.current_game_reward = 0.0
        self.decay_epsilon()
        self.save_model()

    def get_win_rate(self):
        if self.games_played == 0:
            return 0.0
        return (self.ai_wins / self.games_played) * 100.0

    def save_model(self):
        data = {
            "q_table": self.q_table,
            "games_played": self.games_played,
            "ai_wins": self.ai_wins,
            "ai_losses": self.ai_losses,
            "epsilon": self.epsilon,
            "total_rewards_history": self.total_rewards_history
        }
        try:
            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving AI model: {e}")

    def load_model(self):
        if not os.path.exists(self.filename):
            return
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                self.q_table = data.get("q_table", {})
                self.games_played = data.get("games_played", 0)
                self.ai_wins = data.get("ai_wins", 0)
                self.ai_losses = data.get("ai_losses", 0)
                self.epsilon = data.get("epsilon", self.epsilon)
                self.total_rewards_history = data.get("total_rewards_history", [])
        except Exception as e:
            print(f"Error loading AI model: {e}")
