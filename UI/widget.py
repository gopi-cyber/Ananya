import sys
import math
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QFrame, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QPainterPath, QLinearGradient, QBrush

class ChatWidget(QWidget):
    command_entered = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 380)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide() # Hidden by default
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 35, 15, 15) # Leave space for the top tab
        self.main_layout.setSpacing(10)
        
        # 1. Header Area (Implicitly handled by paintEvent for the tab)
        
        # 2. Log Area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFrameStyle(QFrame.Shape.NoFrame)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: white;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        self.main_layout.addWidget(self.log_area)
        
        # 3. Separator Line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: rgba(0, 102, 255, 100); height: 1px;")
        self.main_layout.addWidget(line)
        
        # 4. Input Area
        input_container = QHBoxLayout()
        self.prompt_label = QLabel("> ")
        self.prompt_label.setStyleSheet("color: white; font-weight: bold; font-family: monospace;")
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("enter message...")
        self.input_field.setFrame(False)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                color: white;
                font-family: 'Consolas', monospace;
                font-size: 14px;
            }
        """)
        input_container.addWidget(self.prompt_label)
        input_container.addWidget(self.input_field)
        self.main_layout.addLayout(input_container)
        
        # Connect Input
        self.input_field.returnPressed.connect(self.handle_input)
        
        # 5. Bottom Actions
        action_layout = QHBoxLayout()
        self.img_btn = QLabel("[+ img]")
        self.img_btn.setStyleSheet("color: #aaaaaa; font-family: monospace; font-size: 11px;")
        
        self.send_btn = QLabel("[send \u21B5]")
        self.send_btn.setStyleSheet("color: #aaaaaa; font-family: monospace; font-size: 11px;")
        
        action_layout.addWidget(self.img_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.send_btn)
        self.main_layout.addLayout(action_layout)
        
        # Initial Content
        self.add_log("$ Close the Spotify widget and show the chat widget.", "command")
        self.add_log("> Closing the music widget.", "system")
        self.add_log("Opening the chat.", "plain")
        self.add_log("$ Can you still hear me mate?", "command")
        self.add_log("> I can still hear you loud and clear, Sir. Standing by.", "system")
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def handle_input(self):
        text = self.input_field.text().strip()
        if text:
            self.add_log(f"$ {text}", "command")
            self.command_entered.emit(text)
            self.input_field.clear()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.input_field.setFocus()

    def add_log(self, text, style="plain"):
        if style == "command":
            formatted = f'<span style="color: white; font-weight: bold;">{text}</span>'
        elif style == "system":
            formatted = f'<span style="color: #ffffff; font-weight: bold;">{text}</span>'
        else:
            formatted = f'<span style="color: #dddddd;">{text}</span>'
        
        self.log_area.append(formatted + "<br>")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # --- Draw Main Panel Body ---
        path = QPainterPath()
        cut = 25 # Bottom-right cut size
        path.moveTo(0, 15) # Top-left (after the tab start)
        path.lineTo(w, 15) # Top-right
        path.lineTo(w, h - cut) # Side before bottom-right cut
        path.lineTo(w - cut, h) # Bottom-right cut
        path.lineTo(0, h) # Bottom-left
        path.closeSubpath()
        
        # Background: Semi-transparent dark grey
        painter.setBrush(QColor(30, 35, 40, 220))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
        
        # Border: Subtle glow line
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.drawPath(path)
        
        # --- Draw Top Tab (The Blue/Cyan Header) ---
        tab_w = 140
        tab_h = 22
        tab_path = QPainterPath()
        tab_x = 20
        # Trapezoid shape for the tab
        tab_path.moveTo(tab_x, 15)
        tab_path.lineTo(tab_x + 10, 0)
        tab_path.lineTo(tab_x + tab_w - 10, 0)
        tab_path.lineTo(tab_x + tab_w, 15)
        tab_path.closeSubpath()
        
        # Tab Glow Background
        tab_grad = QLinearGradient(QPointF(tab_x, 0), QPointF(tab_x, 15))
        tab_grad.setColorAt(0, QColor(0, 180, 255, 200))
        tab_grad.setColorAt(1, QColor(0, 100, 200, 150))
        painter.setBrush(tab_grad)
        painter.drawPath(tab_path)
        
        # Tab Text
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Monospace", 8, QFont.Weight.Bold))
        painter.drawText(QRectF(tab_x, 0, tab_w, 15), Qt.AlignmentFlag.AlignCenter, "ANANYA_CORE_OS_v1.0")

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = QWidget()
    window.setStyleSheet("background-color: #111111;") # Dark background for preview
    layout = QVBoxLayout(window)
    widget = ChatWidget()
    layout.addWidget(widget)
    window.resize(400, 550)
    window.show()
    sys.exit(app.exec())
