import sys
from PyQt6.QtWidgets import QMainWindow, QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint, QRectF, pyqtSlot
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QBrush, QPen, QPainterPath, QRegion
from UI.orc_reactor import OrcReactor
from UI.widget import ChatWidget, MemoryWidget, SettingsWidget, CameraWidget
from UI.button import TacticalDock

class DashboardUI(QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.dock.mini_clicked.connect(lambda: self.set_mini_mode(not self.mini_mode))
        
        # Connect Chat Command
        self.chat_widget.command_entered.connect(self.handle_command)
        
        self.layout_components()
        self.showMaximized()

    def get_tactical_path(self, w, h):
        """Returns a premium rounded rectangular path for the tactical HUD."""
        path = QPainterPath()
        radius = 24
        path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
        return path


    def set_mini_mode(self, enabled):
        """Toggles between full tactical dashboard and mini-overlay mode."""
        self.mini_mode = enabled
        self.hide() # Crucial for Windows to apply flag changes
        
        if enabled:
            # Hide all UI except the core reactor
            self.chat_widget.hide()
            self.memory_widget.hide()
            self.settings_widget.hide()
            self.camera_widget.hide()
            self.dock.hide()
            
            # Shrink Reactor
            self.reactor.scale = 0.5
            self.reactor.setFixedSize(200, 200)
            
            # Change Window Flags for overlay
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
            
            # Resize and move the window to bottom-right
            screen = QApplication.primaryScreen().geometry()
            size = 220
            self.setGeometry(
                screen.width() - size - 20,
                screen.height() - size - 60, # Above taskbar
                size, size
            )
            
            # Center reactor in the now-small window
            self.reactor.move(10, 10)
            
            # Set circular mask
            self.setMask(QRegion(0, 0, size, size, QRegion.RegionType.Ellipse))
        else:
            self.clearMask()
            self.reactor.scale = 0.7
            self.reactor.setFixedSize(400, 400)
            
            # Restore main window flags
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            
            # Show components
            self.dock.show()
            self.layout_components()
            self.showMaximized()
            
        self.show()
        self.raise_()
        self.activateWindow()
        self.update()


    def handle_command(self, cmd):
        """Standard command handler for dashboard buttons."""
        cmd_lower = cmd.lower()
        if "dashboard" in cmd_lower or "full" in cmd_lower:
            self.set_mini_mode(False)
        elif "mini" in cmd_lower or "hide" in cmd_lower:
            self.set_mini_mode(True)

    def layout_components(self):
        if hasattr(self, 'reactor'):
            self.reactor.move(
                int((self.width() - self.reactor.width()) / 2),
                int((self.height() - self.reactor.height()) / 2)
            )
        
        margin = 30
        if hasattr(self, 'chat_widget'):
            self.chat_widget.move(
                self.width() - self.chat_widget.width() - margin,
                self.height() - self.chat_widget.height() - margin
            )
        if hasattr(self, 'memory_widget'):
            self.memory_widget.move(margin, self.height() - self.memory_widget.height() - margin)
            
        if hasattr(self, 'settings_widget'):
            self.settings_widget.move(
                int((self.width() - self.settings_widget.width()) / 2),
                int((self.height() - self.settings_widget.height()) / 2) - 50
            )
        if hasattr(self, 'camera_widget'):
            self.camera_widget.move(self.width() - self.camera_widget.width() - margin, margin)

        if hasattr(self, 'dock'):
            dock_bottom_margin = 22 
            self.dock.move(
                int((self.width() - self.dock.width()) / 2),
                int(self.height() - self.dock.height() - dock_bottom_margin)
            )

    @pyqtSlot(str, str)
    def add_terminal_log(self, msg, style="plain"):
        """Routes logs to the ChatWidget as stylized bubbles."""
        if hasattr(self, 'chat_widget') and self.chat_widget:
            if style == "streaming":
                self.chat_widget.add_log(msg, "streaming")
                return

            if msg.startswith("You: "):
                text = msg[5:].strip()
                self.chat_widget.add_log(text, "user")
            elif msg.startswith("Ananya: "):
                text = msg[8:].strip()
                self.chat_widget.add_log(text, "ai")
            elif msg.startswith("SYS:"):
                text = msg[4:].strip()
                self.chat_widget.add_log(text, "system")
            else:
                self.chat_widget.add_log(msg, style)



    @pyqtSlot(dict)
    def refresh_memory_ui(self, memory_dict):
        if hasattr(self, 'memory_widget') and self.memory_widget:
            self.memory_widget.refresh_memory(memory_dict)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.layout_components()

    def paintEvent(self, event):
        if self.mini_mode:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 1. Background
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # 2. Main Background Path (Sharp Cut Corners)
        path = self.get_tactical_path(w, h)
        gradient = QLinearGradient(0, 0, w, h)
        gradient.setColorAt(0, QColor("#010409"))
        gradient.setColorAt(0.6, QColor("#030810"))
        gradient.setColorAt(1, QColor("#010409"))
        painter.fillPath(path, QBrush(gradient))
        
        # CLIP to prevent any leakage
        painter.setClipPath(path)

        # 3. Top Center Notch (Redesigned for Premium Look)
        accent_color = QColor("#0066FF") 
        w_notch, w_side, slope, y_base, y_drop = 300, 40, 15, 0, 12
        x_start = (w - w_notch) // 2
        notch_path = QPainterPath()
        notch_path.moveTo(x_start, y_base)
        notch_path.lineTo(x_start + w_side, y_base)
        notch_path.lineTo(x_start + w_side + slope, y_drop)
        notch_path.lineTo(x_start + w_notch - w_side - slope, y_drop)
        notch_path.lineTo(x_start + w_notch - w_side, y_base)
        notch_path.lineTo(x_start + w_notch, y_base)
        
        painter.setPen(QPen(accent_color, 2.0))
        painter.drawPath(notch_path)
        
        # Inner glow for notch
        glow_pen = QPen(QColor(0, 102, 255, 60), 4.0)
        painter.setPen(glow_pen)
        painter.drawPath(notch_path)

        # 4. Futuristic Curved Corner Brackets (Glowing & Purely Curved)
        corner_pen = QPen(QColor("#00FFCC"), 2.2) # Cyan glow
        painter.setPen(corner_pen)
        c_rad = 35 # Organic curve
        offset = 12
        
        # Top-Left Arc
        tl_path = QPainterPath()
        tl_path.arcMoveTo(QRectF(offset, offset, c_rad*2, c_rad*2), 160)
        tl_path.arcTo(QRectF(offset, offset, c_rad*2, c_rad*2), 160, -50)
        painter.drawPath(tl_path)
        
        # Top-Right Arc
        tr_path = QPainterPath()
        tr_path.arcMoveTo(QRectF(w - offset - c_rad*2, offset, c_rad*2, c_rad*2), 20)
        tr_path.arcTo(QRectF(w - offset - c_rad*2, offset, c_rad*2, c_rad*2), 20, 50)
        painter.drawPath(tr_path)
        
        # Bottom-Left Arc
        bl_path = QPainterPath()
        bl_path.arcMoveTo(QRectF(offset, h - offset - c_rad*2, c_rad*2, c_rad*2), 200)
        bl_path.arcTo(QRectF(offset, h - offset - c_rad*2, c_rad*2, c_rad*2), 200, 50)
        painter.drawPath(bl_path)
        
        # Bottom-Right Arc
        br_path = QPainterPath()
        br_path.arcMoveTo(QRectF(w - offset - c_rad*2, h - offset - c_rad*2, c_rad*2, c_rad*2), 340)
        br_path.arcTo(QRectF(w - offset - c_rad*2, h - offset - c_rad*2, c_rad*2, c_rad*2), 340, -50)
        painter.drawPath(br_path)
        
        # Add subtle outer glow to corners
        glow_pen = QPen(QColor(0, 255, 204, 60), 6.0)
        painter.setPen(glow_pen)
        painter.drawPath(tl_path)
        painter.drawPath(tr_path)
        painter.drawPath(bl_path)
        painter.drawPath(br_path)


        # 5. Connecting Lines between corners
        gap = 10
        connect_pen = QPen(QColor("#1A1A1A"), 1.2)
        painter.setPen(connect_pen)

        # Fix: Using 'offset' instead of undefined 'b_offset'
        # Left side connecting line
        painter.drawLine(offset, offset + c_rad + gap, offset, h - offset - c_rad - gap)
        # Right side connecting line
        painter.drawLine(w - offset, offset + c_rad + gap, w - offset, h - offset - c_rad - gap)
        # Bottom side connecting line
        painter.drawLine(offset + c_rad + gap, h - offset, w - offset - c_rad - gap, h - offset)





        # 6. Grid
        gl, gr, gt, gb = 80, w - 80, 40, h - 40
        cols, rows = 40, 30
        vs, hs = (gr - gl) / cols, (gb - gt) / rows
        
        painter.setPen(QPen(QColor("#101010"), 1.0))
        for i in range(1, cols):
            x = gl + vs*i
            painter.drawLine(int(x), gt, int(x), gb)
        
        painter.setBrush(QColor("#101010"))
        for i in range(1, rows):
            y = gt + hs*i
            painter.drawLine(gl, int(y), gr, int(y))
            painter.drawEllipse(QRectF(gl-7.5, y-2.5, 5, 5))
            painter.drawEllipse(QRectF(gr+2.5, y-2.5, 5, 5))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()

    def mouseDoubleClickEvent(self, event):
        if self.mini_mode: self.set_mini_mode(False)
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_M: self.set_mini_mode(not self.mini_mode)
        elif event.key() == Qt.Key.Key_Escape: self.close()
        super().keyPressEvent(event)

    def set_status(self, state):
        self.status = state
        if hasattr(self, 'reactor'): self.reactor.set_status(state)
        self.update()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = DashboardUI()
    window.show()
    sys.exit(app.exec())