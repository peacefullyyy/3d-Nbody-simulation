import pygame
import sys
from body import Body
from simulation import Simulation
from renderer import Renderer
import numpy as np
import math
import time

# === КОНСТАНТЫ ===
G = 1.0
SUN_MASS = 1000.0

# === СОЗДАНИЕ ТЕЛ ===
sun = Body(
    mass=SUN_MASS,
    position=[0, 0, 0],
    velocity=[0, 0, 0],
    radius=25,
    color=(255, 220, 50),
    fixed=True
)

def orbital_speed(radius):
    return math.sqrt(G * SUN_MASS / radius)

# Планеты (без max_trail_length)
venus = Body(
    mass=0.8,
    position=[80, 0, 0],
    velocity=[0, 0, orbital_speed(80)],
    radius=7,
    color=(255, 200, 100)
)

earth = Body(
    mass=1.0,
    position=[120, 0, 0],
    velocity=[0, 0, orbital_speed(120)],
    radius=8,
    color=(50, 150, 255)
)

mars = Body(
    mass=0.5,
    position=[170, 0, 0],
    velocity=[0, 0, orbital_speed(170) * 0.99],
    radius=7,
    color=(255, 80, 50)
)

jupiter = Body(
    mass=2.5,
    position=[230, 0, 0],
    velocity=[0, 0, orbital_speed(230)],
    radius=15,
    color=(200, 180, 100)
)

# Несколько астероидов для красоты (с вечными следами)
asteroids = []
for i in range(20):
    angle = np.random.uniform(0, 2 * math.pi)
    radius = np.random.uniform(195, 205)
    mass = 0.01
    size = 2
    color = (150, 150, 150)
    
    speed = math.sqrt(G * SUN_MASS / radius)
    
    asteroid = Body(
        mass=mass,
        position=[radius * math.cos(angle), 0, radius * math.sin(angle)],
        velocity=[-speed * math.sin(angle), 0, speed * math.cos(angle)],
        radius=size,
        color=color,
        fixed=False
    )
    asteroids.append(asteroid)

bodies = [sun, venus, earth, mars, jupiter] + asteroids

# === ЗАПУСК ===
sim = Simulation(bodies, G=G, dt=0.005)
renderer = Renderer(1200, 800)

print("🌌 3D N-BODY СИМУЛЯЦИЯ С ВЕЧНЫМИ ТРЕЙЛАМИ")
print("Управление:")
print("  ← → ↑ ↓ - Вращать камеру")
print("  + / - - Зум")
print("  R - Автовращение камеры")
print("  O - Показать/скрыть трейлы")
print("  C - Очистить трейлы (начать заново)")
print("  [ / ] - Ускорять/замедлять время")
print("  Space - Пауза")
print("  ESC - Выход")

clock = pygame.time.Clock()
running = True
start_time = time.time()
paused = False

while running:
    # Обработка событий
    event_result = renderer.handle_events()
    if event_result == 'clear_trails':
        sim.clear_trails()
        print("🧹 ВСЕ трейлы очищены! Орбиты начинаются заново.")
    if event_result == False:
        running = False
        break
    
    # Обработка клавиш
    keys = pygame.key.get_pressed()
    if keys[pygame.K_SPACE]:
        paused = not paused
        pygame.time.wait(200)
        print(f"{'⏸ Пауза' if paused else '▶ Продолжаем'}")
    
    if keys[pygame.K_LEFTBRACKET]:
        sim.time_scale *= 0.9
        pygame.time.wait(100)
        print(f"⏱ Время: {sim.time_scale:.2f}x")
    if keys[pygame.K_RIGHTBRACKET]:
        sim.time_scale *= 1.1
        pygame.time.wait(100)
        print(f"⏱ Время: {sim.time_scale:.2f}x")
    
    if not paused:
        for _ in range(3):
            sim.step()
    
    current_time = time.time() - start_time
    renderer.draw(bodies, current_time)
    clock.tick(60)

pygame.quit()
sys.exit()
