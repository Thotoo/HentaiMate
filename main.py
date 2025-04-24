from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QMovie

class GIFWindow(QWidget):
    
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF Player")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)  # Qt.FramelessWindowHint 
        self.setAttribute(Qt.WA_TranslucentBackground)

        # GIF label
        self.gif_label = QLabel(self)

        # Load and play the GIF
        self.movie = QMovie("Gifs/idle.gif")

        self.movie.setScaledSize(QSize(1000, 1000)) # replace with the path to your gif
        self.gif_label.setMovie(self.movie)
        self.movie.start()

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(self.gif_label)
        self.setLayout(layout)

    # Handle key press events
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Up:
            self.move(self.geometry().y(), self.geometry().y() - 10)
            self.movie = QMovie("Gifs/climb_back.gif")  # replace with the path to your gif
            self.gif_label.setMovie(self.movie)
            self.movie.start()
            print("Up arrow key pressed")
            # Do something when the Up arrow key is pressed
        elif key == Qt.Key_Down:
            print("Down arrow key pressed")
            # Do something when the Down arrow key is pressed
        elif key == Qt.Key_Escape:
            print("Escape key pressed")
            self.close()  # Close the window when Escape is pressed
        else:
            print(f"Key {key} pressed")  # For other keys

if __name__ == "__main__":
    app = QApplication([])
    window = GIFWindow()
    window.show()
    app.exec()
