import sys
import os
import random
import json
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget, 
                              QVBoxLayout, QProgressBar, QGridLayout)
from PySide6.QtCore import Qt, QTimer, QRect, QPoint, QPropertyAnimation, QEasingCurve, QSize, Signal, Slot
from PySide6.QtGui import QMovie, QCursor, QPixmap, QTransform, QFont, QColor

# Import actual sensor modules
import temperature
import carbondioxide
import door

# State file for saving pet stats
STATE_FILE = 'pet_state.json'

def clamp(value, min_val=0, max_val=100):
    return max(min_val, min(value, max_val))

class StatWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Configure window
        self.setWindowTitle("Pet Stats")
        self.setFixedSize(300, 280)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create header label
        header_label = QLabel("🐾 Virtual Pet Stats")
        header_label.setAlignment(Qt.AlignCenter)
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        main_layout.addWidget(header_label)
        
        # Create grid for stats
        stats_grid = QGridLayout()
        main_layout.addLayout(stats_grid)
        
        # Create status labels
        self.temp_label = QLabel("🌡️ Temp: -- °C")
        self.co2_label = QLabel("🫁 CO₂: -- ppm")
        self.door_label = QLabel("🚪 Door: --")
        self.mood_label = QLabel("😺 Mood: --")
        
        # Add to grid
        stats_grid.addWidget(QLabel("Environment:"), 0, 0)
        stats_grid.addWidget(self.temp_label, 1, 0)
        stats_grid.addWidget(self.co2_label, 2, 0)
        stats_grid.addWidget(self.door_label, 3, 0)
        stats_grid.addWidget(self.mood_label, 4, 0)
        
        # Create hunger progress bar
        hunger_label = QLabel("🍗 Hunger:")
        self.hunger_bar = QProgressBar()
        self.hunger_bar.setRange(0, 100)
        self.hunger_bar.setValue(100)
        
        # Create sleep progress bar
        sleep_label = QLabel("😴 Sleep:")
        self.sleep_bar = QProgressBar()
        self.sleep_bar.setRange(0, 100)
        self.sleep_bar.setValue(100)
        
        # Create water progress bar
        water_label = QLabel("💧 Water:")
        self.water_bar = QProgressBar()
        self.water_bar.setRange(0, 100)
        self.water_bar.setValue(100)
        
        # Add progress bars to grid
        stats_grid.addWidget(QLabel("Pet Needs:"), 0, 1)
        stats_grid.addWidget(hunger_label, 1, 1)
        stats_grid.addWidget(self.hunger_bar, 1, 2)
        stats_grid.addWidget(sleep_label, 2, 1)
        stats_grid.addWidget(self.sleep_bar, 2, 2)
        stats_grid.addWidget(water_label, 3, 1)
        stats_grid.addWidget(self.water_bar, 3, 2)
        
        # Set up styling for the bars
        self.set_progress_bar_style(self.hunger_bar)
        self.set_progress_bar_style(self.sleep_bar)
        self.set_progress_bar_style(self.water_bar)
        
        self.show()
    
    def set_progress_bar_style(self, bar):
        bar.setTextVisible(True)
        bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 20px;
            }
        """)
    
    def update_stats(self, temp, co2, door_state, hunger, sleep, water, mood):
        # Update labels
        self.temp_label.setText(f"🌡️ Temp: {temp} °C")
        self.co2_label.setText(f"🫁 CO₂: {co2} ppm")
        self.door_label.setText(f"🚪 Door: {door_state}")
        self.mood_label.setText(f"😺 Mood: {mood}")
        
        # Update progress bars
        self.hunger_bar.setValue(hunger)
        self.sleep_bar.setValue(sleep)
        self.water_bar.setValue(water)
        
        # Update color based on value
        for bar, value in [(self.hunger_bar, hunger), (self.sleep_bar, sleep), (self.water_bar, water)]:
            if value < 20:
                bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid grey;
                        border-radius: 5px;
                        text-align: center;
                    }
                    QProgressBar::chunk {
                        background-color: #F44336;
                        width: 20px;
                    }
                """)
            elif value < 50:
                bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid grey;
                        border-radius: 5px;
                        text-align: center;
                    }
                    QProgressBar::chunk {
                        background-color: #FFC107;
                        width: 20px;
                    }
                """)
            else:
                bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid grey;
                        border-radius: 5px;
                        text-align: center;
                    }
                    QProgressBar::chunk {
                        background-color: #4CAF50;
                        width: 20px;
                    }
                """)

class ItemWindow(QMainWindow):
    def __init__(self, item_path, parent=None):
        super().__init__(parent)
        self.item_path = item_path
        self.scale_factor = 3  # Slightly smaller than pet
        
        # Configure window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        
        # Create item label
        self.item_label = QLabel(self)
        self.setCentralWidget(self.item_label)
        
        # Load and scale the item image
        self.load_item()
        
        # Position randomly on screen
        self.random_position()
        
        # Set timer for despawning
        self.despawn_timer = QTimer(self)
        self.despawn_timer.timeout.connect(self.close)
        self.despawn_timer.start(30000)  # Despawn after 30 seconds
        
        self.show()
    
    def load_item(self):
        pixmap = QPixmap(str(self.item_path))
        
        # Get screen dimensions
        desktop = QApplication.primaryScreen().availableGeometry()
        max_width = desktop.width() // 2  # Maximum half the screen width
        max_height = desktop.height() // 2  # Maximum half the screen height
        
        # Calculate desired size with scale factor
        desired_width = pixmap.width() * self.scale_factor
        desired_height = pixmap.height() * self.scale_factor
        
        # If too large, adjust scale factor
        if desired_width > max_width or desired_height > max_height:
            width_scale = max_width / pixmap.width() if desired_width > max_width else self.scale_factor
            height_scale = max_height / pixmap.height() if desired_height > max_height else self.scale_factor
            self.scale_factor = min(width_scale, height_scale)
        
        scaled_pixmap = pixmap.scaled(
            int(pixmap.width() * self.scale_factor),
            int(pixmap.height() * self.scale_factor),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.item_label.setPixmap(scaled_pixmap)
        self.resize(scaled_pixmap.width(), scaled_pixmap.height())
    
    def random_position(self):
        desktop = QApplication.primaryScreen().availableGeometry()
        
        # Make sure we have valid ranges for random positioning
        max_x = max(0, desktop.width() - self.width())
        max_y = max(0, desktop.height() - self.height())
        
        x = random.randint(0, max_x) if max_x > 0 else 0
        y = random.randint(0, max_y) if max_y > 0 else 0
        
        self.move(x, y)


class DesktopPet(QMainWindow):
    # Custom signal for state changes
    stat_changed = Signal(int, int, str, int, int, int, str)
    
    def __init__(self):
        super().__init__()
    
        # Scale factor
        self.scale_factor = 4
        self.base_size = QSize(100, 100)  # or get this from a sample frame
        self.scaled_size = self.base_size * self.scale_factor
        self.resize(self.scaled_size)
        
        # Stats
        self.hunger, self.sleep, self.water = self.load_state()
        self.temp = 25  # Default temperature
        self.co2 = 500  # Default CO2
        self.door_state = "Closed"  # Default door state
        
        # States
        self.IDLE = 0
        self.WALKING = 1
        self.FALLING = 2
        self.FLOATING = 3
        self.JUMPING = 4
        self.LANDING = 5
        self.GRABBED = 6
        self.HIT = 7
        self.EATING = 8
        self.DRINKING = 9
        self.SLEEPING = 10
        
        # Configure window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        
        # Create pet label
        self.pet_label = QLabel(self)
        self.setCentralWidget(self.pet_label)
        
        # Animation variables
        self.anim_path = Path("gifs")
        self.animations = {
            self.IDLE: self.anim_path / "idle.gif",
            self.WALKING: self.anim_path / "walk.gif",
            self.FALLING: self.anim_path / "fall.gif",
            self.FLOATING: self.anim_path / "floating_flap.gif",
            self.JUMPING: self.anim_path / "jump.gif",
            self.LANDING: self.anim_path / "land.gif",
            self.HIT: self.anim_path / "hit.gif",
            self.EATING: self.anim_path / "eat.gif",
            self.DRINKING: self.anim_path / "drink.gif",
            self.SLEEPING: self.anim_path / "sleep.gif"
        }
        
        # Props paths
        self.props_path = self.anim_path / "props"
        self.food_path = self.anim_path / "food"
        self.drink_path = self.anim_path / "drink"
        
        # Active item window
        self.current_item_window = None
        
        # Load default animation
        self.movie = QMovie(str(self.animations[self.IDLE]))
        self.pet_label.setMovie(self.movie)
        self.movie.start()
        
        # Set initial size with scale factor
        base_size = 100
        self.resize(base_size * self.scale_factor, base_size * self.scale_factor)
        
        # Movement variables
        self.current_state = self.IDLE
        self.direction = 1  # 1 for right, -1 for left
        self.speed = 2 * self.scale_factor  # Scale speed as well
        self.is_grabbed = False
        self.grab_offset = QPoint(0, 0)
        
        # Create stats window
        self.stats_window = StatWindow()
        
        # Set up timers
        self.movement_timer = QTimer(self)
        self.movement_timer.timeout.connect(self.update_position)
        self.movement_timer.start(50)  # Update every 50ms
        
        self.state_timer = QTimer(self)
        self.state_timer.timeout.connect(self.change_state)
        self.state_timer.start(random.randint(5000, 10000))  # Random state changes
        
        # Set up item spawn timer
        self.item_timer = QTimer(self)
        self.item_timer.timeout.connect(self.spawn_random_item)
        self.item_timer.start(random.randint(30000, 60000))  # Every 30-60 seconds
        
        # Set up stats timer
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(5000)  # Update every 5 seconds
        
        # Connect signals
        self.stat_changed.connect(self.stats_window.update_stats)
        
        # Position on taskbar
        self.move_to_taskbar()
        self.show()
        
        # Initial stats update
        self.update_stats()

    def closeEvent(self, event):
        self.save_state()
        event.accept()  # Allow closing
    
    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE) as f:
                    data = json.load(f)
                    return data.get('hunger', 100), data.get('sleep', 100), data.get('water', 100)
            except (json.JSONDecodeError, IOError):
                return 100, 100, 100
        return 100, 100, 100
    
    def save_state(self):
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump({
                    'hunger': self.hunger, 
                    'sleep': self.sleep, 
                    'water': self.water
                }, f)
        except IOError:
            print("Failed to save pet state")
    
    def move_to_taskbar(self):
        desktop = QApplication.primaryScreen().availableGeometry()
        self.move(random.randint(0, desktop.width() - self.width()), 
                  desktop.height() - self.height())
    
    def set_animation(self, state):
        if state in self.animations and os.path.exists(self.animations[state]):
            self.current_state = state
            self.movie.stop()
            self.movie = QMovie(str(self.animations[state]))
            
            # Scale up the movie frames
            self.movie.setCacheMode(QMovie.CacheAll)
            self.movie.frameChanged.connect(self.scale_frame)
            
            self.pet_label.setMovie(self.movie)
            self.movie.start()
    
    def scale_frame(self):
        current_pixmap = self.movie.currentPixmap()
        
        if self.direction < 0:
            # Flip the pixmap horizontally
            transform = QTransform().scale(-1, 1)
            current_pixmap = current_pixmap.transformed(transform, Qt.SmoothTransformation)
        
        scaled_pixmap = current_pixmap.scaled(
            current_pixmap.width() * self.scale_factor,
            current_pixmap.height() * self.scale_factor,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.pet_label.setPixmap(scaled_pixmap)
        self.resize(scaled_pixmap.width(), scaled_pixmap.height())
    
    def update_position(self):
        if self.is_grabbed:
            # Check for collision with item window while grabbed
            if self.current_item_window and self.check_collision_with_item():
                self.interact_with_item()
            return
            
        if self.current_state == self.WALKING:
            pos = self.pos()
            new_x = pos.x() + (self.speed * self.direction)
        
            # Check screen boundaries
            desktop = QApplication.primaryScreen().availableGeometry()
            if new_x < 0:
                self.direction = 1  # Change direction to right
                new_x = 0
            elif new_x > desktop.width() - self.width():
                self.direction = -1  # Change direction to left
                new_x = desktop.width() - self.width()
                
            self.move(new_x, pos.y())
        
        elif self.current_state == self.FALLING:
            pos = self.pos()
            new_y = pos.y() + (10 * self.scale_factor)  # Fall speed, scaled
            
            # Check if reached bottom
            desktop = QApplication.primaryScreen().availableGeometry()
            if new_y >= desktop.height() - self.height():
                new_y = desktop.height() - self.height()
                self.set_animation(self.LANDING)
                QTimer.singleShot(500, lambda: self.set_animation(self.IDLE))
            
            self.move(pos.x(), new_y)
    
    def change_state(self):
        if self.is_grabbed:
            return
            
        # Don't interrupt falling or landing
        if self.current_state in [self.FALLING, self.LANDING, self.JUMPING, self.EATING, self.DRINKING, self.SLEEPING]:
            return
        
        # If stats are critically low, prioritize that behavior
        if self.hunger <= 20 or self.water <= 20 or self.sleep <= 20:
            # Pet is hungry
            if self.hunger <= min(self.water, self.sleep):
                self.spawn_food_item()
                return
            # Pet is thirsty
            elif self.water <= min(self.hunger, self.sleep):
                self.spawn_drink_item()
                return
            # Pet is sleepy
            elif self.sleep <= min(self.hunger, self.water):
                self.spawn_bed_item()
                return
        
        choices = [self.IDLE, self.WALKING]
        weights = [0.3, 0.7]  # More likely to walk than idle
        
        new_state = random.choices(choices, weights)[0]
        
        # Occasionally make the pet jump
        if random.random() < 0.1:
            self.jump()
        else:
            self.set_animation(new_state)
        
        # Set a new timer interval
        self.state_timer.setInterval(random.randint(3000, 8000))
    
    def jump(self):
        self.set_animation(self.JUMPING)
        
        # Create jump animation
        pos = self.pos()
        jump_height = random.randint(50, 150) * self.scale_factor
        
        self.jump_animation = QPropertyAnimation(self, b"pos")
        self.jump_animation.setDuration(500)
        self.jump_animation.setStartValue(pos)
        self.jump_animation.setEndValue(QPoint(pos.x(), pos.y() - jump_height))
        self.jump_animation.setEasingCurve(QEasingCurve.OutQuad)
        
        # After jumping, start falling
        self.jump_animation.finished.connect(lambda: self.set_animation(self.FALLING))
        self.jump_animation.start()
    
    def throw(self, direction):
        pos = self.pos()
        throw_distance = random.randint(100, 300) * self.scale_factor
        throw_height = random.randint(50, 200) * self.scale_factor
        
        # Create throw animation
        self.throw_animation = QPropertyAnimation(self, b"pos")
        self.throw_animation.setDuration(700)
        self.throw_animation.setStartValue(pos)
        
        # Calculate throw endpoint
        throw_x = pos.x() + (throw_distance * direction)
        # Check screen boundaries
        desktop = QApplication.primaryScreen().availableGeometry()
        throw_x = max(0, min(desktop.width() - self.width(), throw_x))
        
        self.throw_animation.setEndValue(QPoint(throw_x, pos.y() - throw_height))
        self.throw_animation.setEasingCurve(QEasingCurve.OutQuad)
        
        # After throwing, start falling
        self.throw_animation.finished.connect(lambda: self.set_animation(self.FALLING))
        self.throw_animation.start()
    
    def spawn_random_item(self):
        # Close existing item window if any
        if self.current_item_window:
            self.current_item_window.close()
            self.current_item_window = None

        # Choose which type of item to spawn based on needs
        if self.hunger <= min(self.water, self.sleep):
            self.spawn_food_item()
        elif self.water <= min(self.hunger, self.sleep):
            self.spawn_drink_item()
        elif self.sleep <= min(self.hunger, self.water):
            self.spawn_bed_item()
        else:
            # Random item if no urgent needs
            item_type = random.choice(["bed", "food", "drink"])
            
            if item_type == "bed":
                self.spawn_bed_item()
            elif item_type == "food":
                self.spawn_food_item()
            else:  # drink
                self.spawn_drink_item()
        
        # Reset timer for next spawn
        self.item_timer.start(random.randint(30000, 60000))  # 30-60 seconds
    
    def spawn_bed_item(self):
        # Just use bed.png from props
        item_path = self.props_path / "bed.png"
        if os.path.exists(item_path):
            self.current_item_window = ItemWindow(item_path)
    
    def spawn_food_item(self):
        # Get random food item
        food_files = list(self.food_path.glob("*.png"))
        if food_files:
            item_path = random.choice(food_files)
            self.current_item_window = ItemWindow(item_path)
    
    def spawn_drink_item(self):
        # Get random drink item
        drink_files = list(self.drink_path.glob("*.png"))
        if drink_files:
            item_path = random.choice(drink_files)
            self.current_item_window = ItemWindow(item_path)
    
    def check_collision_with_item(self):
        if not self.current_item_window:
            return False
            
        # Get rectangles for pet and item
        pet_rect = self.geometry()
        item_rect = self.current_item_window.geometry()
        
        # Check for intersection
        return pet_rect.intersects(item_rect)
    
    def interact_with_item(self):
        if not self.current_item_window:
            return
            
        # Get the item type from the path
        item_path = self.current_item_window.item_path
        item_type = "unknown"
        
        if "props" in str(item_path):
            item_type = "bed"
        elif "food" in str(item_path):
            item_type = "food"
        elif "drink" in str(item_path):
            item_type = "drink"
            
        # Perform different interactions based on item type
        if item_type == "bed":
            self.set_animation(self.SLEEPING)
            # Increase sleep
            self.sleep = clamp(self.sleep + 30)
            QTimer.singleShot(3000, lambda: self.set_animation(self.IDLE))
        elif item_type == "food":
            self.set_animation(self.EATING)
            # Increase hunger
            self.hunger = clamp(self.hunger + 20)
            QTimer.singleShot(2000, lambda: self.set_animation(self.IDLE))
        elif item_type == "drink":
            self.set_animation(self.DRINKING)
            # Increase water
            self.water = clamp(self.water + 20)
            QTimer.singleShot(2000, lambda: self.set_animation(self.IDLE))
        
        # Update stats display
        self.update_stats()
        self.save_state()
            
        # Close the item window
        self.current_item_window.close()
        self.current_item_window = None
    
    def update_stats(self):
        # Use actual sensor data instead of simulated values
        try:
            # Get temperature from sensor
            temp_data = temperature.get_temperature()
            if isinstance(temp_data, (int, float)):
                self.temp = temp_data
            else:
                # If there's an error or invalid data, use default
                print(f"Temperature sensor issue: {temp_data}")
                self.temp = 25  # Use default value
                
            # Get CO2 from sensor
            co2_data = carbondioxide.get_co2()
            if isinstance(co2_data, (int, float)):
                self.co2 = co2_data
            else:
                # If there's an error or invalid data, use default
                print(f"CO2 sensor issue: {co2_data}")
                self.co2 = 500  # Use default value
                
            # Get door state from sensor
            door_data = door.get_door_status()
            if isinstance(door_data, str):
                self.door_state = door_data
            else:
                # If there's an error or invalid data, use default
                print(f"Door sensor issue: {door_data}")
                self.door_state = "Closed"  # Use default value
                
        except Exception as e:
            # If any sensor read fails, log error and use default values
            print(f"Error reading sensors: {e}")
            self.temp = 25
            self.co2 = 500
            self.door_state = "Closed"
        
        # Decrease stats based on environment
        self.hunger -= 0.5
        self.sleep -= 0.4
        self.water -= 0.3
        
        # Adjust stats based on sensor readings
        if self.co2 > 1000:
            self.sleep -= 1  # High CO2 makes pet sleepy faster
        if self.temp > 28 or self.temp < 18:
            self.hunger -= 0.5  # Temperature extremes increase hunger
            self.water -= 0.5  # Temperature extremes increase thirst
        if self.door_state.lower() == "open":
            self.hunger -= 1  # Open door increases hunger
            self.water -= 1  # Open door increases thirst
        
        # Clamp values
        self.hunger = clamp(self.hunger)
        self.sleep = clamp(self.sleep)
        self.water = clamp(self.water)
        
        # Check if pet is dying
        if self.hunger <= 0 or self.sleep <= 0 or self.water <= 0:
            self.set_animation(self.HIT)  # Use hit animation for dying
            
        # Get mood based on environment
        mood = self.get_mood()
        
        # Update stats window
        self.stat_changed.emit(
            int(self.temp), 
            int(self.co2), 
            self.door_state, 
            int(self.hunger), 
            int(self.sleep), 
            int(self.water),
            mood
        )
        
        # Save state
        self.save_state()
    
    def get_mood(self):
        if self.co2 > 1000:
            return "😵 Dizzy from poor air!"
        elif self.temp > 28:
            return "🥵 It's too hot!"
        elif self.temp < 18:
            return "🥶 Brrr! Too cold!"
        elif self.door_state.lower() == "open":
            return "🐾 The door is open!"
        elif self.hunger < 20 or self.water < 20 or self.sleep < 20:
            return "😢 I need attention!"
        else:
            return "😌 Cozy and content."

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_grabbed = True
            self.grab_offset = event.pos()
            # Play hit animation instead of floating
            self.set_animation(self.HIT)
            
    def mouseMoveEvent(self, event):
        if self.is_grabbed:
            # Move pet with cursor, accounting for grab offset
            self.move(QCursor.pos() - self.grab_offset)
            
    def mouseReleaseEvent(self, event):
        if self.is_grabbed:
            self.is_grabbed = False
            
            # Determine throw direction based on mouse movement
            cursor_pos = QCursor.pos()
            window_center = self.geometry().center()
            
            direction = 1 if cursor_pos.x() > window_center.x() else -1
            
            # Throw the pet
            self.throw(direction)


# This section is modified to remove the mock modules since we're now using the real ones
if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = DesktopPet()
    sys.exit(app.exec())