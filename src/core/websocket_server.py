"""
WebSocket server to connect the frontend UI to the Zentrax voice/gesture control backend.
Run this alongside main.py to enable web UI control.
"""

import asyncio
import websockets
import json
import threading
import sys
import os

# Optional psutil for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

# Add project root to path to import main
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

try:
    from main import VoiceGestureControl
except ImportError as e:
    print(f"Warning: Could not import VoiceGestureControl from main.py: {e}")
    print("WebSocket server will run in standalone mode")
    VoiceGestureControl = None


class ZentraxWebSocketServer:
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.controller = None
        self.controller_thread = None
        
    async def register(self, websocket):
        """Register a new client connection"""
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        
        # Determine initial status safely
        is_awake = False
        mode = None
        if self.controller:
            is_awake = getattr(self.controller, 'is_awake', False)
            mode = getattr(self.controller, 'active_mode', None)
        
        # Send initial status
        await self.send_to_client(websocket, {
            'type': 'status',
            'status': 'awake' if is_awake else 'sleeping',
            'mode': mode
        })
        
        # Send welcome message
        await self.send_to_client(websocket, {
            'type': 'log',
            'message': 'Connected to Zentrax WebSocket server',
            'level': 'success'
        })
        
    async def unregister(self, websocket):
        """Unregister a disconnected client"""
        self.clients.discard(websocket)
        print(f"Client disconnected. Total clients: {len(self.clients)}")
        
    async def send_to_client(self, websocket, message):
        """Send message to a specific client"""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending to client: {e}")
            
    async def broadcast(self, message):
        """Broadcast message to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[self.send_to_client(client, message) for client in self.clients],
                return_exceptions=True
            )
            
    async def handle_client(self, websocket):
        """Handle incoming client connections and messages"""
        await self.register(websocket)
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_command(data)
                except json.JSONDecodeError:
                    await self.send_to_client(websocket, {
                        'type': 'error',
                        'message': 'Invalid JSON format'
                    })
                except Exception as e:
                    await self.send_to_client(websocket, {
                        'type': 'error',
                        'message': str(e)
                    })
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
            
    async def handle_command(self, data):
        """Process commands from frontend"""
        command = data.get('command')
        params = data.get('params', {})
        
        print(f"Received command: {command}, params: {params}")
        
        # Send acknowledgment for all commands
        await self.broadcast({
            'type': 'response',
            'command': command,
            'status': 'received'
        })
        
        if command == 'wake':
            await self.broadcast({
                'type': 'log',
                'message': 'Starting Zentrax...',
                'level': 'info'
            })
            
            # Try to start the controller if not running
            if not self.controller or not getattr(self.controller, 'running', False):
                started = self.start_controller()
                if not started and VoiceGestureControl is None:
                    # Running in standalone mode without backend
                    await self.broadcast({
                        'type': 'log',
                        'message': 'Running in standalone UI mode (backend not available)',
                        'level': 'warning'
                    })
            
            if self.controller:
                self.controller.is_awake = True
                self.controller.active_mode = 'voice'
            
            # Always send awake status to UI
            await self.broadcast({
                'type': 'status',
                'status': 'awake',
                'mode': 'voice'
            })
            await self.broadcast({
                'type': 'log',
                'message': 'Zentrax is now awake in voice mode',
                'level': 'success'
            })
                
        elif command == 'sleep':
            if self.controller:
                self.controller.is_awake = False
            await self.broadcast({
                'type': 'status',
                'status': 'sleeping',
                'mode': None
            })
            await self.broadcast({
                'type': 'log',
                'message': 'Zentrax is going to sleep',
                'level': 'info'
            })
                
        elif command == 'switch_mode':
            mode = params.get('mode')
            if self.controller:
                if getattr(self.controller, 'is_awake', False):
                    self.controller.active_mode = mode
                    await self.broadcast({
                        'type': 'status',
                        'status': 'awake',
                        'mode': mode
                    })
                    await self.broadcast({
                        'type': 'log',
                        'message': f'Switched to {mode} mode',
                        'level': 'success'
                    })
                else:
                    await self.broadcast({
                        'type': 'log',
                        'message': 'Zentrax must be awake to switch modes',
                        'level': 'warning'
                    })
            else:
                # UI-only mode - still allow mode switching for display
                await self.broadcast({
                    'type': 'status',
                    'status': 'awake',
                    'mode': mode
                })
                await self.broadcast({
                    'type': 'log',
                    'message': f'Switched to {mode} mode (UI only)',
                    'level': 'info'
                })
                
        elif command == 'start_game':
            if self.controller and getattr(self.controller, 'is_awake', False):
                try:
                    self.controller.start_hill_climb()
                    await self.broadcast({
                        'type': 'log',
                        'message': 'Hill Climb game started',
                        'level': 'success'
                    })
                except Exception as e:
                    await self.broadcast({
                        'type': 'log',
                        'message': f'Failed to start game: {str(e)}',
                        'level': 'error'
                    })
            else:
                await self.broadcast({
                    'type': 'log',
                    'message': 'Zentrax must be awake to start the game',
                    'level': 'warning'
                })
                
        elif command == 'stop':
            if self.controller:
                self.controller.running = False
                self.controller.is_awake = False
            await self.broadcast({
                'type': 'status',
                'status': 'sleeping',
                'mode': None
            })
            await self.broadcast({
                'type': 'log',
                'message': 'Zentrax stopped',
                'level': 'info'
            })
        
        elif command == 'execute':
            # Execute a voice command from UI
            cmd = params.get('command', '')
            if cmd:
                await self.broadcast({
                    'type': 'log',
                    'message': f'Executing: {cmd}',
                    'level': 'info'
                })
                if self.controller and hasattr(self.controller, '_handle_recognized_text'):
                    try:
                        self.controller._handle_recognized_text(cmd.lower())
                        await self.broadcast({
                            'type': 'log',
                            'message': f'Command executed: {cmd}',
                            'level': 'success'
                        })
                    except Exception as e:
                        await self.broadcast({
                            'type': 'log',
                            'message': f'Error executing command: {str(e)}',
                            'level': 'error'
                        })
        
        elif command == 'get_status':
            # Return current status
            is_awake = self.controller.is_awake if self.controller else False
            mode = getattr(self.controller, 'active_mode', None) if self.controller else None
            await self.broadcast({
                'type': 'status',
                'status': 'awake' if is_awake else 'sleeping',
                'mode': mode
            })
        
        else:
            await self.broadcast({
                'type': 'log',
                'message': f'Unknown command: {command}',
                'level': 'warning'
            })
                
    def start_controller(self):
        """Start the VoiceGestureControl in a separate thread"""
        if VoiceGestureControl is None:
            print("Warning: VoiceGestureControl not available, running in standalone mode")
            return False
            
        if not self.controller or not self.controller.running:
            try:
                print("Starting VoiceGestureControl...")
                self.controller = VoiceGestureControl(use_whisper=True, whisper_model="base")
                self.controller.is_awake = False
                self.controller.running = True
                self.controller_thread = threading.Thread(
                    target=self.controller.run,
                    daemon=True
                )
                self.controller_thread.start()
                print("VoiceGestureControl started")
                return True
            except Exception as e:
                print(f"Error starting VoiceGestureControl: {e}")
                return False
        return True
    
    async def send_system_info(self):
        """Send system info to all connected clients periodically."""
        if not PSUTIL_AVAILABLE:
            # Send default values when psutil is not available
            await self.broadcast({
                'type': 'system_info',
                'battery': 100,
                'cpu': 0,
                'ram': 0,
                'disk': 0
            })
            return
            
        try:
            # Get system stats
            battery = psutil.sensors_battery()
            battery_percent = battery.percent if battery else 100
            
            cpu_percent = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory()
            
            # Use C: drive on Windows, / on other systems
            try:
                disk = psutil.disk_usage('C:/' if sys.platform == 'win32' else '/')
            except Exception:
                disk = None
            
            await self.broadcast({
                'type': 'system_info',
                'battery': battery_percent,
                'cpu': cpu_percent,
                'ram': ram.percent,
                'disk': disk.percent if disk else 0
            })
        except Exception as e:
            print(f"Error getting system info: {e}")
    
    async def system_info_loop(self):
        """Background task to send system info every 5 seconds."""
        while True:
            await self.send_system_info()
            await asyncio.sleep(5)
            
    async def start(self):
        """Start the WebSocket server"""
        print(f"Starting Zentrax WebSocket Server on {self.host}:{self.port}")
        print("Open frontend/index.html in your browser to access the UI")
        
        # Start system info broadcast task
        asyncio.create_task(self.system_info_loop())
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever


def main():
    """Main entry point"""
    server = ZentraxWebSocketServer(host='localhost', port=8765)
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nShutting down server...")
        if server.controller:
            server.controller.running = False
        print("Server stopped")


if __name__ == "__main__":
    main()
