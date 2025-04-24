import sys
import os
import random
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtCore import Qt, QTimer, QRect, QPoint, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import  QMovie, QCursor, QPixmap, QTransform
class DesktopPet(QMainWindow):
    def __init__(self):
        super().__init__()
    
        
        # Scale factor
        self.scale_factor = 4
        self.base_size = QSize(100, 100)  # or get this from a sample frame
        self.scaled_size = self.base_size * self.scale_factor
        self.resize(self.scaled_size)
        
        # States
        self.IDLE = 0
        self.WALKING = 1
        self.FALLING = 2
        self.FLOATING = 3
        self.JUMPING = 4
        self.LANDING = 5
        self.GRABBED = 6
        self.HIT = 7
        
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
            self.HIT: self.anim_path / "hit.gif"
        }
        
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
        
        # Set up timers
        self.movement_timer = QTimer(self)
        self.movement_timer.timeout.connect(self.update_position)
        self.movement_timer.start(50)  # Update every 50ms
        
        self.state_timer = QTimer(self)
        self.state_timer.timeout.connect(self.change_state)
        self.state_timer.start(random.randint(5000, 10000))  # Random state changes
        
        # Position on taskbar
        self.move_to_taskbar()
        self.show()

    def closeEvent(self, event):
        event.ignore()
    
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
            
            # Flip animation horizontally based on direction
                
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
        if self.current_state in [self.FALLING, self.LANDING, self.JUMPING]:
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = DesktopPet()
    sys.exit(app.exec())