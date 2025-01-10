import pygame
import math
import random
from enum import Enum
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

pygame.init()

# Stałe
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 700
FPS = 60

# Kolory
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)

# Stałe hexów
HEX_SIZE = 40
HEX_WIDTH = HEX_SIZE * 2
HEX_HEIGHT = math.sqrt(3) * HEX_SIZE
GRID_WIDTH = 20
GRID_HEIGHT = 15

class TerrainType(Enum):
    GRASS = {"color": GREEN, "movement_cost": 1}
    MOUNTAIN = {"color": GRAY, "movement_cost": 2}
    WATER = {"color": (0, 100, 255), "movement_cost": 3}
    FOREST = {"color": (0, 100, 0), "movement_cost": 2}

class BuildingType(Enum):
    CITY = {"cost": 500, "income": 50, "defense": 2}
    FACTORY = {"cost": 300, "income": 30, "production_bonus": 1.5}
    FORT = {"cost": 200, "income": 0, "defense": 3}
    MINE = {"cost": 400, "income": 40, "resource_bonus": 1.5}

class UnitType(Enum):
    SOLDIER = {"speed": 2, "cost": 100, "attack": 1, "defense": 1, "range": 1}
    TANK = {"speed": 3, "cost": 300, "attack": 3, "defense": 2, "range": 1}
    PLANE = {"speed": 4, "cost": 500, "attack": 2, "defense": 1, "range": 2}
    ARTILLERY = {"speed": 1, "cost": 400, "attack": 4, "defense": 1, "range": 3}

@dataclass
class Hex:
    q: int  # hex coordinates
    r: int
    terrain: TerrainType
    building: Optional[BuildingType] = None
    unit: Optional['Unit'] = None
    owner: Optional[str] = None

    def pixel_position(self) -> Tuple[float, float]:
        x = HEX_SIZE * (3/2 * self.q)
        y = HEX_SIZE * (math.sqrt(3)/2 * self.q + math.sqrt(3) * self.r)
        return (x + SCREEN_WIDTH/4, y + SCREEN_HEIGHT/4)

    def __hash__(self):
        return hash((self.q, self.r))  # Make Hex hashable using q and r coordinates

    def __eq__(self, other):
        return isinstance(other, Hex) and self.q == other.q and self.r == other.r  # Compare based on coordinates

class Unit:
    def __init__(self, unit_type: UnitType, owner: str):
        self.type = unit_type
        self.owner = owner
        self.moved_this_turn = False
        self.health = 100
        
    def can_move_to(self, start_hex: Hex, target_hex: Hex) -> bool:
        if target_hex.unit is not None:
            return False
        distance = hex_distance(start_hex, target_hex)
        return (distance <= self.type.value["speed"] and 
                not self.moved_this_turn)

def hex_distance(start: Hex, target: Hex) -> int:
    return max(abs(start.q - target.q), abs(start.r - target.r), 
               abs((start.q + start.r) - (target.q + target.r)))

class Player:
    def __init__(self, name: str, color: Tuple[int, int, int]):
        self.name = name
        self.color = color
        self.money = 1000
        self.income = 100
        self.units: List[Unit] = []
        self.buildings: List[Tuple[BuildingType, Hex]] = []

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Hex Strategy Game")
        self.clock = pygame.time.Clock()
        
        self.players = [
            Player("Player", BLUE),
            Player("AI 1", RED),
            Player("AI 2", GREEN),
            Player("AI 3", YELLOW)
        ]
        self.current_player_index = 0
        self.selected_hex = None
        self.possible_moves = set()
        self.turn_number = 1
        
        self.init_map()
        self.init_starting_positions()
        
    def init_map(self):
        self.hexes = {}
        for q in range(-GRID_WIDTH//2, GRID_WIDTH//2):
            for r in range(-GRID_HEIGHT//2, GRID_HEIGHT//2):
                if abs(q + r) <= GRID_WIDTH//2:
                    terrain = random.choice(list(TerrainType))
                    self.hexes[(q, r)] = Hex(q, r, terrain)

    def init_starting_positions(self):
        # Przydziel początkowe miasta i jednostki dla graczy
        starting_positions = [
            (-5, -5), (5, 5), (5, -5), (-5, 5)
        ]
        
        for i, pos in enumerate(starting_positions):
            if i < len(self.players):
                hex = self.hexes.get(pos)
                if hex:
                    hex.building = BuildingType.CITY
                    hex.owner = self.players[i].name
                    # Dodaj początkowe jednostki
                    hex.unit = Unit(UnitType.SOLDIER, self.players[i].name)
                    self.players[i].units.append(hex.unit)
                    self.players[i].buildings.append((BuildingType.CITY, hex))

    def get_hex_at_pixel(self, x: float, y: float) -> Optional[Hex]:
        for hex in self.hexes.values():
            hx, hy = hex.pixel_position()
            if math.sqrt((x - hx)**2 + (y - hy)**2) < HEX_SIZE:
                return hex
        return None

    def draw_hex(self, hex: Hex):
        x, y = hex.pixel_position()
        points = []
        for i in range(6):
            angle = i * math.pi / 3
            points.append((x + HEX_SIZE * math.cos(angle), y + HEX_SIZE * math.sin(angle)))
        
        # Rysuj teren
        pygame.draw.polygon(self.screen, hex.terrain.value["color"], points)
        pygame.draw.polygon(self.screen, BLACK, points, 1)
        
        # Rysuj budynek
        if hex.building:
            pygame.draw.circle(self.screen, 
                             self.get_player_by_name(hex.owner).color if hex.owner else BLACK,
                             (int(x), int(y)), HEX_SIZE//2)
        
        # Rysuj jednostkę
        if hex.unit:
            unit_color = self.get_player_by_name(hex.unit.owner).color
            unit_radius = HEX_SIZE//3
            pygame.draw.circle(self.screen, unit_color, 
                             (int(x), int(y) + HEX_SIZE//3), unit_radius)
            
            # Rysuj pasek życia
            health_width = (HEX_SIZE//2) * (hex.unit.health / 100)
            pygame.draw.rect(self.screen, RED, 
                           (x - HEX_SIZE//4, y + HEX_SIZE//2, 
                            HEX_SIZE//2, 4))
            pygame.draw.rect(self.screen, GREEN,
                           (x - HEX_SIZE//4, y + HEX_SIZE//2, 
                            health_width, 4))

        # Podświetl możliwe ruchy
        if hex in self.possible_moves:
            pygame.draw.polygon(self.screen, (255, 255, 0, 128), points, 2)

    def draw_interface(self):
        # Rysuj górny panel
        pygame.draw.rect(self.screen, GRAY, (0, 0, SCREEN_WIDTH, 50))
        
        # Informacje o obecnym graczu
        current_player = self.players[self.current_player_index]
        font = pygame.font.Font(None, 36)
        
        # Tura i gracz
        turn_text = font.render(f"Turn: {self.turn_number}", True, WHITE)
        player_text = font.render(f"Player: {current_player.name}", True, 
                                current_player.color)
        money_text = font.render(f"Money: {current_player.money}", True, WHITE)
        income_text = font.render(f"Income: {current_player.income}", True, WHITE)
        
        self.screen.blit(turn_text, (10, 10))
        self.screen.blit(player_text, (200, 10))
        self.screen.blit(money_text, (400, 10))
        self.screen.blit(income_text, (600, 10))
        
        # Przycisk końca tury
        end_turn_rect = pygame.draw.rect(self.screen, GREEN, 
                                       (SCREEN_WIDTH - 120, 10, 100, 30))
        end_turn_text = font.render("End Turn", True, BLACK)
        self.screen.blit(end_turn_text, (SCREEN_WIDTH - 110, 15))

    def get_player_by_name(self, name: str) -> Optional[Player]:
        return next((p for p in self.players if p.name == name), None)

    def handle_click(self, x: float, y: float):
        hex = self.get_hex_at_pixel(x, y)
        if hex:
            if hex.unit and hex.unit.owner == self.players[self.current_player_index].name:
                self.selected_hex = hex
                self.possible_moves = self.calculate_possible_moves(hex)
            elif self.selected_hex:
                if hex in self.possible_moves:
                    self.move_unit(self.selected_hex, hex)
                    self.selected_hex = None
                    self.possible_moves = set()

    def calculate_possible_moves(self, hex: Hex) -> set:
        moves = set()
        for q in range(hex.q - 1, hex.q + 2):
            for r in range(hex.r - 1, hex.r + 2):
                target_hex = self.hexes.get((q, r))
                if target_hex and hex_distance(hex, target_hex) <= 1:
                    moves.add(target_hex)
        return moves

    def move_unit(self, from_hex: Hex, to_hex: Hex):
        if to_hex.unit is None:
            to_hex.unit = from_hex.unit
            from_hex.unit = None
            self.players[self.current_player_index].units.append(to_hex.unit)

    def next_turn(self):
        self.turn_number += 1
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        for player in self.players:
            player.money += player.income  # Zarobki co turę
        self.selected_hex = None
        self.possible_moves = set()

    def run(self):
        running = True
        while running:
            self.screen.fill(WHITE)

            # Rysowanie mapy
            for hex in self.hexes.values():
                self.draw_hex(hex)

            # Rysowanie interfejsu
            self.draw_interface()
            
            # Obsługuje zdarzenia
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_click(event.pos[0], event.pos[1])
                    elif event.button == 3:  # Kliknięcie prawym przyciskiem na kończenie tury
                        self.next_turn()
            
            pygame.display.flip()
            self.clock.tick(FPS)

# Uruchomienie gry
game = Game()
game.run()

pygame.quit()
