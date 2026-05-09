import sys
from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtCore import Qt, QPoint, QRectF, pyqtSlot
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QBrush, QPen, QPainterPath
from UI.orc_reactor import OrcReactor
from UI.widget import ChatWidget
from UI.button import TacticalDock

class DashboardUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.showMaximized()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.status = "IDLE"
        self.drag_pos = QPoint()

        # Initialize Orc Reactor
        self.reactor = OrcReactor(self)
        
        # Initialize Chat Widget
        self.chat_widget = ChatWidget(self)
        self.chat_widget.resize(280, 400)
        
        # Initialize Tactical Dock
        self.dock = TacticalDock(self)
        
        # Connect Signals
        self.dock.chat_clicked.connect(self.chat_widget.toggle_visibility)
        # Placeholder for main app connection
        self.chat_widget.command_entered.connect(lambda cmd: print(f"Command received: {cmd}"))
        
        self.layout_components()

    def layout_components(self):
        # 1. Center the reactor in the window
        if hasattr(self, 'reactor'):
            rect_width = self.reactor.width()
            rect_height = self.reactor.height()
            self.reactor.move(
                int((self.width() - rect_width) / 2),
                int((self.height() - rect_height) / 2)
            )
        
        # 2. Position Chat Widget at Bottom-Right
        if hasattr(self, 'chat_widget'):
            margin = 30
            self.chat_widget.move(
                self.width() - self.chat_widget.width() - margin,
                self.height() - self.chat_widget.height() - margin
            )

        # 3. Position Tactical Dock at Bottom-Center
        if hasattr(self, 'dock'):
            bottom_margin = 10
            self.dock.move(
                int((self.width() - self.dock.width()) / 2),
                int(self.height() - self.dock.height() - bottom_margin)
            )

    @pyqtSlot(str)
    def add_terminal_log(self, msg):
        if not hasattr(self, 'chat_widget') or not self.chat_widget:
            return
            
        if msg.startswith("You: "):
            self.chat_widget.add_log(f"$ {msg[5:]}", "command")
        elif msg.startswith("Ananya: "):
            self.chat_widget.add_log(f"> {msg[8:]}", "system")
        else:
            self.chat_widget.add_log(msg, "plain")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.layout_components()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Background Gradient (Matches the screenshot's dark tone)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#010409"))
        gradient.setColorAt(0.6, QColor("#030810"))
        gradient.setColorAt(1, QColor("#010409"))
        
        c = 40  # Cut size
        w = self.width()
        h = self.height()
        path = QPainterPath()
        path.moveTo(c, 0)
        path.lineTo(w - c, 0)
        path.lineTo(w, c)
        path.lineTo(w, h - c)
        path.lineTo(w - c, h)
        path.lineTo(c, h)
        path.lineTo(0, h - c)
        path.lineTo(0, c)
        path.closeSubpath()
        painter.fillPath(path, QBrush(gradient))

        # 2. Top Center Futuristic Notch Line (Gray)
        accent_color = QColor("#AAAAAA") 

        
        # Dimensions
        w_total = 250
        w_side = 30
        slope = 10
        y_base = 5
        y_drop = 10
        x_start = (self.width() - w_total) // 2

        # Create Path
        notch_path = QPainterPath()
        notch_path.moveTo(x_start, y_base)
        notch_path.lineTo(x_start + w_side, y_base)
        notch_path.lineTo(x_start + w_side + slope, y_drop)
        notch_path.lineTo(x_start + w_total - w_side - slope, y_drop)
        notch_path.lineTo(x_start + w_total - w_side, y_base)
        notch_path.lineTo(x_start + w_total, y_base)



        # Draw Main Line (Solid)
        main_pen = QPen(accent_color, 1.2)
        painter.setPen(main_pen)
        painter.drawPath(notch_path)

        # 3. Four Corner Futuristic Brackets with Connecting Lines
        corner_color = QColor("#FFFFFF")
        corner_pen = QPen(corner_color, 1.2)
        painter.setPen(corner_pen)
        
        c_rad = 6
        offset = 10  # Offset from window edge
        bottom_offset = 20
        # Color for the curves (Light blue from the image)
        curve_pen = QPen(QColor("#CCCCCC"), 1.5)
        painter.setPen(curve_pen)
        
        # Top-Left Corner
        tl_path = QPainterPath()
        tl_path.arcMoveTo(QRectF(offset, offset, c_rad*2, c_rad*2), 180)
        tl_path.arcTo(QRectF(offset, offset, c_rad*2, c_rad*2), 180, -90)
        painter.drawPath(tl_path)
        
        # Top-Right Corner
        tr_path = QPainterPath()
        tr_path.arcMoveTo(QRectF(self.width() - offset - c_rad*2, offset, c_rad*2, c_rad*2), 0)
        tr_path.arcTo(QRectF(self.width() - offset - c_rad*2, offset, c_rad*2, c_rad*2), 0, 90)
        painter.drawPath(tr_path)
        
        # Bottom-Left Corner
        bl_path = QPainterPath()
        bl_path.arcMoveTo(QRectF(offset, self.height() - bottom_offset - c_rad*2, c_rad*2, c_rad*2), 180)
        bl_path.arcTo(QRectF(offset, self.height() - bottom_offset - c_rad*2, c_rad*2, c_rad*2), 180, 90)
        painter.drawPath(bl_path)
        
        # Bottom-Right Corner
        br_path = QPainterPath()
        br_path.arcMoveTo(QRectF(self.width() - offset - c_rad*2, self.height() - bottom_offset - c_rad*2, c_rad*2, c_rad*2), 0)
        br_path.arcTo(QRectF(self.width() - offset - c_rad*2, self.height() - bottom_offset - c_rad*2, c_rad*2, c_rad*2), 0, -90)
        painter.drawPath(br_path)

        # Connecting Lines between corners (left, right, bottom)
        gap = 4
        bottom_gap = 5
        connect_pen = QPen(QColor("#222222"), 1.5)
        painter.setPen(connect_pen)

        # Left side connecting line
        left_path = QPainterPath()
        left_path.moveTo(offset, offset + c_rad + gap)
        left_path.lineTo(offset, self.height() - bottom_offset - c_rad - gap)
        painter.drawPath(left_path)

        # Right side connecting line
        right_path = QPainterPath()
        right_path.moveTo(self.width() - offset, offset + c_rad + gap)
        right_path.lineTo(self.width() - offset, self.height() - bottom_offset - c_rad - gap)
        painter.drawPath(right_path)

        # Bottom side connecting line
        bottom_path = QPainterPath()
        bottom_path.moveTo(offset + c_rad + bottom_gap, self.height() - bottom_offset)
        bottom_path.lineTo(self.width() - offset - c_rad - bottom_gap, self.height() - bottom_offset)
        painter.drawPath(bottom_path)

        # 4. Grid Box Lines Inside
        grid_pen = QPen(QColor("#222222"), 1.0)
        painter.setPen(grid_pen)
        
        margin = 40
        margin_sides = 80
        grid_cols = 40
        grid_rows = 30
        
        grid_left = margin_sides
        grid_right = self.width() - margin_sides
        grid_top = margin
        grid_bottom = self.height() - margin
        
        v_step = (grid_right - grid_left) / grid_cols
        h_step = (grid_bottom - grid_top) / grid_rows
        
        for i in range(1, grid_cols):
            x = grid_left + v_step * i
            grid_path = QPainterPath()
            grid_path.moveTo(x, grid_top)
            grid_path.lineTo(x, grid_bottom)
            painter.drawPath(grid_path)
        
        dot_offset = 5
        dot_radius = 2.5
        painter.setBrush(QColor("#222222"))
        
        for i in range(1, grid_rows):
            y = grid_top + h_step * i
            grid_path = QPainterPath()
            grid_path.moveTo(grid_left, y)
            grid_path.lineTo(grid_right, y)
            painter.drawPath(grid_path)
            
            # Start dot
            start_dot = QPainterPath()
            start_dot.addEllipse(grid_left - dot_offset - dot_radius, y - dot_radius, dot_radius * 2, dot_radius * 2)
            painter.drawPath(start_dot)
            # End dot
            end_dot = QPainterPath()
            end_dot.addEllipse(grid_right + dot_offset - dot_radius, y - dot_radius, dot_radius * 2, dot_radius * 2)
            painter.drawPath(end_dot)


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()

    def set_status(self, state):
        self.status = state
        if hasattr(self, 'reactor'):
            self.reactor.set_status(state)
        self.update()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = DashboardUI()
    window.show()
    sys.exit(app.exec())