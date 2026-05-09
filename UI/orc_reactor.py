import sys
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QPainterPath

class OrcReactor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(550, 550)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Animation setup
        self.rotation_angle = 0
        self.rotation_angle_3 = 0
        self.rotation_angle_4 = 0
        self.rotation_angle_5 = 0
        self.rotation_angle_6 = 0
        self.rotation_angle_7 = 0
        self.rotation_angle_8 = 0
        self.rotation_angle_9 = 0
        self.rotation_angle_10 = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16) # ~60 FPS

    def update_animation(self):
        self.rotation_angle += 2    # Clockwise for Circle 2
        self.rotation_angle_3 -= 1  # Counter-clockwise for Circle 3
        self.rotation_angle_4 += 3  # Fast clockwise for Circle 4
        self.rotation_angle_5 -= 2  # Counter-clockwise for Circle 5
        self.rotation_angle_6 += 1.5 # Clockwise for Circle 6
        self.rotation_angle_7 -= 1  # Counter-clockwise for Circle 7
        self.rotation_angle_8 += 0.5 # Slow clockwise for Circle 8
        self.rotation_angle_9 -= 0.8 # Slow counter-clockwise for Circle 9
        self.rotation_angle_10 += 0.3 # Very slow clockwise for Circle 10
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = 80
        outer_radius = 85
        circle3_radius = 95
        circle4_radius = 115
        circle5_radius = 125
        circle6_radius = 135
        circle7_radius = 147
        circle8_radius = 175
        circle9_radius = 220
        circle10_radius = 240
        
        # Circle 10 (Outer-most, Sensor Array)
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle_10)
        painter.translate(-center)
        
        marker_pen10 = QPen(QColor(150, 150, 150), 1.5)
        painter.setPen(marker_pen10)
        dot_size10 = 2
        
        import math
        for angle in [45, 135, 225, 315]:
            rad = math.radians(angle)
            # Draw only 1 dot at each diagonal
            dot_radius = circle10_radius
            px = center.x() + dot_radius * math.cos(rad)
            py = center.y() + dot_radius * math.sin(rad)
            painter.setBrush(QColor(150, 150, 150))
            painter.drawEllipse(QPointF(px, py), dot_size10/2, dot_size10/2)
        
        painter.restore()
        
        # Circle 9 (Outer-most, HUD markers)
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle_9)
        painter.translate(-center)
        
        marker_pen9 = QPen(QColor(255, 255, 255), 1.5)
        painter.setPen(marker_pen9)
        marker_len9 = 8
        
        # Draw 4 cardinal markers (Top, Bottom, Left, Right)
        # Top
        painter.drawLine(int(center.x()), int(center.y() - circle9_radius - marker_len9/2),
                         int(center.x()), int(center.y() - circle9_radius + marker_len9/2))
        # Bottom
        painter.drawLine(int(center.x()), int(center.y() + circle9_radius - marker_len9/2),
                         int(center.x()), int(center.y() + circle9_radius + marker_len9/2))
        # Left
        painter.drawLine(int(center.x() - circle9_radius - marker_len9/2), int(center.y()),
                         int(center.x() - circle9_radius + marker_len9/2), int(center.y()))
        # Right
        painter.drawLine(int(center.x() + circle9_radius - marker_len9/2), int(center.y()),
                         int(center.x() + circle9_radius + marker_len9/2), int(center.y()))
        
        # Draw 4 diagonal markers (Double Line Style)
        import math
        offset = 1.5 # Offset for double line
        for angle in [45, 135, 225, 315]:
            rad = math.radians(angle)
            # Parallel offset logic: shift the points perpendicular to the radial direction
            perp_rad = rad + math.pi/2
            dx = math.cos(perp_rad) * offset
            dy = math.sin(perp_rad) * offset
            
            for side in [-1, 1]:
                x_start = center.x() + (circle9_radius - marker_len9/2) * math.cos(rad) + side * dx
                y_start = center.y() + (circle9_radius - marker_len9/2) * math.sin(rad) + side * dy
                x_end = center.x() + (circle9_radius + marker_len9/2) * math.cos(rad) + side * dx
                y_end = center.y() + (circle9_radius + marker_len9/2) * math.sin(rad) + side * dy
                painter.drawLine(int(x_start), int(y_start), int(x_end), int(y_end))
        
        painter.restore()
        
        # Circle 8 (Outer-most, Dotted)
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle_8)
        painter.translate(-center)
        
        dot_pen = QPen(QColor(200, 200, 200), 2)
        dot_pen.setStyle(Qt.PenStyle.CustomDashLine)
        dot_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        # r = 175, C = 1099.5, with 64 dots: 1099.5 / 64 = 17.18
        dot_pen.setDashPattern([0.01, 17.18]) 
        painter.setPen(dot_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw two arcs to leave gaps at top (90 deg) and bottom (270 deg)
        # Qt angles are in 1/16th of a degree. 90 deg is top, 270 is bottom.
        # Let's leave a 10 degree gap at each.
        rect = QRectF(center.x() - circle8_radius, center.y() - circle8_radius, 
                      circle8_radius * 2, circle8_radius * 2)
        
        # Right arc (from bottom gap to top gap)
        painter.drawArc(rect, (270 + 5) * 16, (180 - 10) * 16)
        # Left arc (from top gap to bottom gap)
        painter.drawArc(rect, (90 + 5) * 16, (180 - 10) * 16)
        
        # Top and Bottom vertical markers (Drawn INSIDE to rotate together)
        marker_pen = QPen(QColor(200, 200, 200), 2)
        painter.setPen(marker_pen)
        marker_len = 5
        # Top
        painter.drawLine(int(center.x()), int(center.y() - circle8_radius - marker_len/2),
                         int(center.x()), int(center.y() - circle8_radius + marker_len/2))
        # Bottom
        painter.drawLine(int(center.x()), int(center.y() + circle8_radius - marker_len/2),
                         int(center.x()), int(center.y() + circle8_radius + marker_len/2))
        
        painter.restore()
        
        # Circle 7 (Outer-most, White, Blade cut)
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle_7)
        painter.translate(-center)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255))
        
        path7 = QPainterPath()
        start_angle7 = -60
        span_angle7 = -30
        thickness7 = 4
        
        path7.arcMoveTo(center.x() - circle7_radius, center.y() - circle7_radius, circle7_radius * 2, circle7_radius * 2, start_angle7)
        path7.arcTo(center.x() - circle7_radius, center.y() - circle7_radius, circle7_radius * 2, circle7_radius * 2, start_angle7, span_angle7)
        
        inner_r7 = circle7_radius - thickness7
        path7.arcTo(center.x() - inner_r7, center.y() - inner_r7, inner_r7 * 2, inner_r7 * 2, start_angle7 + span_angle7 - 5, - (span_angle7 - 10))
        path7.closeSubpath()
        painter.drawPath(path7)
        painter.restore()
        
        # Circle 6 (Outer-most, White, 1/4 arc)
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle_6)
        painter.translate(-center)
        
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(int(center.x() - circle6_radius), int(center.y() - circle6_radius), 
                        int(circle6_radius * 2), int(circle6_radius * 2), 
                        90 * 16, 90 * 16)
        painter.restore()
        
        # Circle 5 (Outer-most, White, 1/4 arc)
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle_5)
        painter.translate(-center)
        
        painter.setPen(QPen(QColor(180, 180, 180), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(int(center.x() - circle5_radius), int(center.y() - circle5_radius), 
                        int(circle5_radius * 2), int(circle5_radius * 2), 
                        180 * 16, 90 * 16)
        painter.restore()
        
        # Circle 4 (Outer-most, White, 1/4 arc)
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle_4)
        painter.translate(-center)
        
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(int(center.x() - circle4_radius), int(center.y() - circle4_radius), 
                        int(circle4_radius * 2), int(circle4_radius * 2), 
                        0, 90 * 16)
        painter.restore()
        
        # Circle 3 (Outer-most, Light Blue)
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle_3)
        painter.translate(-center)
        
        painter.setPen(QPen(QColor("#00CCFF"), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # Full solid circle
        painter.drawEllipse(center, circle3_radius, circle3_radius)
        painter.restore()
        
        # Circle 2 (outer) - Quarter arc with diagonal "blade" cuts
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle)
        painter.translate(-center)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255))
        
        outer_path = QPainterPath()
        # Define angles for the slice (start and end)
        # We use a small offset between inner and outer points to create the diagonal cut
        start_angle = -90
        end_angle = -60
        thickness = 5
        
        # Outer Arc
        outer_path.arcMoveTo(center.x() - outer_radius, center.y() - outer_radius, outer_radius * 2, outer_radius * 2, start_angle)
        outer_path.arcTo(center.x() - outer_radius, center.y() - outer_radius, outer_radius * 2, outer_radius * 2, start_angle, end_angle)
        
        # Diagonal cut at the end (tip)
        inner_r = outer_radius - thickness
        outer_path.arcTo(center.x() - inner_r, center.y() - inner_r, inner_r * 2, inner_r * 2, start_angle + end_angle - 5, - (end_angle - 10))
        
        # Diagonal cut at the start
        outer_path.closeSubpath()
        painter.drawPath(outer_path)
        painter.restore()
        
        # Circle 1 (inner)
        painter.setPen(QPen(Qt.GlobalColor.white, 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius, radius)

        # Draw "ANANYA" Text
        font = QFont("Inter", 18) # Clean sans-serif
        if not font.exactMatch(): font = QFont("Arial", 18) # Fallback
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6) # Futuristic spacing
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.white)
        
        # Center text precisely
        metrics = painter.fontMetrics()
        text = "ANANYA"
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.ascent()
        
        painter.drawText(
            int(center.x() - text_width / 2),
            int(center.y() + text_height / 3), # Offset for vertical centering
            text
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OrcReactor()
    window.resize(600, 600)
    window.setStyleSheet("background-color: #010409;")
    window.show()
    sys.exit(app.exec())
