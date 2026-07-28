import numpy as np
from body import Body

class Simulation:
    def __init__(self, bodies, G=1.0, dt=0.01):
        self.bodies = bodies
        self.G = G
        self.dt = dt
        self.time_scale = 1.0
        
        # Находим Солнце
        self.sun = None
        for body in bodies:
            if body.fixed or body.mass > 100:
                self.sun = body
                break
        
        # Вычисляем начальные ускорения
        self.compute_accelerations()
    
    def compute_accelerations(self, bodies=None):
        """
        Расчет ускорений от ВСЕХ тел (N-body гравитация)
        """
        if bodies is None:
            bodies = self.bodies
        
        n = len(bodies)
        
        # Сбрасываем ускорения
        for body in bodies:
            if not body.fixed:
                body.acceleration = np.array([0.0, 0.0, 0.0], dtype=float)
        
        # Для каждой пары тел считаем гравитацию
        for i in range(n):
            for j in range(i + 1, n):
                body1 = bodies[i]
                body2 = bodies[j]
                
                if body1.fixed and body2.fixed:
                    continue
                
                diff = body2.position - body1.position
                dist = np.linalg.norm(diff)
                
                if dist < 0.001:
                    continue
                
                force_mag = self.G / (dist * dist)
                direction = diff / dist
                
                if not body1.fixed:
                    body1.acceleration += force_mag * body2.mass * direction
                
                if not body2.fixed:
                    body2.acceleration -= force_mag * body1.mass * direction
    
    def get_state(self, bodies=None):
        """Получает текущее состояние системы (позиции и скорости)"""
        if bodies is None:
            bodies = self.bodies
        
        positions = np.array([body.position.copy() for body in bodies])
        velocities = np.array([body.velocity.copy() for body in bodies])
        return positions, velocities
    
    def set_state(self, positions, velocities, bodies=None):
        """Устанавливает состояние системы"""
        if bodies is None:
            bodies = self.bodies
        
        for i, body in enumerate(bodies):
            if not body.fixed:
                body.position = positions[i].copy()
                body.velocity = velocities[i].copy()
    
    def derivatives(self, positions, velocities, bodies=None):
        """
        Вычисляет производные (dy/dt) для RK4
        """
        if bodies is None:
            bodies = self.bodies
        
        # Создаем временные копии тел с новыми позициями
        temp_bodies = []
        for i, body in enumerate(bodies):
            temp_body = Body(
                mass=body.mass,
                position=positions[i],
                velocity=velocities[i],
                radius=body.radius,
                color=body.color,
                fixed=body.fixed
            )
            temp_bodies.append(temp_body)
        
        # Вычисляем ускорения для временных тел
        self.compute_accelerations(temp_bodies)
        
        # Собираем производные
        dpos = np.array([body.velocity.copy() for body in temp_bodies])
        dvel = np.array([body.acceleration.copy() for body in temp_bodies])
        
        return dpos, dvel
    
    def update_trails(self):
        """
        Обновляет трейлы (следы) для тел
        Следы оставляют ТОЛЬКО планеты (масса > 0.1)
        Астероиды (масса <= 0.01) НЕ оставляют следы
        """
        for body in self.bodies:
            # Оставляем следы только для планет (масса > 0.1)
            # Астероиды (масса 0.01) - пропускаем
            if not body.fixed and body.mass > 0.1:
                body.trail.append(body.position.copy())
    
    def step(self):
        """
        Шаг симуляции методом Рунге-Кутты 4-го порядка
        """
        dt = self.dt * self.time_scale
        bodies = self.bodies
        
        # Получаем текущее состояние
        pos, vel = self.get_state(bodies)
        
        # k1
        dpos1, dvel1 = self.derivatives(pos, vel, bodies)
        
        # k2
        pos2 = pos + 0.5 * dt * dpos1
        vel2 = vel + 0.5 * dt * dvel1
        dpos2, dvel2 = self.derivatives(pos2, vel2, bodies)
        
        # k3
        pos3 = pos + 0.5 * dt * dpos2
        vel3 = vel + 0.5 * dt * dvel2
        dpos3, dvel3 = self.derivatives(pos3, vel3, bodies)
        
        # k4
        pos4 = pos + dt * dpos3
        vel4 = vel + dt * dvel3
        dpos4, dvel4 = self.derivatives(pos4, vel4, bodies)
        
        # Обновляем состояние (усредняем производные)
        new_pos = pos + (dt / 6.0) * (dpos1 + 2*dpos2 + 2*dpos3 + dpos4)
        new_vel = vel + (dt / 6.0) * (dvel1 + 2*dvel2 + 2*dvel3 + dvel4)
        
        # Применяем новые позиции и скорости
        for i, body in enumerate(bodies):
            if not body.fixed:
                body.position = new_pos[i].copy()
                body.velocity = new_vel[i].copy()
        
        # Пересчитываем ускорения для нового состояния
        self.compute_accelerations(bodies)
        
        # Обновляем трейлы (только для планет)
        self.update_trails()
    
    def step_euler(self):
        """Метод Эйлера (для сравнения)"""
        dt = self.dt * self.time_scale
        
        for body in self.bodies:
            if not body.fixed:
                body.velocity += body.acceleration * dt
        
        for body in self.bodies:
            if not body.fixed:
                body.position += body.velocity * dt
        
        self.compute_accelerations()
        self.update_trails()
    
    def add_perturbation(self, body_index, force):
        """Добавляет возмущение к телу"""
        if body_index < len(self.bodies):
            self.bodies[body_index].velocity += force / self.bodies[body_index].mass
    
    def get_total_energy(self):
        """Вычисляет полную механическую энергию системы"""
        kinetic = 0
        potential = 0
        
        for body in self.bodies:
            if not body.fixed:
                kinetic += 0.5 * body.mass * np.dot(body.velocity, body.velocity)
        
        n = len(self.bodies)
        for i in range(n):
            for j in range(i + 1, n):
                body1 = self.bodies[i]
                body2 = self.bodies[j]
                if body1.fixed and body2.fixed:
                    continue
                diff = body2.position - body1.position
                dist = np.linalg.norm(diff)
                if dist > 0.001:
                    potential -= self.G * body1.mass * body2.mass / dist
        
        return kinetic + potential
    
    def clear_trails(self):
        """Очищает все трейлы"""
        for body in self.bodies:
            body.trail = []
