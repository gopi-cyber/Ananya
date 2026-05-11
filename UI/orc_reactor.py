import sys
import math
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QPainterPath, QRadialGradient

class OrcReactor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.scale = 0.7
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
        self.status = "IDLE"
        self.pulse_phase = 0
        
        # Smooth Animation Variables
        self.current_c9_radius = 220 * self.scale 
        self.target_c9_radius = 220 * self.scale
        
        # Real-time Voice & Audio Amplitude Tracking
        self.audio_amplitude = 0.0
        self.target_amplitude = 0.0
        self.is_mic_active = False
        
        # Floating Neon Particles System (24 Energy Sparks)
        self.particles = []
        for i in range(24):
            angle = (i / 24.0) * math.pi * 2 + (math.sin(i) * 0.5)
            base_orbit_radius = 185 + (i % 3) * 15
            speed = 0.01 + (i % 4) * 0.005
            direction = 1 if (i % 2 == 0) else -1
            size = 2.0 + (i % 3) * 1.5
            color = QColor(0, 191, 255) if (i % 3 != 0) else QColor(255, 0, 128) # Teal/Cyan vs Pink
            self.particles.append({
                "angle": angle,
                "base_orbit": base_orbit_radius,
                "speed": speed,
                "direction": direction,
                "size": size,
                "color": color,
                "phase_offset": i * 1.3
            })
        
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
        
        # --- Smooth Radius Transitions ---
        S = self.scale
        if self.status == "LISTENING":
            self.target_c9_radius = (170 + 45) * S
        elif self.status in ["SPEAKING", "THINKING"]:
            self.target_c9_radius = 260 * S
        else: # IDLE
            self.target_c9_radius = 220 * S
            
        lerp_speed = 0.04
        self.current_c9_radius += (self.target_c9_radius - self.current_c9_radius) * lerp_speed

        # --- Smooth Audio Amplitude Decay & Decay Physics ---
        if self.target_amplitude > self.audio_amplitude:
            amplitude_lerp = 0.25 # Sharp attack
        else:
            amplitude_lerp = 0.08 # Smooth decay
        self.audio_amplitude += (self.target_amplitude - self.audio_amplitude) * amplitude_lerp

        # --- Particles Orbit Movement Update ---
        # Particles speed up significantly as voice/audio intensity increases
        particle_speed_mult = 1.0 + (self.audio_amplitude * 4.0)
        for p in self.particles:
            p["angle"] += p["speed"] * p["direction"] * particle_speed_mult

        # Always increment pulse_phase for continuous breathing
        self.pulse_phase += 0.06 if self.status != "SPEAKING" else 0.12
            
        self.update()

    def set_amplitude(self, amp, is_mic=False):
        # Clip amplitude safely between 0.0 and 1.0
        self.target_amplitude = max(0.0, min(1.0, amp))
        self.is_mic_active = is_mic
        # Force redraw
        self.update()

    def set_status(self, state):
        self.status = state
        self.update()

    def mouseDoubleClickEvent(self, event):
        # Find the DashboardUI and exit mini mode
        p = self.parent()
        while p:
            if hasattr(p, 'set_mini_mode'):
                p.set_mini_mode(False)
                break
            p = p.parent()
        super().mouseDoubleClickEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        
        # Global Scale Factor
        S = self.scale
        
        # Dynamic physical scale based on voice/audio amplitude (engine pumping effect)
        dynamic_amp_scale = 1.0 + (self.audio_amplitude * 0.15)
        
        radius = 80 * S * dynamic_amp_scale
        outer_radius = 85 * S * dynamic_amp_scale
        # --- Breathing effect (Ripple: Circle 3 to Circle 8) ---
        # "spread bigger" amplitude for C3, with propagation delay for others
        def get_pulse_radius(base_r, phase_delay, amp):
            # Scale amplitude: full for SPEAKING, prominent for others
            amp_scale = 1.0 if self.status == "SPEAKING" else 0.8
            return (base_r * S * dynamic_amp_scale) + (math.sin(self.pulse_phase - phase_delay) * (amp * S * amp_scale))

        circle3_radius = get_pulse_radius(95, 0.0, 20) # Core: highest amplitude
        circle4_radius = get_pulse_radius(115, 0.25, 14)
        circle5_radius = get_pulse_radius(125, 0.5, 10)
        circle6_radius = get_pulse_radius(135, 0.75, 7)
        circle7_radius = get_pulse_radius(147, 1.0, 5)
        circle8_radius = get_pulse_radius(170, 1.25, 3)
        
        # --- Dynamic HUD Geometry Visibility (States) ---
        if self.status == "LISTENING":
            show_cardinal = False
            rotate_9 = True
            show_c10 = True
        elif self.status == "THINKING":
            show_cardinal = True
            rotate_9 = True
            show_c10 = False
        elif self.status == "SPEAKING":
            show_cardinal = False
            rotate_9 = False
            show_c10 = False
        else: # IDLE
            show_cardinal = True
            rotate_9 = True
            show_c10 = True

        circle9_radius = self.current_c9_radius

        # Energy Fog Effect (Circle 3 to Circle 8) - Active on Speaking
        if self.status == "SPEAKING":
            painter.save()
            fog_radius = circle8_radius + 20
            fog_grad = QRadialGradient(center, fog_radius)
            # Oscillate opacity for the "fog"
            fog_alpha = int(40 + math.sin(self.pulse_phase) * 20)
            
            stop_start = circle3_radius / fog_radius
            stop_end = circle8_radius / fog_radius
            
            fog_grad.setColorAt(0, QColor(0, 102, 255, 0)) # Clear inside
            fog_grad.setColorAt(stop_start, QColor(0, 102, 255, fog_alpha)) # Blue fog starts at C3
            fog_grad.setColorAt(stop_end, QColor(0, 102, 255, 0)) # Fades out by C8
            
            painter.setBrush(fog_grad)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, int(fog_radius), int(fog_radius))
            painter.restore()
        
        # --- Circle 9 (Tactical Markers) ---
        painter.save()
        if rotate_9:
            painter.translate(center)
            painter.rotate(self.rotation_angle_9)
            painter.translate(-center)
            
        marker_len9 = 15 * S
        offset = 4 * S
        marker_pen9 = QPen(QColor(255, 255, 255), 1.5 * S)
        
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            
            if angle in [0, 90, 180, 270]:
                # Cardinal: Single Line
                if show_cardinal:
                    dim_pen = QPen(QColor(150, 150, 150), 1.5 * S)
                    painter.setPen(dim_pen)
                    x_start = center.x() + (circle9_radius - marker_len9/2) * math.cos(rad)
                    y_start = center.y() + (circle9_radius - marker_len9/2) * math.sin(rad)
                    x_end = center.x() + (circle9_radius + marker_len9/2) * math.cos(rad)
                    y_end = center.y() + (circle9_radius + marker_len9/2) * math.sin(rad)
                    painter.drawLine(int(x_start), int(y_start), int(x_end), int(y_end))
            else:
                # Diagonal: Double Line (with Glow/Brightness Effect)
                perp_rad = rad + math.pi/2
                dx = math.cos(perp_rad) * offset
                dy = math.sin(perp_rad) * offset
                
                # --- GLOW PASS for Double Lines ---
                glow_pen = QPen(QColor(255, 255, 255, 60), 3.5 * S)
                painter.setPen(glow_pen)
                for side in [-1, 1]:
                    x_start = center.x() + (circle9_radius - marker_len9/2) * math.cos(rad) + side * dx
                    y_start = center.y() + (circle9_radius - marker_len9/2) * math.sin(rad) + side * dy
                    x_end = center.x() + (circle9_radius + marker_len9/2) * math.cos(rad) + side * dx
                    y_end = center.y() + (circle9_radius + marker_len9/2) * math.sin(rad) + side * dy
                    painter.drawLine(int(x_start), int(y_start), int(x_end), int(y_end))
                
                # --- MAIN PASS (Full White) ---
                painter.setPen(marker_pen9)
                for side in [-1, 1]:
                    x_start = center.x() + (circle9_radius - marker_len9/2) * math.cos(rad) + side * dx
                    y_start = center.y() + (circle9_radius - marker_len9/2) * math.sin(rad) + side * dy
                    x_end = center.x() + (circle9_radius + marker_len9/2) * math.cos(rad) + side * dx
                    y_end = center.y() + (circle9_radius + marker_len9/2) * math.sin(rad) + side * dy
                    painter.drawLine(int(x_start), int(y_start), int(x_end), int(y_end))
        
        painter.restore()

        # Circle 10 (Outer-most, Sensor Array)
        if show_c10:
            painter.save()
            painter.translate(center)
            # In IDLE, if we want dots to match C9 rotating double lines, they must share rotation
            if self.status == "IDLE":
                painter.rotate(self.rotation_angle_9)
            else:
                painter.rotate(self.rotation_angle_10)
            painter.translate(-center)
            
            marker_pen10 = QPen(QColor(150, 150, 150), 1.5 * S)
            painter.setPen(marker_pen10)
            dot_size10 = 2 * S
            circle10_radius = 240 * S
            
            for angle in [45, 135, 225, 315]:
                rad = math.radians(angle)
                # Draw only 1 dot at each diagonal
                dot_radius = circle10_radius
                px = center.x() + dot_radius * math.cos(rad)
                py = center.y() + dot_radius * math.sin(rad)
                painter.setBrush(QColor(150, 150, 150))
                painter.drawEllipse(QPointF(px, py), dot_size10/2, dot_size10/2)
            painter.restore()
        
        # Circle 8 (Outer-most, Dotted)
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle_8)
        painter.translate(-center)
        
        dot_pen = QPen(QColor(200, 200, 200), 2 * S)
        dot_pen.setStyle(Qt.PenStyle.CustomDashLine)
        dot_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        # Scale dash pattern
        dash_len = (17.18 * S)
        dot_pen.setDashPattern([0.01, dash_len]) 
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
        marker_pen = QPen(QColor(200, 200, 200), 2 * S)
        painter.setPen(marker_pen)
        marker_len = 5 * S
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
        
        path7 = QPainterPath()
        start_angle7 = -60
        span_angle7 = -30
        thickness7 = 4 * S
        
        path7.arcMoveTo(center.x() - circle7_radius, center.y() - circle7_radius, circle7_radius * 2, circle7_radius * 2, start_angle7)
        path7.arcTo(center.x() - circle7_radius, center.y() - circle7_radius, circle7_radius * 2, circle7_radius * 2, start_angle7, span_angle7)
        
        inner_r7 = circle7_radius - thickness7
        path7.arcTo(center.x() - inner_r7, center.y() - inner_r7, inner_r7 * 2, inner_r7 * 2, start_angle7 + span_angle7 - 5, - (span_angle7 - 10))
        path7.closeSubpath()

        # Main Path
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawPath(path7)
        painter.restore()
        
        # Circle 6 (Outer-most, White, 1/4 arc)
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle_6)
        painter.translate(-center)
        
        painter.setPen(QPen(QColor(80, 80, 80), 2 * S))
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
        
        painter.setPen(QPen(QColor(180, 180, 180), 2 * S))
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
        
        painter.setPen(QPen(QColor(80, 80, 80), 2 * S))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(int(center.x() - circle4_radius), int(center.y() - circle4_radius), 
                        int(circle4_radius * 2), int(circle4_radius * 2), 
                        0, 90 * 16)
        painter.restore()
        
        # Circle 3 (Electric Core Glow)
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle_3)
        painter.translate(-center)
        
        # Create a radial gradient for the "core line" effect
        # We target the area around circle3_radius (95)
        grad3 = QRadialGradient(center, circle3_radius + 4)
        # Navy fade-in
        grad3.setColorAt((circle3_radius - 4) / (circle3_radius + 4), QColor(0, 0, 51, 50)) 
        # Electric Blue
        grad3.setColorAt((circle3_radius - 2) / (circle3_radius + 4), QColor(0, 102, 255))
        # Bright Core
        grad3.setColorAt(circle3_radius / (circle3_radius + 4), QColor(255, 255, 255))
        # Electric Blue
        grad3.setColorAt((circle3_radius + 2) / (circle3_radius + 4), QColor(0, 102, 255))
        # Navy fade-out
        grad3.setColorAt(1.0, QColor(0, 0, 51, 50))
        
        c3_pen = QPen(grad3, 6 * S) # Thicker to show the gradient
        painter.setPen(c3_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, circle3_radius, circle3_radius)
        painter.restore()
        
        # Circle 2 (outer) - Quarter arc with diagonal "blade" cuts
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle)
        painter.translate(-center)
        
        outer_path = QPainterPath()
        start_angle = -90
        end_angle = -60
        thickness = 5 * S
        
        # Outer Arc
        outer_path.arcMoveTo(center.x() - outer_radius, center.y() - outer_radius, outer_radius * 2, outer_radius * 2, start_angle)
        outer_path.arcTo(center.x() - outer_radius, center.y() - outer_radius, outer_radius * 2, outer_radius * 2, start_angle, end_angle)
        
        # Diagonal cut at the end (tip)
        inner_r = outer_radius - thickness
        outer_path.arcTo(center.x() - inner_r, center.y() - inner_r, inner_r * 2, inner_r * 2, start_angle + end_angle - 5, - (end_angle - 10))
        outer_path.closeSubpath()

        # Main Path
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawPath(outer_path)
        painter.restore()
        
        # --- Orbiting Neon Particles System ---
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for p in self.particles:
            # Particle orbital radius expands with audio amplitude and breathing
            pulse = math.sin(self.pulse_phase + p["phase_offset"]) * 5 * S
            amp_expansion = self.audio_amplitude * 35 * S
            orbit_r = (p["base_orbit"] * S) + pulse + amp_expansion
            
            px = center.x() + orbit_r * math.cos(p["angle"])
            py = center.y() + orbit_r * math.sin(p["angle"])
            
            alpha = int(120 + self.audio_amplitude * 135)
            alpha = max(50, min(255, alpha))
            
            p_color = QColor(p["color"])
            p_color.setAlpha(alpha)
            
            # Ambient Particle Glow
            glow_color = QColor(p_color)
            glow_color.setAlpha(int(alpha * 0.35))
            painter.setBrush(glow_color)
            painter.setPen(Qt.PenStyle.NoPen)
            glow_size = p["size"] * 2.8 * S
            painter.drawEllipse(QPointF(px, py), glow_size, glow_size)
            
            # Particle Core
            painter.setBrush(p_color)
            painter.setPen(Qt.PenStyle.NoPen)
            p_size = p["size"] * S
            painter.drawEllipse(QPointF(px, py), p_size, p_size)
        painter.restore()

        # --- Radial Soundwave Spectrum Visualizer (Equalizer Spikes) ---
        if self.audio_amplitude > 0.01:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Pink/magenta if mic is active, blue/cyan if speakers are active
            base_color = QColor(255, 0, 128) if self.is_mic_active else QColor(0, 191, 255)
            
            for i in range(48):
                angle = (i / 48.0) * 360.0
                rad = math.radians(angle)
                
                # Frequency/Fourier-like simulation wave
                wave = abs(math.sin(i * 0.3 + self.pulse_phase * 3) * 0.4 + 
                           math.sin(i * 0.8) * 0.4 + 
                           math.cos(i * 1.5) * 0.2)
                
                start_r = circle8_radius
                end_r = circle8_radius + (self.audio_amplitude * 55 * S * wave)
                
                sx = center.x() + start_r * math.cos(rad)
                sy = center.y() + start_r * math.sin(rad)
                
                ex = center.x() + end_r * math.cos(rad)
                ey = center.y() + end_r * math.sin(rad)
                
                # 1. Glow Line
                glow_pen = QPen(base_color, 3.5 * S)
                glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                glow_color = QColor(base_color)
                glow_color.setAlpha(int(40 + self.audio_amplitude * 110))
                glow_pen.setColor(glow_color)
                painter.setPen(glow_pen)
                painter.drawLine(QPointF(sx, sy), QPointF(ex, ey))
                
                # 2. Main Sharp Core
                sharp_pen = QPen(QColor(255, 255, 255), 1.2 * S)
                sharp_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(sharp_pen)
                painter.drawLine(QPointF(sx, sy), QPointF(ex, ey))
                
            painter.restore()
        
        # Circle 1 (inner)
        painter.setPen(QPen(Qt.GlobalColor.white, 3 * S))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius, radius)

        # Draw "ANANYA" Text
        font_size = int(18 * S)
        font = QFont("Inter", font_size) # Clean sans-serif
        if not font.exactMatch(): font = QFont("Arial", font_size) # Fallback
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, int(6 * S)) # Futuristic spacing
        painter.setFont(font)
        
        # Center text precisely
        metrics = painter.fontMetrics()
        text = "ANANYA"
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.ascent()
        
        tx = int(center.x() - text_width / 2)
        ty = int(center.y() + text_height / 3)

        # Main Text
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(tx, ty, text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OrcReactor()
    window.resize(600, 600)
    window.setStyleSheet("background-color: #010409;")
    window.show()
    sys.exit(app.exec())
