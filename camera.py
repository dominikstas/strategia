class Camera:
    def __init__(self, width: int, height: int):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.zoom = 1.0
        self.drag_start = None
        self.min_zoom = 0.5
        self.max_zoom = 2.0
        
    def handle_mouse_wheel(self, y: int):
        """Handle mouse wheel scrolling for zooming"""
        zoom_speed = 0.1
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom + y * zoom_speed))
        
    def start_drag(self, x: int, y: int):
        """Start camera dragging from the given position"""
        self.drag_start = (x - self.x, y - self.y)
        
    def stop_drag(self):
        """Stop camera dragging"""
        self.drag_start = None
        
    def update_drag(self, x: int, y: int):
        """Update camera position while dragging"""
        if self.drag_start:
            self.x = x - self.drag_start[0]
            self.y = y - self.drag_start[1]
    
    def get_offset(self) -> tuple[float, float]:
        """Get current camera offset"""
        return self.x + self.width / 2, self.y + self.height / 2
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple[float, float]:
        """Convert screen coordinates to world coordinates"""
        offset_x, offset_y = self.get_offset()
        world_x = (screen_x - offset_x) / self.zoom
        world_y = (screen_y - offset_y) / self.zoom
        return world_x, world_y
    
    def world_to_screen(self, world_x: float, world_y: float) -> tuple[float, float]:
        """Convert world coordinates to screen coordinates"""
        offset_x, offset_y = self.get_offset()
        screen_x = world_x * self.zoom + offset_x
        screen_y = world_y * self.zoom + offset_y
        return screen_x, screen_y