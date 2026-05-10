import sys
from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtCore import Qt, QPoint, QRectF, pyqtSlot
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QBrush, QPen, QPainterPath, QRegion
from UI.orc_reactor import OrcReactor
from UI.widget import ChatWidget, MemoryWidget, SettingsWidget, CameraWidget
from UI.button import TacticalDock

class DashboardUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.showMaximized()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.status = "IDLE"
        self.drag_pos = QPoint()
        self.mini_mode = False

        # Initialize Orc Reactor
        self.reactor = OrcReactor(self)
        
        # Initialize Widgets
        self.chat_widget = ChatWidget(self)
        self.chat_widget.resize(280, 400)
        
        self.memory_widget = MemoryWidget(self)
        self.memory_widget.resize(450, 600)

        self.settings_widget = SettingsWidget(self)
        self.settings_widget.resize(350, 420)

        self.camera_widget = CameraWidget(self)
        self.camera_widget.resize(480, 360)
        
        # Initialize Tactical Dock
        self.dock = TacticalDock(self)
        
        # Connect Signals
        self.dock.chat_clicked.connect(self.chat_widget.toggle_visibility)
        self.dock.memory_clicked.connect(self.memory_widget.toggle_visibility)
        self.dock.settings_clicked.connect(self.settings_widget.toggle_visibility)
        self.dock.camera_clicked.connect(self.camera_widget.toggle_visibility)
        
        # Placeholder for main app connection
        self.chat_widget.command_entered.connect(self.handle_command)
        
        self.layout_components()

    def set_mini_mode(self, enabled):
        """Toggles between full tactical dashboard and mini-overlay mode."""
        self.mini_mode = enabled
        
        if enabled:
            # 1. Hide peripheral components
            self.chat_widget.hide()
            self.memory_widget.hide()
            self.settings_widget.hide()
            self.camera_widget.hide()
            self.dock.hide()
            
            # 2. Scale down and reposition reactor
            self.reactor.scale = 0.4
            self.reactor.setMinimumSize(250, 250)
            self.reactor.resize(250, 250)
            margin = 10
            # Move to bottom right
            self.reactor.move(
                self.width() - self.reactor.width() - margin,
                self.height() - self.reactor.height() - margin
            )
            
            # 3. Window Behavior
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
            # Apply circular mask so only the reactor area captures mouse events
            mask_rect = self.reactor.geometry()
            self.setMask(QRegion(mask_rect, QRegion.RegionType.Ellipse))
            
        else:
            # 1. Restore Reactor
            self.reactor.scale = 0.7
            self.reactor.setMinimumSize(400, 400)
            self.reactor.resize(400, 400)
            
            # 2. Clear mask and restore window flags
            self.clearMask()
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
            
            # 3. Show Dock (widgets stay hidden unless toggled)
            self.dock.show()
            self.layout_components()
            
        self.show() 
        self.raise_()
        self.activateWindow()
        self.update()

    def handle_command(self, cmd):
        """Handles commands from the chat widget."""
        cmd_lower = cmd.lower()
        if "open" in cmd_lower:
            # Extract app name (simple logic)
            app_name = cmd_lower.split("open")[-1].strip()
            if app_name:
                self.launch_app(app_name)
            else:
                self.add_terminal_log("Ananya: Which application should I open?")
        elif "dashboard" in cmd_lower or "full" in cmd_lower:
            self.set_mini_mode(False)
            self.add_terminal_log("Ananya: Restoring full tactical interface.")
        elif "mini" in cmd_lower or "hide" in cmd_lower:
            self.set_mini_mode(True)
            self.add_terminal_log("Ananya: Switching to background overlay mode.")
        else:
            print(f"Command received: {cmd}")

    def launch_app(self, app_name):
        """Simulates opening an app and switches to mini mode."""
        self.add_terminal_log(f"You: open {app_name}")
        self.add_terminal_log(f"Ananya: Initializing {app_name.upper()} execution sequence. Switching to overlay.")
        
        # In a real implementation, you'd use something like:
        # os.startfile(app_name) or a lookup table for paths
        
        # Trigger mini mode transition
        self.set_mini_mode(True)

    def layout_components(self):
        # 1. Center the reactor in the window
        if hasattr(self, 'reactor'):
            rect_width = self.reactor.width()
            rect_height = self.reactor.height()
            self.reactor.move(
                int((self.width() - rect_width) / 2),
                int((self.height() - rect_height) / 2)
            )
        
        # 2. Position Widgets
        margin = 30
        if hasattr(self, 'chat_widget'):
            self.chat_widget.move(
                self.width() - self.chat_widget.width() - margin,
                self.height() - self.chat_widget.height() - margin
            )
        if hasattr(self, 'memory_widget'):
            self.memory_widget.move(
                margin,
                self.height() - self.memory_widget.height() - margin
            )
        if hasattr(self, 'settings_widget'):
            # Place settings in the middle-ish or near dock
            self.settings_widget.move(
                int((self.width() - self.settings_widget.width()) / 2),
                int((self.height() - self.settings_widget.height()) / 2) - 50
            )
        if hasattr(self, 'camera_widget'):
            # Place camera top-right
            self.camera_widget.move(
                self.width() - self.camera_widget.width() - margin,
                margin
            )

        # 3. Position Tactical Dock at Bottom-Center
        if hasattr(self, 'dock'):
            # The bottom connecting line is at height - 20
            # We place the dock slightly above it
            dock_bottom_margin = 22 
            self.dock.move(
                int((self.width() - self.dock.width()) / 2),
                int(self.height() - self.dock.height() - dock_bottom_margin)
            )

    @pyqtSlot(str)
    def add_terminal_log(self, msg):
        if not hasattr(self, 'chat_widget') or not self.chat_widget:
            return
            
        # Detect app opening from backend to trigger mini-mode
        if "[open_app]" in msg:
            self.set_mini_mode(True)

        if msg.startswith("You: "):
            self.chat_widget.add_log(f"$ {msg[5:]}", "command")
        elif msg.startswith("Ananya: "):
            self.chat_widget.add_log(f"> {msg[8:]}", "system")
        else:
            self.chat_widget.add_log(msg, "plain")

    @pyqtSlot(dict)
    def refresh_memory_ui(self, memory_dict):
        if hasattr(self, 'memory_widget') and self.memory_widget:
            self.memory_widget.refresh_memory(memory_dict)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.layout_components()

    def paintEvent(self, event):
        if hasattr(self, 'mini_mode') and self.mini_mode:
            return
            
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

    def mouseDoubleClickEvent(self, event):
        """Returns to full mode on double click if in mini mode."""
        if self.mini_mode:
            self.set_mini_mode(False)
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_M:
            self.set_mini_mode(not self.mini_mode)
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

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