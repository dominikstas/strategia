import pygame
import math
import random
from enum import Enum
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from camera import Camera

# Game constants
WINDOW_MIN_SIZE = (800, 600)
HEX_SIZE = 40
# Define colors - Updated to match the player IDs
COLORS = {
    'EMPTY': (255, 255, 255),    # White
    0: (0, 0, 255),      # Blue - Player
    1: (255, 0, 0),      # Red - Bot 1
    2: (0, 255, 0),      # Green - Bot 2
    3: (255, 255, 0),    # Yellow - Bot 3
}
@dataclass
class BuildingStats:
    cost: int
    income: int
    defense_bonus: int

@dataclass
class UnitStats:
    cost: int
    attack: int
    defense: int
    movement: int
    range: int

class BuildingType(Enum):
    CAPITAL = "Capital"
    BARRACKS = "Barracks"
    RESEARCH_LAB = "Research Lab"
    FACTORY = "Factory"
    MINE = "Mine"

BUILDING_DATA = {
    BuildingType.CAPITAL: BuildingStats(cost=500, income=50, defense_bonus=5),
    BuildingType.BARRACKS: BuildingStats(cost=200, income=0, defense_bonus=2),
    BuildingType.RESEARCH_LAB: BuildingStats(cost=300, income=20, defense_bonus=0),
    BuildingType.FACTORY: BuildingStats(cost=400, income=30, defense_bonus=1),
    BuildingType.MINE: BuildingStats(cost=250, income=40, defense_bonus=0)
}

class UnitType(Enum):
    INFANTRY = "Infantry"
    TANK = "Tank"
    ARTILLERY = "Artillery"
    AIRCRAFT = "Aircraft"

UNIT_DATA = {
    UnitType.INFANTRY: UnitStats(cost=100, attack=5, defense=3, movement=2, range=1),
    UnitType.TANK: UnitStats(cost=300, attack=10, defense=7, movement=3, range=1),
    UnitType.ARTILLERY: UnitStats(cost=250, attack=8, defense=2, movement=1, range=3),
    UnitType.AIRCRAFT: UnitStats(cost=400, attack=12, defense=4, movement=4, range=2)
}

class Building:
    def __init__(self, building_type: BuildingType, owner: int, position: Tuple[int, int]):
        self.type = building_type
        stats = BUILDING_DATA[building_type]
        self.cost = stats.cost
        self.income = stats.income
        self.defense_bonus = stats.defense_bonus
        self.position = position
        self.owner = owner
        self.health = 100
        self.level = 1

class Unit:
    def __init__(self, unit_type: UnitType, owner: int):
        self.type = unit_type
        stats = UNIT_DATA[unit_type]
        self.cost = stats.cost
        self.attack = stats.attack
        self.defense = stats.defense
        self.movement = stats.movement
        self.range = stats.range
        self.health = 100
        self.moves_left = stats.movement
        self.owner = owner
        self.has_attacked = False

    def reset_turn(self):
        self.moves_left = self.movement
        self.has_attacked = False

    def can_attack(self, target: 'Unit', distance: int) -> bool:
        return (not self.has_attacked and 
                distance <= self.range and 
                target.owner != self.owner)

class Player:
    def __init__(self, id: int, is_bot: bool = False):
        self.id = id
        self.is_bot = is_bot
        self.gold = 1000
        self.income = 100
        self.buildings: List[Building] = []
        self.units: List[Unit] = []

    def can_afford(self, cost: int) -> bool:
        return self.gold >= cost

    def add_unit(self, unit_type: UnitType) -> Optional[Unit]:
        if self.can_afford(UNIT_DATA[unit_type].cost):
            unit = Unit(unit_type, self.id)
            self.gold -= unit.cost
            self.units.append(unit)
            return unit
        return None

    def add_building(self, building_type: BuildingType, position: Tuple[int, int]) -> Optional[Building]:
        if self.can_afford(BUILDING_DATA[building_type].cost):
            building = Building(building_type, self.id, position)
            self.gold -= building.cost
            self.buildings.append(building)
            self.income += building.income
            return building
        return None

class HexTile:
    def __init__(self, q: int, r: int):
        self.q = q
        self.r = r
        self.owner = None
        self.unit: Optional[Unit] = None
        self.building: Optional[Building] = None
        self.terrain_type = random.choice(["plain", "forest", "mountain", "water"])
        self.defense_bonus = {"plain": 0, "forest": 2, "mountain": 4, "water": -1}[self.terrain_type]

    def get_defense_bonus(self) -> int:
        total_bonus = self.defense_bonus
        if self.building:
            total_bonus += self.building.defense_bonus
        return total_bonus

class Game:
    def __init__(self, screen_size: Tuple[int, int]):
        pygame.init()
        self.screen = pygame.display.set_mode(screen_size, pygame.RESIZABLE)
        pygame.display.set_caption("Hex Strategy Game")
        self.clock = pygame.time.Clock()
        
        # Initialize camera
        self.camera = Camera(screen_size[0], screen_size[1])
        
        # Initialize game state
        self.grid = self._create_initial_grid()
        self.players = [
            Player(0, is_bot=False),  # Player
            Player(1, is_bot=True),   # Bot 1
            Player(2, is_bot=True),   # Bot 2
            Player(3, is_bot=True)    # Bot 3
        ]
        self._setup_initial_positions()
        
        self.current_player = 0
        self.selected_tile: Optional[Tuple[int, int]] = None
        self.possible_moves: List[Tuple[int, int]] = []
        self.running = True
        self.turn = 1
    
    def handle_click(self, pos: Tuple[int, int]):
        # Convert screen coordinates to world coordinates for hex grid
        world_pos = self.camera.screen_to_world(*pos)
        hex_pos = self.pixel_to_hex(world_pos)
        
        if hex_pos in self.grid:
            tile = self.grid[hex_pos]
            if tile.owner == self.current_player:
                if self.selected_tile == hex_pos:
                    self.selected_tile = None
                    self.possible_moves = []
                else:
                    self.selected_tile = hex_pos
                    self.possible_moves = self.get_possible_moves(hex_pos)
            elif self.selected_tile and hex_pos in self.possible_moves:
                self.move_unit(self.selected_tile, hex_pos)
    
    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        q, r = pos
        return [(q+1, r), (q-1, r), (q, r+1), (q, r-1), (q+1, r-1), (q-1, r+1)]
    
    def get_possible_moves(self, start: Tuple[int, int]) -> List[Tuple[int, int]]:
        tile = self.grid[start]
        moves = []
        visited = set()
        queue = [(start, 0)]
        
        while queue:
            pos, moves_left = queue.pop(0)
            if moves_left == 0:
                continue
            for neighbor in self.get_neighbors(pos):
                if (neighbor in self.grid and 
                    neighbor not in visited and 
                    self.grid[neighbor].terrain_type != "water"):
                    visited.add(neighbor)
                    moves.append(neighbor)
                    queue.append((neighbor, moves_left - 1))
        
        return moves

    def _create_initial_grid(self) -> Dict[Tuple[int, int], HexTile]:
        grid = {}
        radius = 10
        for q in range(-radius, radius + 1):
            r1 = max(-radius, -q - radius)
            r2 = min(radius, -q + radius)
            for r in range(r1, r2 + 1):
                grid[(q, r)] = HexTile(q, r)
        return grid

    def _setup_initial_positions(self):
        # Assign initial territories and capitals
        starting_positions = [(-8, -8), (8, 8), (8, -8), (-8, 8)]
        for i, pos in enumerate(starting_positions):
            if pos in self.grid:
                tile = self.grid[pos]
                tile.owner = i
                tile.building = Building(BuildingType.CAPITAL, i, pos)
                self.players[i].buildings.append(tile.building)
                # Add initial unit
                unit = Unit(UnitType.INFANTRY, i)
                tile.unit = unit
                self.players[i].units.append(unit)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Convert screen coordinates to world coordinates for hex grid
                    mouse_x, mouse_y = event.pos
                    world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
                    self.handle_click((world_x, world_y))
                elif event.button == 2:  # Middle mouse button
                    self.camera.start_drag(*event.pos)
                elif event.button == 4:  # Mouse wheel up
                    self.camera.handle_mouse_wheel(0.1)
                elif event.button == 5:  # Mouse wheel down
                    self.camera.handle_mouse_wheel(-0.1)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:  # Middle mouse button
                    self.camera.stop_drag()
            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[1]:  # Middle mouse button
                    self.camera.update_drag(*event.pos)
            elif event.type == pygame.VIDEORESIZE:
                self.camera.width = event.w
                self.camera.height = event.h
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.end_turn()

    def _draw_grid(self):
        for q, r in self.grid:
            # Calculate base hex position
            x = HEX_SIZE * (3/2 * q)
            y = HEX_SIZE * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
            
            # Convert to screen coordinates using camera
            screen_x, screen_y = self.camera.world_to_screen(x, y)
            
            # Calculate hex points
            points = []
            hex_size = HEX_SIZE * self.camera.zoom
            for i in range(6):
                angle_rad = math.pi / 180 * (60 * i - 30)
                px = screen_x + hex_size * math.cos(angle_rad)
                py = screen_y + hex_size * math.sin(angle_rad)
                points.append((px, py))
            
            # Check if hex is visible on screen before drawing
            screen_rect = pygame.Rect(0, 0, self.camera.width, self.camera.height)
            hex_rect = pygame.Rect(
                min(p[0] for p in points),
                min(p[1] for p in points),
                max(p[0] for p in points) - min(p[0] for p in points),
                max(p[1] for p in points) - min(p[1] for p in points)
            )
            
            if screen_rect.colliderect(hex_rect):
                # Draw hex
                tile = self.grid[(q, r)]
                color = COLORS['EMPTY'] if tile.owner is None else COLORS[tile.owner]
                pygame.draw.polygon(self.screen, color, points, 0)
                pygame.draw.polygon(self.screen, (0, 0, 0), points, 1)
                
                # Draw unit or building with scaled size
                if tile.unit:
                    unit_color = COLORS[tile.unit.owner]
                    pygame.draw.circle(self.screen, unit_color, 
                                    (screen_x, screen_y), 
                                    (HEX_SIZE // 3) * self.camera.zoom)
                elif tile.building:
                    building_color = COLORS[tile.building.owner]
                    building_size = (HEX_SIZE // 2) * self.camera.zoom
                    pygame.draw.rect(self.screen, building_color, 
                                  (screen_x - building_size/2, 
                                   screen_y - building_size/2,
                                   building_size, building_size))

    def pixel_to_hex(self, pos: Tuple[float, float]) -> Tuple[int, int]:
        x, y = pos
        # Convert to hex grid coordinates
        q = (2/3 * x) / HEX_SIZE
        r = (-1/3 * x + math.sqrt(3)/3 * y) / HEX_SIZE
        return self._round_hex(q, r)
    def _round_hex(self, q: float, r: float) -> Tuple[int, int]:
        s = -q - r
        q = round(q)
        r = round(r)
        s = round(s)
        
        q_diff = abs(q - q)
        r_diff = abs(r - r)
        s_diff = abs(s - s)
        
        if q_diff > r_diff and q_diff > s_diff:
            q = -r - s
        elif r_diff > s_diff:
            r = -q - s
            
        return (q, r)

    def hex_distance(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        return (abs(a[0] - b[0]) + 
                abs(a[0] + a[1] - b[0] - b[1]) + 
                abs(a[1] - b[1])) // 2

    def run_bot_turn(self, bot: Player):
        # Basic AI logic
        # 1. Collect resources
        bot.gold += bot.income
        
        # 2. Build if possible
        self._bot_build(bot)
        
        # 3. Create units
        self._bot_create_units(bot)
        
        # 4. Move units
        self._bot_move_units(bot)
        
        # End turn
        self.end_turn()

    def _bot_build(self, bot: Player):
        if bot.gold >= 300:
            # Find empty tile next to owned territory
            for q, r in self.grid:
                tile = self.grid[(q, r)]
                if (tile.owner == bot.id and 
                    not tile.building and 
                    tile.terrain_type != "water"):
                    # Choose random building
                    building_type = random.choice(list(BuildingType))
                    if bot.can_afford(BUILDING_DATA[building_type].cost):
                        bot.add_building(building_type, (q, r))
                        tile.building = bot.buildings[-1]
                        break

    def _bot_create_units(self, bot: Player):
        if bot.gold >= 200:
            unit_type = random.choice(list(UnitType))
            if bot.can_afford(UNIT_DATA[unit_type].cost):
                # Find an empty tile next to a barracks or capital
                for building in bot.buildings:
                    if building.type in [BuildingType.BARRACKS, BuildingType.CAPITAL]:
                        for neighbor in self.get_neighbors(building.position):
                            if neighbor in self.grid and not self.grid[neighbor].unit:
                                new_unit = bot.add_unit(unit_type)
                                if new_unit:
                                    self.grid[neighbor].unit = new_unit
                                    return

    def _bot_move_units(self, bot: Player):
        for unit in bot.units:
            if unit.moves_left > 0:
                # Find the nearest enemy unit or building
                target = self._find_nearest_enemy(unit, bot)
                if target:
                    path = self._find_path(unit.position, target, unit.moves_left)
                    if path:
                        # Move towards the target
                        new_pos = path[-1]
                        old_pos = unit.position
                        self.grid[new_pos].unit = unit
                        self.grid[old_pos].unit = None
                        unit.position = new_pos
                        unit.moves_left = 0
                        
                        # Attack if in range
                        if self.hex_distance(new_pos, target) <= unit.range:
                            target_tile = self.grid[target]
                            if target_tile.unit:
                                self.resolve_combat(unit, target_tile.unit, target_tile)
                            elif target_tile.building:
                                self._attack_building(unit, target_tile.building)

    def _find_nearest_enemy(self, unit: Unit, bot: Player) -> Optional[Tuple[int, int]]:
        min_distance = float('inf')
        nearest_enemy = None
        for q, r in self.grid:
            tile = self.grid[(q, r)]
            if tile.owner != bot.id and (tile.unit or tile.building):
                distance = self.hex_distance(unit.position, (q, r))
                if distance < min_distance:
                    min_distance = distance
                    nearest_enemy = (q, r)
        return nearest_enemy

    def _find_path(self, start: Tuple[int, int], end: Tuple[int, int], max_moves: int) -> List[Tuple[int, int]]:
        queue = [(start, [start])]
        visited = set()
        
        while queue:
            (q, r), path = queue.pop(0)
            if len(path) > max_moves:
                continue
            if (q, r) == end:
                return path
            
            for next_pos in self.get_neighbors((q, r)):
                if next_pos not in visited and self.grid[next_pos].terrain_type != "water":
                    visited.add(next_pos)
                    new_path = path + [next_pos]
                    queue.append((next_pos, new_path))
        
        return []

    def _attack_building(self, unit: Unit, building: Building):
        damage = unit.attack * (unit.health / 100)
        building.health -= damage
        if building.health <= 0:
            tile = self.grid[building.position]
            tile.building = None
            self.players[building.owner].buildings.remove(building)
            if building.type == BuildingType.CAPITAL:
                self._eliminate_player(building.owner)

    def _eliminate_player(self, player_id: int):
        eliminated_player = self.players[player_id]
        for building in eliminated_player.buildings:
            tile = self.grid[building.position]
            tile.building = None
            tile.owner = None
        for unit in eliminated_player.units:
            tile = self.grid[unit.position]
            tile.unit = None
        self.players[player_id] = None

    def draw(self):
        self.screen.fill((255, 255, 255))
        self._draw_grid()
        pygame.display.flip()

    def _draw_grid(self):
        for q, r in self.grid:
            x = HEX_SIZE * (3/2 * q)
            y = HEX_SIZE * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
        
        # Offset to screen center
            center_x = self.screen.get_width() // 2
            center_y = self.screen.get_height() // 2
        
            points = []
            for i in range(6):
                angle_rad = math.pi / 180 * (60 * i - 30)
                px = x + HEX_SIZE * math.cos(angle_rad)
                py = y + HEX_SIZE * math.sin(angle_rad)
                points.append((px + center_x, py + center_y))
        
        # Draw hex
            tile = self.grid[(q, r)]
            color = COLORS['EMPTY'] if tile.owner is None else COLORS[tile.owner]
            pygame.draw.polygon(self.screen, color, points, 0)
            pygame.draw.polygon(self.screen, (0, 0, 0), points, 1)
        
        # Draw unit or building
            if tile.unit:
                unit_color = COLORS[tile.unit.owner]
                pygame.draw.circle(self.screen, unit_color, (center_x + x, center_y + y), HEX_SIZE // 3)
            elif tile.building:
                building_color = COLORS[tile.building.owner]
                pygame.draw.rect(self.screen, building_color, (center_x + x - HEX_SIZE // 4, center_y + y - HEX_SIZE // 4, HEX_SIZE // 2, HEX_SIZE // 2))

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            
            # Turn logic
            current = self.players[self.current_player]
            if current and current.is_bot:
                self.run_bot_turn(current)
            
            self.clock.tick(60)  # 60 FPS

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.end_turn()

    def end_turn(self):
        self.current_player = (self.current_player + 1) % len(self.players)
        while self.players[self.current_player] is None:
            self.current_player = (self.current_player + 1) % len(self.players)
        
        self.turn += 1
        for player in self.players:
            if player:
                player.gold += player.income
                for unit in player.units:
                    unit.reset_turn()

if __name__ == "__main__":
    game = Game(WINDOW_MIN_SIZE)
    game.run()