import pygame
import math
from enum import Enum
from typing import List, Dict, Optional
import random

# Inicjalizacja Pygame
pygame.init()

# Stałe
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Kolory
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

class UnitType(Enum):
    SOLDIER = {"speed": 2, "cost": 100, "size": 10, "color": BLUE}
    TANK = {"speed": 1.5, "cost": 300, "size": 15, "color": RED}
    PLANE = {"speed": 4, "cost": 500, "size": 12, "color": GREEN}

class Unit:
    def __init__(self, unit_type: UnitType, x: float, y: float, owner: str):
        self.type = unit_type
        self.x = x
        self.y = y
        self.target_x: Optional[float] = None
        self.target_y: Optional[float] = None
        self.owner = owner
        self.selected = False
        
    def move(self):
        if self.target_x is not None and self.target_y is not None:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < self.type.value["speed"]:
                self.x = self.target_x
                self.y = self.target_y
                self.target_x = None
                self.target_y = None
            else:
                speed = self.type.value["speed"]
                ratio = speed / distance
                self.x += dx * ratio
                self.y += dy * ratio
    
    def draw(self, screen):
        color = self.type.value["color"]
        size = self.type.value["size"]
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), size)
        if self.selected:
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 
                             size + 2, 2)

class City:
    def __init__(self, x: int, y: int, owner: str, name: str):
        self.x = x
        self.y = y
        self.owner = owner
        self.name = name
        self.population = 1000
        self.resources = 500
        self.production = 10
        
    def draw(self, screen):
        color = BLUE if self.owner == "Player" else RED
        pygame.draw.rect(screen, color, 
                        (self.x - 20, self.y - 20, 40, 40))
        # Rysowanie nazwy miasta
        font = pygame.font.Font(None, 24)
        text = font.render(self.name, True, BLACK)
        screen.blit(text, (self.x - 30, self.y + 25))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Python RTS Game")
        self.clock = pygame.time.Clock()
        
        self.units: List[Unit] = []
        self.cities: List[City] = [
            City(100, 100, "Player", "Alfa City"),
            City(600, 400, "AI", "Beta City")
        ]
        self.resources = 1000
        self.selected_unit = None
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Obsługa kliknięć na jednostki
                clicked_unit = None
                for unit in self.units:
                    distance = math.sqrt((mouse_x - unit.x)**2 + 
                                      (mouse_y - unit.y)**2)
                    if distance < unit.type.value["size"]:
                        clicked_unit = unit
                        break
                
                if clicked_unit:
                    # Zaznaczanie jednostki
                    if self.selected_unit:
                        self.selected_unit.selected = False
                    self.selected_unit = clicked_unit
                    clicked_unit.selected = True
                elif self.selected_unit:
                    # Wydawanie rozkazu ruchu
                    self.selected_unit.target_x = mouse_x
                    self.selected_unit.target_y = mouse_y
            
            # Tworzenie jednostek
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s and self.resources >= UnitType.SOLDIER.value["cost"]:
                    self.create_unit(UnitType.SOLDIER)
                elif event.key == pygame.K_t and self.resources >= UnitType.TANK.value["cost"]:
                    self.create_unit(UnitType.TANK)
                elif event.key == pygame.K_p and self.resources >= UnitType.PLANE.value["cost"]:
                    self.create_unit(UnitType.PLANE)
                    
        return True
    
    def create_unit(self, unit_type: UnitType):
        player_city = next(city for city in self.cities if city.owner == "Player")
        self.units.append(Unit(unit_type, player_city.x, player_city.y, "Player"))
        self.resources -= unit_type.value["cost"]
    
    def update(self):
        # Aktualizacja jednostek
        for unit in self.units:
            unit.move()
        
        # Aktualizacja zasobów
        for city in self.cities:
            if city.owner == "Player":
                self.resources += city.production / FPS
    
    def draw(self):
        self.screen.fill(WHITE)
        
        # Rysowanie miast
        for city in self.cities:
            city.draw(self.screen)
        
        # Rysowanie jednostek
        for unit in self.units:
            unit.draw(self.screen)
        
        # Rysowanie interfejsu
        font = pygame.font.Font(None, 36)
        resources_text = font.render(f"Resources: {int(self.resources)}", True, BLACK)
        self.screen.blit(resources_text, (10, 10))
        
        help_text = font.render("S - Soldier (100), T - Tank (300), P - Plane (500)", 
                              True, BLACK)
        self.screen.blit(help_text, (10, SCREEN_HEIGHT - 30))
        
        pygame.display.flip()
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()