import sys
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt, QSize, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPainterPath, QFont

class TacticalDock(QWidget):
    # Signals
    chat_clicked = pyqtSignal()
    camera_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 60) # Smaller width for 2 icons
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.icons = ["chat", "camera"]
        self.active_index = 0 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        icon_size = 24
        spacing = 45
        y_center = 25
        
        start_x = (w - (len(self.icons) * spacing)) // 2 + spacing // 2
        
        for i, icon_type in enumerate(self.icons):
            x = start_x + (i * spacing)
            
            # Draw Separator (except after the last icon)
            if i < len(self.icons) - 1:
                sep_x = x + (spacing // 2)
                painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
                painter.drawLine(int(sep_x), y_center - 10, int(sep_x), y_center + 10)
            
            # Draw Icon
            self.draw_tactical_icon(painter, x, y_center, icon_type, active=(i == self.active_index))

        # Draw Bottom Indicator (Dot - Pill - Dot)
        indicator_y = y_center + 25
        self.draw_indicator(painter, w // 2, indicator_y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            # Simple hit detection
            if x < self.width() / 2:
                self.active_index = 0
                self.chat_clicked.emit()
            else:
                self.active_index = 1
                self.camera_clicked.emit()
            self.update()

    def draw_tactical_icon(self, painter, x, y, icon_type, active=False):
        painter.save()
        painter.translate(x, y)
        
        color = QColor(255, 255, 255) if active else QColor(200, 200, 200, 180)
        painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        s = 10 # icon half-size
        
        if icon_type == "core":
            # Outer broken circle
            painter.drawArc(QRectF(-s, -s, s*2, s*2), 45 * 16, 270 * 16)
            # Inner circle
            painter.drawEllipse(QRectF(-s/3, -s/3, (s/3)*2, (s/3)*2))
            # Dot in center
            painter.setBrush(color)
            painter.drawEllipse(QPointF(0, 0), 1.5, 1.5)
            
        elif icon_type == "chat":
            path = QPainterPath()
            path.addRoundedRect(QRectF(-s, -s+2, s*2, s*1.5), 3, 3)
            # Tail
            path.moveTo(-s+5, s-2)
            path.lineTo(-s+2, s+2)
            path.lineTo(-s+8, s-2)
            painter.drawPath(path)
            
        elif icon_type == "camera":
            # Body
            painter.drawRoundedRect(QRectF(-s, -s+4, s*1.4, s*1.2), 2, 2)
            # Lens
            path = QPainterPath()
            path.moveTo(s*0.5, -s+6)
            path.lineTo(s, -s+2)
            path.lineTo(s, s+2)
            path.lineTo(s*0.5, s-2)
            path.closeSubpath()
            painter.drawPath(path)
            
        elif icon_type == "music":
            # Note head
            painter.setBrush(color)
            painter.drawEllipse(QPointF(-s+4, s-2), 4, 3)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            # Stem
            painter.drawLine(int(-s+8), int(s-2), int(-s+8), int(-s+2))
            # Flag
            path = QPainterPath()
            path.moveTo(-s+8, -s+2)
            path.cubicTo(0, -s, s, -s+5, s-2, 0)
            painter.drawPath(path)

        painter.restore()

    def draw_indicator(self, painter, x, y):
        # Dot - Pill - Dot
        color = QColor(255, 255, 255, 150)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        
        # Left Dot
        painter.drawEllipse(QPointF(x - 25, y), 3, 3)
        # Center Pill
        painter.drawRoundedRect(QRectF(x - 10, y - 3, 20, 6), 3, 3)
        # Right Dot
        painter.drawEllipse(QPointF(x + 25, y), 3, 3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    window.setStyleSheet("background-color: #222222;")
    layout = QHBoxLayout(window)
    dock = TacticalDock()
    layout.addWidget(dock)
    window.resize(400, 200)
    window.show()
    sys.exit(app.exec())
