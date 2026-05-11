import json
import socket
import threading
from core.logging import LOG


class UnrealEngineRelay:
    def __init__(self, host="0.0.0.0", port=8080):
        self.host = host
        self.port = port
        self.clients = []
        self.clients_lock = threading.Lock()
        self.server_socket = None
        self.running = False
        self._logger = LOG.get_logger("UERelay")

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self._logger.info(f"TCP Socket Server started on {self.host}:{self.port}")
            threading.Thread(target=self._accept_clients, daemon=True).start()
        except Exception as e:
            self._logger.error(f"Failed to start TCP server: {e}")

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        with self.clients_lock:
            for c in self.clients:
                try:
                    c.close()
                except Exception:
                    pass
            self.clients.clear()

    def _accept_clients(self):
        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                self._logger.info(f"Client connected from {addr}")
                with self.clients_lock:
                    self.clients.append(client_sock)
                self.send_to_client(client_sock, {"event": "handshake", "status": "connected"})
            except Exception as e:
                if self.running:
                    self._logger.error(f"Error accepting clients: {e}")
                break

    def broadcast(self, data_dict):
        with self.clients_lock:
            if not self.clients:
                return
            try:
                message = (json.dumps(data_dict) + "\n").encode("utf-8")
            except Exception as e:
                self._logger.error(f"Serialization error: {e}")
                return

            inactive = []
            for client in self.clients:
                try:
                    client.sendall(message)
                except Exception:
                    inactive.append(client)

            for client in inactive:
                try:
                    client.close()
                except Exception:
                    pass
                if client in self.clients:
                    self.clients.remove(client)

    def send_to_client(self, client_sock, data_dict):
        try:
            message = (json.dumps(data_dict) + "\n").encode("utf-8")
            client_sock.sendall(message)
        except Exception:
            pass
