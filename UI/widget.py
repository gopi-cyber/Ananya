import sys
import math
import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QFrame, QScrollArea, QSizePolicy, QPushButton)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QTimer, QPoint, QSize
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QPainterPath, QLinearGradient, QBrush, QImage, QPixmap, QFontMetrics

class ChatMessage(QFrame):
    def __init__(self, text, sender="user", parent=None):
        super().__init__(parent)
        self.sender = sender
        self.text = text
        
        layout = QVBoxLayout(self)

        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)
        
        # Sender Label
        sender_label = QLabel("YOU" if sender == "user" else "ANANYA")
        sender_label.setStyleSheet(f"""
            color: {'#0066ff' if sender == 'user' else '#00ffcc'};
            font-size: 9px;
            font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
            letter-spacing: 1px;
        """)
        if sender == "user":
            sender_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            sender_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            
        layout.addWidget(sender_label)
        
        # Content Bubble
        self.content_frame = QFrame()
        bubble_layout = QVBoxLayout(self.content_frame)
        bubble_layout.setContentsMargins(12, 10, 12, 10)
        
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        font = QFont("Segoe UI", 10)
        self.label.setFont(font)
        
        if sender == "user":
            self.label.setStyleSheet("color: #ffffff;")
            self.content_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 102, 255, 30);
                    border: 1px solid rgba(0, 102, 255, 60);
                    border-top-left-radius: 16px;
                    border-top-right-radius: 4px;
                    border-bottom-left-radius: 16px;
                    border-bottom-right-radius: 16px;
                }
            """)
        elif sender == "ai":
            self.label.setStyleSheet("color: #e0e0e0;")
            self.content_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 8);
                    border: 1px solid rgba(255, 255, 255, 15);
                    border-top-left-radius: 4px;
                    border-top-right-radius: 16px;
                    border-bottom-left-radius: 16px;
                    border-bottom-right-radius: 16px;
                }
            """)
        else: # System
            self.label.setStyleSheet("color: #888888; font-style: italic;")
            self.content_frame.setStyleSheet("background: transparent; border: none;")
            
        bubble_layout.addWidget(self.label)
        layout.addWidget(self.content_frame)
        
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)


class ChatWidget(QWidget):

    command_entered = pyqtSignal(str)
    file_selected = pyqtSignal(str) # Path to the file

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 450)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 35, 15, 15)
        self.main_layout.setSpacing(10)
        
        # 1. Message Area (Scrollable)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent;")
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Custom ScrollBar Styling
        self.scroll_area.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 20);
                min-height: 20px;
                border-radius: 2px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.msg_container = QWidget()
        self.msg_container.setStyleSheet("background: transparent;")
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.setContentsMargins(5, 5, 5, 5)
        self.msg_layout.setSpacing(15)
        self.msg_layout.addStretch() # Push messages to top
        
        self.scroll_area.setWidget(self.msg_container)
        self.main_layout.addWidget(self.scroll_area)
        
        # 2. Separator Line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: rgba(0, 102, 255, 40);")
        self.main_layout.addWidget(line)
        
        # 3. Input Area (Pill shaped)
        input_wrapper = QFrame()
        input_wrapper.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 5);
                border: 1px solid rgba(255, 255, 255, 10);
                border-radius: 20px;
            }
        """)
        input_layout = QHBoxLayout(input_wrapper)
        input_layout.setContentsMargins(15, 5, 10, 5)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask Ananya anything...")
        self.input_field.setFrame(False)
        self.input_field.setStyleSheet("background: transparent; color: white; font-size: 13px; padding: 5px 0;")
        
        self.send_btn = QPushButton("\u21B5") # Enter symbol
        self.send_btn.setFixedSize(28, 28)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066ff;
                color: white;
                border-radius: 14px;
                font-weight: bold;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0052cc;
            }
        """)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        self.main_layout.addWidget(input_wrapper)
        
        # Connect Signals
        self.input_field.returnPressed.connect(self.handle_input)
        self.send_btn.clicked.connect(self.handle_input)
        
        # 4. Attachment Button
        self.attach_btn = QPushButton("\ud83d\udcce Attach File")
        self.attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attach_btn.setStyleSheet("""
            QPushButton {
                color: #888888;
                background: transparent;
                border: none;
                font-size: 10px;
                text-align: left;
                padding-left: 10px;
            }
            QPushButton:hover { color: #ffffff; }
        """)
        self.attach_btn.clicked.connect(self.handle_attach)
        self.main_layout.addWidget(self.attach_btn)

    def handle_input(self):

        text = self.input_field.text().strip()
        if text:
            print(f"[UI] Input triggered: {text}")
            self.add_log(text, "user") # Use 'user' style
            self.command_entered.emit(text)
            self.input_field.clear()



    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.input_field.setFocus()

    def handle_attach(self):
        from PyQt6.QtWidgets import QFileDialog
        import os
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Attach File", "", 
            "All Files (*);;Images (*.png *.jpg *.jpeg);;Documents (*.pdf *.txt *.docx *.py *.js *.html *.css *.json)"
        )
        if file_path:
            self.file_selected.emit(file_path)
            self.add_log(f"> Attached: {os.path.basename(file_path)}", "system")

    def add_log(self, text, style="plain"):
        # Map styles to senders
        sender = "system"
        if style in ["user", "command"]:
            sender = "user"
        elif style == "system" or "Ananya:" in text:
            sender = "ai"
            text = text.replace("Ananya: ", "")
        
        # Create message widget
        msg_widget = ChatMessage(text, sender)
        
        # Layout for alignment
        align_layout = QHBoxLayout()
        align_layout.setContentsMargins(0, 0, 0, 0)
        
        if sender == "user":
            align_layout.addStretch()
            align_layout.addWidget(msg_widget)
            align_layout.setContentsMargins(40, 0, 0, 0) # Left padding for user
        elif sender == "ai":
            align_layout.addWidget(msg_widget)
            align_layout.addStretch()
            align_layout.setContentsMargins(0, 0, 40, 0) # Right padding for AI
        else:
            align_layout.addStretch()
            align_layout.addWidget(msg_widget)
            align_layout.addStretch()
            
        # Insert before the stretch at the end
        self.msg_layout.insertLayout(self.msg_layout.count() - 1, align_layout)
        
        # Auto-scroll
        QTimer.singleShot(100, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())


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

# --- Obsidian Graph Implementation ---

class GraphNode:
    def __init__(self, id, label, color, is_hub=False):
        self.id = id
        self.label = label
        self.color = color
        self.is_hub = is_hub
        self.pos = QPointF(0, 0)
        self.vel = QPointF(0, 0)
        self.radius = 6 if is_hub else 4
        self.opacity = 1.0
        self.hovered = False

class GraphEdge:
    def __init__(self, source, target):
        self.source = source
        self.target = target

class GraphArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes = []
        self.edges = []
        self.zoom = 1.0
        self.offset = QPointF(0, 0)
        self.dragging = False
        self.last_mouse_pos = QPoint()
        self.selected_node = None
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_physics)
        self.timer.start(16) # ~60 FPS
        
    def set_data(self, memory_dict):
        self.nodes = []
        self.edges = []
        
        # Central Hub
        core_node = GraphNode("core", "BRAIN", QColor("#9d7cd8"), True)
        self.nodes.append(core_node)
        
        colors = ["#7aa2f7", "#bb9af7", "#7dcfff", "#e0af68", "#9ece6a", "#f7768e"]
        
        for i, (cat, items) in enumerate(memory_dict.items()):
            cat_color = QColor(colors[i % len(colors)])
            # Category Hub
            cat_node = GraphNode(f"cat_{cat}", cat, cat_color, True)
            cat_node.pos = QPointF(math.cos(i) * 100, math.sin(i) * 100)
            self.nodes.append(cat_node)
            self.edges.append(GraphEdge(core_node, cat_node))
            
            for key, entry in items.items():
                val = entry.get("value") if isinstance(entry, dict) else entry
                # Entry Node
                item_node = GraphNode(f"node_{key}", f"{key}: {val}", cat_color)
                item_node.pos = cat_node.pos + QPointF(math.cos(len(self.nodes)) * 20, math.sin(len(self.nodes)) * 20)
                self.nodes.append(item_node)
                self.edges.append(GraphEdge(cat_node, item_node))

    def update_physics(self):
        if not self.nodes: return
        
        # Simple Force-Directed Layout
        dt = 0.5
        repulsion = 1500.0
        spring = 0.05
        damping = 0.8
        
        for i, node in enumerate(self.nodes):
            # 1. Repulsion from all other nodes
            for j, other in enumerate(self.nodes):
                if i == j: continue
                dx = node.pos.x() - other.pos.x()
                dy = node.pos.y() - other.pos.y()
                dist_sq = dx*dx + dy*dy + 0.1
                if dist_sq < 40000:
                    force = repulsion / dist_sq
                    node.vel += QPointF(dx/math.sqrt(dist_sq) * force, dy/math.sqrt(dist_sq) * force)
            
            # 2. Gravity to center
            node.vel -= node.pos * 0.005

        # 3. Spring force along edges
        for edge in self.edges:
            dx = edge.target.pos.x() - edge.source.pos.x()
            dy = edge.target.pos.y() - edge.source.pos.y()
            dist = math.sqrt(dx*dx + dy*dy) + 0.1
            force = (dist - 40) * spring
            move = QPointF(dx/dist * force, dy/dist * force)
            edge.source.vel += move
            edge.target.vel -= move

        # Update positions
        for node in self.nodes:
            node.pos += node.vel * dt
            node.vel *= damping
            
        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 0.9
        self.zoom *= factor
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check for node click
            m_pos = (event.position() - QPointF(self.width()/2, self.height()/2)) / self.zoom - self.offset
            for node in self.nodes:
                dx = node.pos.x() - m_pos.x()
                dy = node.pos.y() - m_pos.y()
                if dx*dx + dy*dy < (node.radius * 2)**2:
                    self.selected_node = node
                    self.update()
                    return
            
            self.dragging = True
            self.last_mouse_pos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.position().toPoint() - self.last_mouse_pos
            self.offset += QPointF(delta.x(), delta.y()) / self.zoom
            self.last_mouse_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self.zoom, self.zoom)
        painter.translate(self.offset.x(), self.offset.y())
        
        # Draw Edges
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
        for edge in self.edges:
            alpha = 100 if (self.selected_node in [edge.source, edge.target]) else 30
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 1))
            painter.drawLine(edge.source.pos, edge.target.pos)
            
        # Draw Nodes
        for node in self.nodes:
            is_related = False
            if self.selected_node:
                if self.selected_node == node:
                    is_related = True
                else:
                    for edge in self.edges:
                        if (edge.source == self.selected_node and edge.target == node) or \
                           (edge.target == self.selected_node and edge.source == node):
                            is_related = True
                            break
            
            alpha = 255 if (not self.selected_node or is_related) else 50
            color = QColor(node.color)
            color.setAlpha(alpha)
            
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(node.pos, node.radius, node.radius)
            
            if is_related or (node.is_hub and self.zoom > 0.8):
                painter.setPen(QColor(255, 255, 255, alpha))
                painter.setFont(QFont("Monospace", 6))
                painter.drawText(node.pos + QPointF(node.radius + 2, 3), node.label)

class MemoryWidget(QWidget):
    command_entered = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(450, 600)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide() # Hidden by default
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 35, 15, 15) # Leave space for the top tab
        self.main_layout.setSpacing(10)
        
        # 2. Graph Area (Obsidian Style)
        self.graph_area = GraphArea()
        self.main_layout.addWidget(self.graph_area)
        
        # 3. Separator Line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: rgba(150, 100, 255, 100); height: 1px;")
        self.main_layout.addWidget(line)
        
        # 4. Input Area
        input_container = QHBoxLayout()
        self.prompt_label = QLabel("\u270E ") # Pencil icon
        self.prompt_label.setStyleSheet("color: #9d7cd8; font-size: 16px; font-family: monospace;")
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("search or append memory...")
        self.input_field.setFrame(False)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                color: #bbbbbb;
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
        self.img_btn = QLabel("[graph]")
        self.img_btn.setStyleSheet("color: #7aa2f7; font-family: monospace; font-size: 11px;")
        
        self.send_btn = QLabel("[save \u21B5]")
        self.send_btn.setStyleSheet("color: #7aa2f7; font-family: monospace; font-size: 11px;")
        
        action_layout.addWidget(self.img_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.send_btn)
        self.main_layout.addLayout(action_layout)
        
        # Initial Content
        self.refresh_memory({
            "identity": {"name": "Gopinath"},
            "notes": {"status": "Integration phase."}
        })

    def handle_input(self):
        text = self.input_field.text().strip()
        if text:
            self.add_log(f"> Querying: {text}", "command")
            self.command_entered.emit(text)
            self.input_field.clear()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.input_field.setFocus()

    def add_log(self, text, style="plain"):
        # Deprecated for Graph view
        pass

    def refresh_memory(self, memory_dict):
        self.graph_area.set_data(memory_dict)

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
        painter.setBrush(QColor(20, 30, 35, 220))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
        
        # Border: Subtle glow line
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(0, 255, 204, 50), 1))
        painter.drawPath(path)
        
        # --- Draw Top Tab (The Memory Header) ---
        tab_w = 180
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
        tab_grad.setColorAt(0, QColor(157, 124, 216, 200)) # Purple
        tab_grad.setColorAt(1, QColor(111, 76, 190, 150))
        painter.setBrush(tab_grad)
        painter.drawPath(tab_path)
        
        # Tab Text
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Monospace", 8, QFont.Weight.Bold))
        painter.drawText(QRectF(tab_x, 0, tab_w, 15), Qt.AlignmentFlag.AlignCenter, "MEMORY_VAULT_v1.0")

class SettingsWidget(QWidget):
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(350, 420)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()
        
        self.config_path = os.path.join("config", "api_keys.json")
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 40, 15, 15)
        self.main_layout.setSpacing(20)
        
        # --- Form Container ---
        form_frame = QFrame()
        form_frame.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)
        
        # 1. Gemini API Keys (Multi-line)
        self.gemini_input = self.create_multi_input_group("GEMINI_API_KEYS (one per line)", "Paste multiple keys here...")
        form_layout.addLayout(self.gemini_input["layout"])
        
        # 2. Camera Index
        self.camera_input = self.create_input_group("CAMERA_INDEX", "0")
        form_layout.addLayout(self.camera_input["layout"])
        
        # 3. Voice Selection
        self.voice_input = self.create_input_group("VOICE_NAME", "Aoede")
        form_layout.addLayout(self.voice_input["layout"])
        
        self.main_layout.addWidget(form_frame)
        self.main_layout.addStretch()
        
        # Save Button
        self.save_btn = QPushButton("EXECUTE_SAVE_SEQUENCE")
        self.save_btn.setFixedHeight(35)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9D7CD8, stop:1 #6F4CBE);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 0px;
                color: white;
                font-family: 'Monospace';
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #AF8AE2, stop:1 #805DCD);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background: #5A3A9E;
            }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        self.main_layout.addWidget(self.save_btn)
        
        # Load current data
        self.load_settings()

    def create_input_group(self, label_text, placeholder):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        label = QLabel(label_text)
        label.setStyleSheet("color: #9D7CD8; font-family: 'Monospace'; font-size: 9px; font-weight: bold;")
        
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setStyleSheet("""
            QLineEdit {
                background: rgba(20, 20, 30, 0.6);
                border: 1px solid rgba(157, 124, 216, 0.3);
                border-radius: 0px;
                padding: 8px;
                color: #FFFFFF;
                font-family: 'Monospace';
                font-size: 10px;
            }
            QLineEdit:focus {
                border: 1px solid #9D7CD8;
                background: rgba(30, 30, 45, 0.8);
            }
        """)
        
        layout.addWidget(label)
        layout.addWidget(edit)
        
        return {"layout": layout, "edit": edit}

    def create_multi_input_group(self, label_text, placeholder):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        label = QLabel(label_text)
        label.setStyleSheet("color: #9D7CD8; font-family: 'Monospace'; font-size: 9px; font-weight: bold;")
        
        edit = QTextEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(80)
        edit.setStyleSheet("""
            QTextEdit {
                background: rgba(20, 20, 30, 0.6);
                border: 1px solid rgba(157, 124, 216, 0.3);
                border-radius: 0px;
                padding: 8px;
                color: #FFFFFF;
                font-family: 'Consolas', 'Monospace';
                font-size: 10px;
            }
            QTextEdit:focus {
                border: 1px solid #9D7CD8;
                background: rgba(30, 30, 45, 0.8);
            }
        """)
        
        layout.addWidget(label)
        layout.addWidget(edit)
        
        return {"layout": layout, "edit": edit}

    def load_settings(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    # Support both old and new formats
                    keys = data.get("gemini_api_keys", [])
                    if not keys and "gemini_api_key" in data:
                        keys = [data["gemini_api_key"]]
                    
                    self.gemini_input["edit"].setText("\n".join(keys))
                    self.camera_input["edit"].setText(str(data.get("camera_index", 0)))
                    self.voice_input["edit"].setText(data.get("voice_name", "Aoede"))
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            # Validate camera index is int
            try:
                cam_idx = int(self.camera_input["edit"].text())
            except ValueError:
                cam_idx = 0
            
            # Split keys by newline and clean up
            raw_keys = self.gemini_input["edit"].toPlainText().split("\n")
            clean_keys = [k.strip() for k in raw_keys if k.strip()]
                
            data = {
                "gemini_api_keys": clean_keys,
                "camera_index": cam_idx,
                "voice_name": self.voice_input["edit"].text().strip()
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=4)
            
            print(f"[ANANYA] [OK] Saved {len(clean_keys)} keys to config/api_keys.json")
            self.settings_saved.emit()
            
            # Visual feedback on button (briefly)
            self.save_btn.setText("SAVED_SUCCESSFULLY")
            QTimer.singleShot(2000, lambda: self.save_btn.setText("EXECUTE_SAVE_SEQUENCE"))
            
        except Exception as e:
            print(f"Error saving settings: {e}")

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # --- Draw Main Panel Background ---
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 15, self.width(), self.height()-15), 10, 10)
        
        # Glassmorphism effect
        bg_color = QColor(15, 15, 25, 230)
        painter.fillPath(path, bg_color)
        
        # Border
        painter.setPen(QPen(QColor(157, 124, 216, 80), 1.5))
        painter.drawPath(path)
        
        # --- Draw Top Tab ---
        tab_w = 160
        tab_h = 22
        tab_path = QPainterPath()
        tab_x = 20
        tab_path.moveTo(tab_x, 15)
        tab_path.lineTo(tab_x + 10, 0)
        tab_path.lineTo(tab_x + tab_w - 10, 0)
        tab_path.lineTo(tab_x + tab_w, 15)
        tab_path.closeSubpath()
        
        tab_grad = QLinearGradient(QPointF(tab_x, 0), QPointF(tab_x, 15))
        tab_grad.setColorAt(0, QColor(157, 124, 216, 200))
        tab_grad.setColorAt(1, QColor(111, 76, 190, 150))
        painter.setBrush(tab_grad)
        painter.drawPath(tab_path)
        
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Monospace", 8, QFont.Weight.Bold))
        painter.drawText(QRectF(tab_x, 0, tab_w, 15), Qt.AlignmentFlag.AlignCenter, "SYSTEM_CONFIG_v1.2")

class CameraWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(480, 360)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()
        
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 45, 15, 15)
        
        self.video_label = QLabel("INITIALIZING_OPTICAL_SENSORS...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                color: #00FFCC;
                font-family: 'Monospace';
                font-weight: bold;
                font-size: 14px;
                background-color: rgba(0, 10, 20, 180);
                border: 1px solid rgba(0, 255, 204, 50);
                border-radius: 0px;
            }
        """)
        self.main_layout.addWidget(self.video_label)
        
        # Add a "Scanning" overlay effect or text
        self.status_label = QLabel("[ STATUS: OFFLINE ]")
        self.status_label.setStyleSheet("color: #FF5555; font-family: 'Monospace'; font-size: 10px;")
        self.main_layout.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignRight)

    def toggle_visibility(self):
        if self.isVisible():
            self.stop_camera()
            self.hide()
        else:
            self.show()
            self.raise_()
            self.start_camera()

    def start_camera(self):
        try:
            config_path = os.path.join("config", "api_keys.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    idx = data.get("camera_index", 0)
            else:
                idx = 0
        except:
            idx = 0
            
        try:
            import cv2
            self.cap = cv2.VideoCapture(idx)
            if self.cap.isOpened():
                self.timer.start(30)
                self.status_label.setText("[ STATUS: ONLINE_ACTIVE ]")
                self.status_label.setStyleSheet("color: #00FFCC; font-family: 'Monospace'; font-size: 10px;")
            else:
                self.video_label.setText("FAILED_TO_CONNECT_OPTICAL_HARDWARE")
        except Exception as e:
            self.video_label.setText(f"CAMERA_ERROR: {str(e)}")

    def stop_camera(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.video_label.clear()
        self.video_label.setText("OPTICAL_SENSORS_DEACTIVATED")
        self.status_label.setText("[ STATUS: OFFLINE ]")
        self.status_label.setStyleSheet("color: #FF5555; font-family: 'Monospace'; font-size: 10px;")

    def update_frame(self):
        if self.cap and self.cap.isOpened():
            import cv2
            ret, frame = self.cap.read()
            if ret:
                # Convert BGR to RGB
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
                
                # Scale pixmap to fit label
                scaled_pixmap = pixmap.scaled(
                    self.video_label.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.video_label.setPixmap(scaled_pixmap)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # --- Draw Main Panel Background ---
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 15, self.width(), self.height()-15), 10, 10)
        
        bg_color = QColor(10, 20, 30, 220)
        painter.fillPath(path, bg_color)
        
        # Border with Cyber-Cyan
        painter.setPen(QPen(QColor(0, 255, 204, 80), 1.5))
        painter.drawPath(path)
        
        # --- Draw Top Tab ---
        tab_w = 180
        tab_h = 22
        tab_path = QPainterPath()
        tab_x = 20
        tab_path.moveTo(tab_x, 15)
        tab_path.lineTo(tab_x + 10, 0)
        tab_path.lineTo(tab_x + tab_w - 10, 0)
        tab_path.lineTo(tab_x + tab_w, 15)
        tab_path.closeSubpath()
        
        tab_grad = QLinearGradient(QPointF(tab_x, 0), QPointF(tab_x, 15))
        tab_grad.setColorAt(0, QColor(0, 255, 204, 200)) # Cyan
        tab_grad.setColorAt(1, QColor(0, 200, 180, 150))
        painter.setBrush(tab_grad)
        painter.drawPath(tab_path)
        
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Monospace", 8, QFont.Weight.Bold))
        painter.drawText(QRectF(tab_x, 0, tab_w, 15), Qt.AlignmentFlag.AlignCenter, "OPTICAL_STREAM_v2.1")

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
