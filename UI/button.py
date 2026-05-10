import sys
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt, QSize, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPainterPath, QFont

class TacticalDock(QWidget):
    # Signals
    chat_clicked = pyqtSignal()
    memory_clicked = pyqtSignal()
    camera_clicked = pyqtSignal()
    mini_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 32) # Expanded for 5 icons
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.icons = ["chat", "memory", "camera", "mini", "settings"]
        self.active_index = 0 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        icon_size = 16
        spacing = 40 
        y_center = 12
        
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
        indicator_y = y_center + 18
        self.draw_indicator(painter, w // 2, indicator_y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            segment = self.width() / 5
            if x < segment:
                self.active_index = 0
                self.chat_clicked.emit()
            elif x < segment * 2:
                self.active_index = 1
                self.memory_clicked.emit()
            elif x < segment * 3:
                self.active_index = 2
                self.camera_clicked.emit()
            elif x < segment * 4:
                self.active_index = 3
                self.mini_clicked.emit()
            else:
                self.active_index = 4
                self.settings_clicked.emit()
            self.update()

    def draw_tactical_icon(self, painter, x, y, icon_type, active=False):
        painter.save()
        painter.translate(x, y)
        
        color = QColor(255, 255, 255) if active else QColor(200, 200, 200, 180)
        painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        s = 6 # tiny icon half-size
        
        if icon_type == "core":
            # Outer broken square
            painter.drawPolyline([
                QPointF(s*0.7, -s*0.7),
                QPointF(-s, -s),
                QPointF(-s, s),
                QPointF(s*0.7, s*0.7)
            ])
            # Inner square
            painter.drawRect(QRectF(-s/3, -s/3, (s/3)*2, (s/3)*2))
            # Dot in center
            painter.setBrush(color)
            painter.drawRect(QRectF(-0.75, -0.75, 1.5, 1.5))

            
        elif icon_type == "chat":
            path = QPainterPath()
            path.addRect(QRectF(-s, -s+2, s*2, s*1.5))
            # Tail
            path.moveTo(-s+5, s-2)
            path.lineTo(-s+2, s+2)
            path.lineTo(-s+8, s-2)
            painter.drawPath(path)

            
        elif icon_type == "memory":
            # Stylized brain/chip icon
            painter.drawRect(QRectF(-s, -s, s*2, s*2))

            painter.drawLine(int(-s), 0, int(s), 0)
            painter.drawLine(0, int(-s), 0, int(s))
            # Nodes
            painter.setBrush(color)
            painter.drawEllipse(QPointF(-s, -s), 1.5, 1.5)
            painter.drawEllipse(QPointF(s, -s), 1.5, 1.5)
            painter.drawEllipse(QPointF(-s, s), 1.5, 1.5)
            painter.drawEllipse(QPointF(s, s), 1.5, 1.5)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
        elif icon_type == "camera":
            # Body
            painter.drawRect(QRectF(-s, -s+4, s*1.4, s*1.2))

            # Lens
            path = QPainterPath()
            path.moveTo(s*0.5, -s+6)
            path.lineTo(s, -s+2)
            path.lineTo(s, s+2)
            path.lineTo(s*0.5, s-2)
            path.closeSubpath()
            painter.drawPath(path)
            
        elif icon_type == "mini":
            # Corner overlay icon
            painter.drawRect(QRectF(-s, -s, s*2, s*2))
            painter.drawRect(QRectF(s-3, s-3, 3, 3)) # inner small corner box
            
        elif icon_type == "settings":
            # Stylized gear/cogs
            painter.drawEllipse(QPointF(0, 0), s-2, s-2)
            # Teeth
            for i in range(8):
                painter.save()
                painter.rotate(i * 45)
                painter.drawLine(0, int(-s+2), 0, int(-s))
                painter.restore()

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
        painter.drawRect(QRectF(x - 22 - 1, y - 1, 2, 2))
        # Center Pill -> Bar
        painter.drawRect(QRectF(x - 8, y - 1, 16, 2))
        # Right Dot
        painter.drawRect(QRectF(x + 22 - 1, y - 1, 2, 2))


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
