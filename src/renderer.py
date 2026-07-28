import pygame
import numpy as np
import math
import random

class Renderer:
    def __init__(self, width=1200, height=800):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("3D Gravity Simulator")
        self.clock = pygame.time.Clock()
        
        # Параметры камеры
        self.camera_distance = 500
        self.rotation_x = 0.3
        self.rotation_y = 0.5
        self.zoom = 1.0
        
        self.offset = np.array([width/2, height/2])
        self.show_orbits = True
        self.running = True
        self.auto_rotate = True
        
        # Звездный фон
        self.generate_starfield()
        
        # Оптимизация: кэшируем проекции точек трейлов
        self.trail_cache = {}
    
    def generate_starfield(self, num_stars=2000):
        """Генерирует звездный фон"""
        self.stars = []
        
        layers = [
            {'count': 1500, 'spread': 3000, 'min_size': 1, 'max_size': 2, 'brightness': (50, 150)},
            {'count': 400, 'spread': 1500, 'min_size': 2, 'max_size': 4, 'brightness': (150, 230)},
            {'count': 100, 'spread': 800, 'min_size': 3, 'max_size': 6, 'brightness': (200, 255)}
        ]
        
        for layer in layers:
            for _ in range(layer['count']):
                x = random.uniform(-layer['spread'], layer['spread'])
                y = random.uniform(-layer['spread'], layer['spread'])
                z = random.uniform(-layer['spread'], layer['spread'])
                
                size = random.uniform(layer['min_size'], layer['max_size'])
                brightness = random.randint(layer['brightness'][0], layer['brightness'][1])
                
                if random.random() < 0.02:
                    color_choice = random.choice([
                        (brightness, brightness * 0.7, brightness * 0.7),
                        (brightness * 0.7, brightness * 0.8, brightness),
                        (brightness, brightness * 0.8, brightness * 0.5),
                    ])
                else:
                    color_choice = (brightness, brightness, brightness)
                
                twinkle_speed = random.uniform(0.5, 2.0)
                twinkle_offset = random.uniform(0, 2*math.pi)
                
                self.stars.append({
                    'pos': np.array([x, y, z], dtype=float),
                    'size': size,
                    'color': color_choice,
                    'base_brightness': brightness,
                    'twinkle_speed': twinkle_speed,
                    'twinkle_offset': twinkle_offset,
                    'layer': layer
                })
    
    def project_3d_to_2d(self, point_3d):
        """Проецирует 3D точку на 2D экран"""
        x, y, z = point_3d
        
        # Вращение по Y
        cos_y = math.cos(self.rotation_y)
        sin_y = math.sin(self.rotation_y)
        x1 = x * cos_y + z * sin_y
        z1 = -x * sin_y + z * cos_y
        
        # Вращение по X
        cos_x = math.cos(self.rotation_x)
        sin_x = math.sin(self.rotation_x)
        y1 = y * cos_x - z1 * sin_x
        z2 = y * sin_x + z1 * cos_x
        
        # Проекция (перспектива)
        if z2 + self.camera_distance != 0:
            scale = self.camera_distance / (z2 + self.camera_distance)
        else:
            scale = 1
        
        x2d = x1 * scale * self.zoom + self.offset[0]
        y2d = -y1 * scale * self.zoom + self.offset[1]
        
        return (int(x2d), int(y2d)), scale
    
    def draw_starfield(self, time):
        """Рисует звездный фон"""
        sorted_stars = sorted(self.stars, key=lambda s: -s['pos'][2])
        
        for star in sorted_stars:
            pos_2d, scale = self.project_3d_to_2d(star['pos'])
            
            margin = 50
            if (pos_2d[0] < -margin or pos_2d[0] > self.width + margin or
                pos_2d[1] < -margin or pos_2d[1] > self.height + margin):
                continue
            
            twinkle = 0.7 + 0.3 * math.sin(time * star['twinkle_speed'] + star['twinkle_offset'])
            brightness = int(star['base_brightness'] * twinkle)
            brightness = max(0, min(255, brightness))
            
            color = (
                min(255, int(star['color'][0] * twinkle)),
                min(255, int(star['color'][1] * twinkle)),
                min(255, int(star['color'][2] * twinkle))
            )
            
            size = max(0.5, star['size'] * scale * self.zoom)
            
            if brightness > 200 and size > 2:
                glow_size = int(size * 3)
                glow_surf = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
                for i in range(3):
                    alpha = 30 - i * 10
                    radius = glow_size - i * 5
                    pygame.draw.circle(glow_surf, (*color, alpha), (glow_size, glow_size), radius)
                self.screen.blit(glow_surf, (pos_2d[0]-glow_size, pos_2d[1]-glow_size))
            
            if size < 1:
                self.screen.set_at(pos_2d, color)
            else:
                pygame.draw.circle(self.screen, color, pos_2d, int(size))
    
    def draw_trails(self, bodies):
        """
        Рисует ВЕЧНЫЕ трейлы (следы) планет
        Оптимизация: рисуем только новые точки, старые уже нарисованы
        """
        for body in bodies:
            if body.fixed or len(body.trail) < 2:
                continue
            
            # Проецируем все точки трейла на 2D (с кэшированием для скорости)
            trail_2d = []
            for pos in body.trail:
                pos_2d, _ = self.project_3d_to_2d(pos)
                trail_2d.append(pos_2d)
            
            # Рисуем ВСЕ точки трейла (вечные следы)
            # Используем линии для плавности
            if len(trail_2d) > 1:
                # Рисуем линии между точками
                for i in range(len(trail_2d) - 1):
                    # Цвет с легким затуханием для старых точек (но они остаются!)
                    alpha = int(255 * (0.3 + 0.7 * (i / len(trail_2d))))
                    
                    # Толщина линии - тонкая для аккуратности
                    thickness = 1
                    
                    # Пропускаем некоторые линии для производительности
                    # если трейл очень длинный
                    step = 1
                    if len(trail_2d) > 1000:
                        step = 2
                    if len(trail_2d) > 5000:
                        step = 4
                    
                    if i % step == 0:
                        color = (
                            min(255, int(body.color[0] * 0.6 + 80)),
                            min(255, int(body.color[1] * 0.6 + 80)),
                            min(255, int(body.color[2] * 0.6 + 80))
                        )
                        pygame.draw.line(
                            self.screen, 
                            color, 
                            trail_2d[i], 
                            trail_2d[i+1], 
                            thickness
                        )
            
            # Рисуем яркую точку в конце трейла (текущая позиция планеты)
            if trail_2d:
                pygame.draw.circle(self.screen, body.color, trail_2d[-1], 4)
    
    def draw_glow_for_sun(self, pos, radius, time):
        """Рисует свечение Солнца"""
        pulse = 1.0 + 0.05 * math.sin(time * 0.5)
        glow_radius = int(radius * 2.5 * pulse)
        
        for i in range(5):
            alpha = 60 - i * 12
            current_radius = glow_radius - i * 15
            if current_radius > 0:
                surf = pygame.Surface((current_radius*2, current_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 200, 50, alpha), (current_radius, current_radius), current_radius)
                self.screen.blit(surf, (pos[0]-current_radius, pos[1]-current_radius))
        
        for i in range(8):
            angle = time * 0.2 + i * math.pi / 4
            length = int(glow_radius * 1.3)
            end_x = pos[0] + length * math.cos(angle)
            end_y = pos[1] + length * math.sin(angle)
            pygame.draw.line(self.screen, (255, 200, 50, 50), pos, (end_x, end_y), 2)
    
    def draw(self, bodies, time=0):
        self.screen.fill((5, 5, 20))
        
        # Рисуем звездный фон
        self.draw_starfield(time)
        
        # Рисуем ВЕЧНЫЕ трейлы (если включены)
        if self.show_orbits:
            self.draw_trails(bodies)
        
        # Сортируем тела по глубине для корректного отображения
        bodies_3d = []
        for body in bodies:
            pos_2d, scale = self.project_3d_to_2d(body.position)
            depth = body.position[2]
            bodies_3d.append((body, pos_2d, depth, scale))
        
        bodies_3d.sort(key=lambda x: x[2])
        
        # Рисуем тела
        for body, pos_2d, depth, scale in bodies_3d:
            if body.mass > 100:  # Солнце
                radius = int(body.radius * self.zoom)
                self.draw_glow_for_sun(pos_2d, radius, time)
                pygame.draw.circle(self.screen, body.color, pos_2d, radius)
                pygame.draw.circle(self.screen, (255, 255, 200), pos_2d, int(radius * 0.5))
            else:
                size = max(2, int(body.radius * scale * self.zoom))
                pygame.draw.circle(self.screen, body.color, pos_2d, size)
                
                if body.mass > 3 and size > 5:
                    glow_surf = pygame.Surface((size*3, size*3), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*body.color, 30), (size*1.5, size*1.5), size*1.5)
                    self.screen.blit(glow_surf, (pos_2d[0]-size*1.5, pos_2d[1]-size*1.5))
        
        # Информация
        font = pygame.font.Font(None, 24)
        total_trail_points = sum(len(body.trail) for body in bodies)
        info_texts = [
            f"🌟 3D Space Simulator",
            f"Zoom: {self.zoom:.1f}x",
            f"Trails: {'ON' if self.show_orbits else 'OFF'} (O)",
            f"Trail points: {total_trail_points}",
            f"Auto-rotate: {'ON' if self.auto_rotate else 'OFF'} (R)",
            f"Stars: {len(self.stars)}",
            f"C - Clear trails",
            f"ESC - exit"
        ]
        for i, text in enumerate(info_texts):
            surface = font.render(text, True, (200, 200, 200))
            text_rect = surface.get_rect()
            bg_surf = pygame.Surface((text_rect.width + 20, text_rect.height + 6), pygame.SRCALPHA)
            bg_surf.fill((0, 0, 0, 150))
            self.screen.blit(bg_surf, (5, 5 + i * 25 - 3))
            self.screen.blit(surface, (10, 10 + i * 25))
            
        pygame.display.flip()
        self.clock.tick(60)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return False
                if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    self.zoom *= 1.1
                if event.key == pygame.K_MINUS:
                    self.zoom *= 0.9
                if event.key == pygame.K_o:
                    self.show_orbits = not self.show_orbits
                if event.key == pygame.K_r:
                    self.auto_rotate = not self.auto_rotate
                if event.key == pygame.K_LEFT:
                    self.rotation_y -= 0.1
                if event.key == pygame.K_RIGHT:
                    self.rotation_y += 0.1
                if event.key == pygame.K_UP:
                    self.rotation_x -= 0.1
                if event.key == pygame.K_DOWN:
                    self.rotation_x += 0.1
                if event.key == pygame.K_c:  # Клавиша C для очистки трейлов
                    return 'clear_trails'
        
        if self.auto_rotate:
            self.rotation_y += 0.005
        
        return True
