import pygame
import sys
import random
import math
import json
import os

# Инициализация Pygame
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("super fighters")

# Цвета
BACKGROUND = (40, 44, 52)
GRID_COLOR = (60, 64, 72)
RED = (231, 76, 60)
BLUE = (52, 152, 219)
GREEN = (46, 204, 113)
YELLOW = (241, 196, 15)
PURPLE = (155, 89, 182)
ORANGE = (230, 126, 34)
CYAN = (26, 188, 156)  # Для Гения
WHITE = (236, 240, 241)
BLACK = (30, 30, 30)
GRAY = (120, 120, 120)
LIGHT_BLUE = (100, 200, 255)

# Файл для сохранения статистики
STATS_FILE = "brawl_stats.json"

# Класс для управления статистикой
class GameStats:
    def __init__(self):
        self.stats = self.load_stats()
        
    def load_stats(self):
        """Загружает статистику из файла"""
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.create_default_stats()
        return self.create_default_stats()
    
    def create_default_stats(self):
        """Создает статистику по умолчанию"""
        return {
            "total_kills": 0,
            "games_played": 0,
            "best_score": 0,
            "unlocked_genius": False,
            "genius_unlock_progress": 0,
            "class_stats": {
                "1": {"kills": 0, "games": 0},
                "2": {"kills": 0, "games": 0},
                "3": {"kills": 0, "games": 0},
                "4": {"kills": 0, "games": 0}  # Для Гения
            }
        }
    
    def save_stats(self):
        """Сохраняет статистику в файл"""
        try:
            with open(STATS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except:
            print("Ошибка сохранения статистики")
    
    def add_kills(self, kills, player_type):
        """Добавляет убийства в статистику"""
        self.stats["total_kills"] += kills
        self.stats["games_played"] += 1
        self.stats["best_score"] = max(self.stats["best_score"], kills)
        
        # Обновляем прогресс разблокировки Гения
        if not self.stats["unlocked_genius"]:
            self.stats["genius_unlock_progress"] += kills
            if self.stats["genius_unlock_progress"] >= 10:
                self.stats["unlocked_genius"] = True
        
        # Обновляем статистику по классам
        class_key = str(player_type)
        if class_key in self.stats["class_stats"]:
            self.stats["class_stats"][class_key]["kills"] += kills
            self.stats["class_stats"][class_key]["games"] += 1
        else:
            self.stats["class_stats"][class_key] = {"kills": kills, "games": 1}
        
        self.save_stats()
    
    def get_unlock_progress(self):
        """Возвращает прогресс разблокировки Гения"""
        if self.stats["unlocked_genius"]:
            return 100
        return min(100, int((self.stats["genius_unlock_progress"] / 10) * 100))
    
    def reset_stats(self):
        """Сбрасывает статистику"""
        self.stats = self.create_default_stats()
        self.save_stats()

# Глобальный объект статистики
stats = GameStats()

# Класс игрока
class Player:
    def __init__(self, x, y, color, player_type=0):
        self.x = x
        self.y = y
        self.color = color
        self.player_type = player_type  # 0 - игрок, 1-3 - боты разных типов, 4 - Гений
        self.radius = 25
        self.speed = 4
        self.health = 100
        self.max_health = 100
        self.direction = 0  # угол в радианах
        self.cooldown = 0
        self.cooldown_max = 20  # задержка между выстрелами
        self.bullets = []
        self.special_cooldown = 0
        self.special_cooldown_max = 100  # задержка для спец-атаки
        
        # Уникальные характеристики для разных типов
        if player_type == 1:  # Стрелок
            self.speed = 5
            self.cooldown_max = 15
            self.bullet_speed = 8
            self.bullet_damage = 10
            self.bullet_color = YELLOW
            self.bullet_radius = 6
            self.name = "Стрелок"
            
        elif player_type == 2:  # Танк
            self.radius = 32
            self.speed = 3
            self.health = 150
            self.max_health = 150
            self.cooldown_max = 30
            self.bullet_speed = 6
            self.bullet_damage = 20
            self.bullet_color = ORANGE
            self.bullet_radius = 10
            self.name = "Танк"
            
        elif player_type == 3:  # Маг
            self.speed = 4
            self.cooldown_max = 25
            self.bullet_speed = 7
            self.bullet_damage = 15
            self.bullet_color = PURPLE
            self.bullet_radius = 8
            self.name = "Маг"
            
        elif player_type == 4:  # Гений
            self.speed = 4
            self.cooldown_max = 20
            self.bullet_speed = 6
            self.bullet_damage = 12
            self.bullet_color = CYAN
            self.bullet_radius = 7
            self.name = "Гений"
            self.max_mines = 3
            self.max_turrets = 2
            self.turret_cooldown = 0
            self.mine_cooldown = 0
            self.mines = []  # Мины для Гения
            self.turrets = []  # Турели для Гения
            
        else:  # Игрок (выбирает тип при старте)
            self.speed = 4
            self.cooldown_max = 20
            self.bullet_speed = 7
            self.bullet_damage = 12
            self.bullet_color = BLUE
            self.bullet_radius = 7
            self.name = "Игрок"
    
    def draw(self, surface):
        # Тело игрока
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        
        # Уникальный вид для Гения
        if self.player_type == 4:
            # Очки
            glasses_width = self.radius * 1.5
            glasses_height = self.radius // 2
            pygame.draw.rect(surface, BLACK, 
                            (self.x - glasses_width//2, self.y - self.radius//3, 
                             glasses_width, glasses_height), 2)
            # Линзы очков
            pygame.draw.circle(surface, LIGHT_BLUE, 
                             (int(self.x - glasses_width//4), int(self.y - self.radius//6)), 
                             self.radius//4)
            pygame.draw.circle(surface, LIGHT_BLUE, 
                             (int(self.x + glasses_width//4), int(self.y - self.radius//6)), 
                             self.radius//4)
        else:
            # Глаза для обычных персонажей
            eye_x = self.x + math.cos(self.direction) * (self.radius * 0.6)
            eye_y = self.y + math.sin(self.direction) * (self.radius * 0.6)
            pygame.draw.circle(surface, WHITE, (int(eye_x), int(eye_y)), self.radius // 4)
            
            # Зрачок
            pupil_x = eye_x + math.cos(self.direction) * (self.radius // 8)
            pupil_y = eye_y + math.sin(self.direction) * (self.radius // 8)
            pygame.draw.circle(surface, BLACK, (int(pupil_x), int(pupil_y)), self.radius // 8)
        
        # Полоска здоровья
        health_width = 50
        health_height = 6
        health_x = self.x - health_width // 2
        health_y = self.y - self.radius - 15
        
        # Фон полоски здоровья
        pygame.draw.rect(surface, BLACK, (health_x, health_y, health_width, health_height))
        
        # Сама полоска здоровья
        health_ratio = self.health / self.max_health
        health_color = GREEN if health_ratio > 0.5 else YELLOW if health_ratio > 0.25 else RED
        pygame.draw.rect(surface, health_color, 
                        (health_x, health_y, int(health_width * health_ratio), health_height))
        
        # Имя или тип
        font = pygame.font.SysFont(None, 20)
        name_text = font.render(self.name, True, WHITE)
        surface.blit(name_text, (self.x - name_text.get_width() // 2, self.y + self.radius + 5))
    
    def move(self, dx, dy, obstacles):
        # Рассчитываем новую позицию
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed
        
        # Проверка границ экрана (не даём выйти за пределы)
        new_x = max(self.radius, min(new_x, WIDTH - self.radius))
        new_y = max(self.radius, min(new_y, HEIGHT - self.radius))
        
        # Проверка столкновений с препятствиями
        collision_occurred = False
        for obstacle in obstacles:
            if self.check_collision(obstacle, new_x, new_y):
                collision_occurred = True
                
                # Проверяем движение по отдельным осям
                # Движение только по X
                test_x = self.x + dx * self.speed
                test_y = self.y
                if not self.check_collision(obstacle, test_x, test_y):
                    # Корректируем только X
                    new_x = test_x
                    new_y = self.y
                
                # Движение только по Y
                test_x = self.x
                test_y = self.y + dy * self.speed
                if not self.check_collision(obstacle, test_x, test_y):
                    # Корректируем только Y
                    new_x = self.x
                    new_y = test_y
                
                # Если оба движения вызывают столкновение, остаёмся на месте
                if self.check_collision(obstacle, test_x, self.y) and self.check_collision(obstacle, self.x, test_y):
                    return
        
        # Если столкновений нет или мы их обошли, обновляем позицию
        if not collision_occurred:
            self.x = new_x
            self.y = new_y
        else:
            # Применяем скорректированные позиции
            self.x = max(self.radius, min(new_x, WIDTH - self.radius))
            self.y = max(self.radius, min(new_y, HEIGHT - self.radius))
    
    def check_collision(self, obstacle, x, y):
        # Упрощенная проверка столкновения с прямоугольным препятствием
        closest_x = max(obstacle.x, min(x, obstacle.x + obstacle.width))
        closest_y = max(obstacle.y, min(y, obstacle.y + obstacle.height))
        
        distance = math.sqrt((x - closest_x) ** 2 + (y - closest_y) ** 2)
        return distance < self.radius
    
    def update_direction(self, mouse_pos):
        self.direction = math.atan2(mouse_pos[1] - self.y, mouse_pos[0] - self.x)
    
    def shoot(self):
        if self.cooldown <= 0:
            if self.player_type == 4:  # Гений - умная пуля с наведением
                # Находим ближайшего бота для наведения
                closest_target = None
                min_distance = 500  # Максимальная дальность наведения
                
                # В реальной игре здесь бы искали ближайшего бота
                # Для простоты стреляем обычной пулей
                self.bullets.append(Bullet(
                    self.x, self.y, 
                    math.cos(self.direction) * self.bullet_speed,
                    math.sin(self.direction) * self.bullet_speed,
                    self.bullet_damage, self.bullet_color, self.bullet_radius
                ))
            else:
                # Обычные персонажи
                self.bullets.append(Bullet(
                    self.x, self.y, 
                    math.cos(self.direction) * self.bullet_speed,
                    math.sin(self.direction) * self.bullet_speed,
                    self.bullet_damage, self.bullet_color, self.bullet_radius
                ))
            
            self.cooldown = self.cooldown_max
    
    def special_attack(self):
        if self.special_cooldown <= 0:
            if self.player_type == 1:  # Стрелок - тройной выстрел
                for angle_offset in [-0.2, 0, 0.2]:
                    angle = self.direction + angle_offset
                    self.bullets.append(Bullet(
                        self.x, self.y, 
                        math.cos(angle) * self.bullet_speed * 1.5,
                        math.sin(angle) * self.bullet_speed * 1.5,
                        self.bullet_damage * 0.7, YELLOW, self.bullet_radius
                    ))
                    
            elif self.player_type == 2:  # Танк - ударная волна
                for i in range(8):
                    angle = (math.pi * 2 / 8) * i
                    self.bullets.append(Bullet(
                        self.x, self.y, 
                        math.cos(angle) * 5,
                        math.sin(angle) * 5,
                        self.bullet_damage * 0.5, ORANGE, 15
                    ))
                    
            elif self.player_type == 3:  # Маг - вращающиеся снаряды
                for i in range(3):
                    angle = self.direction + (math.pi * 2 / 3) * i
                    self.bullets.append(SpinningBullet(
                        self.x, self.y, 
                        math.cos(angle) * 4,
                        math.sin(angle) * 4,
                        self.bullet_damage, PURPLE, self.bullet_radius,
                        self.x, self.y  # центр вращения
                    ))
            
            elif self.player_type == 4:  # Гений - турель
                if len(self.turrets) < self.max_turrets:
                    self.turrets.append(Turret(
                        self.x, self.y,
                        self.bullet_damage * 0.8, CYAN
                    ))
            
            self.special_cooldown = self.special_cooldown_max
    
    def place_mine(self):
        """Размещает мину (для Гения)"""
        if self.player_type == 4 and len(self.mines) < self.max_mines and self.mine_cooldown <= 0:
            self.mines.append(Mine(self.x, self.y, self.bullet_damage * 1.5, CYAN))
            self.mine_cooldown = 30
    
    def update(self, obstacles, bots=None):
        # Обновление перезарядки
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.special_cooldown > 0:
            self.special_cooldown -= 1
        
        # Обновление перезарядки мин и турелей (только для Гения)
        if self.player_type == 4:
            if self.mine_cooldown > 0:
                self.mine_cooldown -= 1
            if self.turret_cooldown > 0:
                self.turret_cooldown -= 1
            
            # Обновление турелей
            if bots:
                for turret in self.turrets:
                    turret.update(bots)
            
            # Обновление мин
            for mine in self.mines:
                mine.update()
        
        # Обновление пуль
        for bullet in self.bullets[:]:
            bullet.update()
            # Удаление пуль за пределами экрана
            if (bullet.x < -bullet.radius or bullet.x > WIDTH + bullet.radius or
                bullet.y < -bullet.radius or bullet.y > HEIGHT + bullet.radius):
                self.bullets.remove(bullet)
    
    def draw_bullets(self, surface):
        for bullet in self.bullets:
            bullet.draw(surface)
        
        # Отрисовка мин и турелей (только для Гения)
        if self.player_type == 4:
            for mine in self.mines:
                mine.draw(surface)
            for turret in self.turrets:
                turret.draw(surface)

# Класс турели для Гения
class Turret:
    def __init__(self, x, y, damage, color):
        self.x = x
        self.y = y
        self.damage = damage
        self.color = color
        self.radius = 15
        self.cooldown = 0
        self.cooldown_max = 60
        self.bullets = []
        self.health = 50
        self.max_health = 50
    
    def update(self, bots):
        if self.cooldown > 0:
            self.cooldown -= 1
        
        # Ищем ближайшего бота
        if bots and self.cooldown <= 0:
            closest_bot = None
            min_distance = 300  # Дальность стрельбы
            
            for bot in bots:
                distance = math.sqrt((self.x - bot.x) ** 2 + (self.y - bot.y) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    closest_bot = bot
            
            # Стреляем в ближайшего бота
            if closest_bot:
                angle = math.atan2(closest_bot.y - self.y, closest_bot.x - self.x)
                self.bullets.append(Bullet(
                    self.x, self.y,
                    math.cos(angle) * 5,
                    math.sin(angle) * 5,
                    self.damage, self.color, 5
                ))
                self.cooldown = self.cooldown_max
        
        # Обновляем пули турели
        for bullet in self.bullets[:]:
            if not bullet.update():
                self.bullets.remove(bullet)
    
    def draw(self, surface):
        # Основание турели
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        
        # Верхняя часть (поворачивается)
        pygame.draw.rect(surface, (self.color[0]//2, self.color[1]//2, self.color[2]//2),
                        (self.x - 10, self.y - 10, 20, 20))
        
        # Полоска здоровья
        health_width = 30
        health_height = 4
        health_x = self.x - health_width // 2
        health_y = self.y - self.radius - 10
        
        pygame.draw.rect(surface, BLACK, (health_x, health_y, health_width, health_height))
        health_ratio = self.health / self.max_health
        pygame.draw.rect(surface, GREEN, 
                        (health_x, health_y, int(health_width * health_ratio), health_height))
        
        # Отрисовка пуль турели
        for bullet in self.bullets:
            bullet.draw(surface)

# Класс мины для Гения
class Mine:
    def __init__(self, x, y, damage, color):
        self.x = x
        self.y = y
        self.damage = damage
        self.color = color
        self.radius = 10
        self.active = True
        self.blink_timer = 0
    
    def update(self):
        self.blink_timer = (self.blink_timer + 1) % 30
    
    def draw(self, surface):
        if self.active:
            # Мигающий эффект
            if self.blink_timer < 15:
                pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
                pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius // 2)
            else:
                pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius)
                pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius // 2)

# Класс пули
class Bullet:
    def __init__(self, x, y, dx, dy, damage, color, radius):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.damage = damage
        self.color = color
        self.radius = radius
    
    def update(self):
        self.x += self.dx
        self.y += self.dy
        
        # Проверка границ для пуль (не даём им уходить слишком далеко)
        if self.x < -50 or self.x > WIDTH + 50 or self.y < -50 or self.y > HEIGHT + 50:
            return False
        return True
    
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        # Эффект свечения
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius // 2)

# Класс вращающейся пули для мага
class SpinningBullet(Bullet):
    def __init__(self, x, y, dx, dy, damage, color, radius, center_x, center_y):
        super().__init__(x, y, dx, dy, damage, color, radius)
        self.center_x = center_x
        self.center_y = center_y
        self.angle = 0
        self.distance = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
        self.rotation_speed = 0.1
    
    def update(self):
        # Вращение вокруг центра
        self.angle += self.rotation_speed
        self.x = self.center_x + math.cos(self.angle) * self.distance
        self.y = self.center_y + math.sin(self.angle) * self.distance
        self.distance += 0.5  # Постепенное удаление от центра
        
        # Проверка границ
        if self.x < -50 or self.x > WIDTH + 50 or self.y < -50 or self.y > HEIGHT + 50:
            return False
        return True

# Класс препятствия
class Obstacle:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
    
    def draw(self, surface):
        # Основной прямоугольник
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
        
        # Текстура препятствия (рамка)
        darker_color = (
            max(0, self.color[0] - 40),
            max(0, self.color[1] - 40),
            max(0, self.color[2] - 40)
        )
        pygame.draw.rect(surface, darker_color, (self.x, self.y, self.width, self.height), 3)

# Класс бота
class Bot(Player):
    def __init__(self, x, y, bot_type):
        colors = [RED, GREEN, PURPLE]
        super().__init__(x, y, colors[bot_type - 1], bot_type)
        self.target = None
        self.change_target_time = 0
        self.wander_time = 0
        self.wander_direction = random.uniform(0, math.pi * 2)
    
    def update_ai(self, players, obstacles):
        # Обновляем перезарядку как у обычного игрока
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.special_cooldown > 0:
            self.special_cooldown -= 1
        
        # Ищем ближайшего противника (игрока или другого бота)
        closest_enemy = None
        closest_distance = float('inf')
        
        for player in players:
            if player != self:  # Не атакуем себя
                # Игрок (player_type == 0) имеет высший приоритет
                # Но также атакуем и других ботов
                distance = math.sqrt((self.x - player.x) ** 2 + (self.y - player.y) ** 2)
                
                # Даем приоритет игроку над ботами
                if player.player_type == 0:  # Игрок
                    priority_distance = distance * 0.7  # Игрок кажется ближе
                else:  # Другой бот
                    priority_distance = distance
                
                if priority_distance < closest_distance and distance < 400:  # Видимость 400 пикселей
                    closest_distance = priority_distance
                    closest_enemy = player
        
        self.target = closest_enemy
        
        # Если нет противников в радиусе, блуждаем
        if not self.target:
            # Блуждание, если нет цели
            if self.wander_time <= 0:
                self.wander_direction = random.uniform(0, math.pi * 2)
                self.wander_time = random.randint(30, 90)
            
            dx = math.cos(self.wander_direction)
            dy = math.sin(self.wander_direction)
            self.move(dx, dy, obstacles)
            self.wander_time -= 1
            return
        
        # Поведение в зависимости от расстояния до цели
        # Поворачиваемся к цели
        self.direction = math.atan2(self.target.y - self.y, self.target.x - self.x)
        
        # Двигаемся к цели или от неё в зависимости от типа
        if self.player_type == 1:  # Стрелок держится на дистанции
            if closest_distance > 180:  # Увеличил дистанцию для лучшей атаки
                # Приближаемся
                dx = math.cos(self.direction)
                dy = math.sin(self.direction)
                # Стреляем при приближении
                if random.random() < 0.08 and self.cooldown <= 0:
                    self.shoot()
            else:
                # Отдаляемся или держим дистанцию
                if closest_distance < 150:
                    dx = -math.cos(self.direction) * 0.7
                    dy = -math.sin(self.direction) * 0.7
                else:
                    dx = 0
                    dy = 0
                # Активно стреляем
                if random.random() < 0.15 and self.cooldown <= 0:
                    self.shoot()
                    
        elif self.player_type == 2:  # Танк идёт в ближний бой
            if closest_distance > 60:  # Идет в ближний бой
                dx = math.cos(self.direction)
                dy = math.sin(self.direction)
                # Стреляет даже при движении
                if random.random() < 0.1 and self.cooldown <= 0:
                    self.shoot()
            else:
                dx = 0
                dy = 0
                # Активно стреляет в упор
                if random.random() < 0.2 and self.cooldown <= 0:
                    self.shoot()
                    
        elif self.player_type == 3:  # Маг двигается зигзагом
            if self.wander_time <= 0:
                self.wander_direction = random.uniform(0, math.pi * 2)
                self.wander_time = 40  # Увеличил время зигзага
            
            # Комбинируем движение к цели и случайное движение
            move_toward = 0.6  # Больше движения к цели
            dx = math.cos(self.direction) * move_toward + math.cos(self.wander_direction) * (1 - move_toward)
            dy = math.sin(self.direction) * move_toward + math.sin(self.wander_direction) * (1 - move_toward)
            
            # Активно стреляет
            if random.random() < 0.12 and self.cooldown <= 0:
                self.shoot()
            
            self.wander_time -= 1
            
            # Спец-атака
            if random.random() < 0.015 and self.special_cooldown <= 0:
                self.special_attack()
        
        self.move(dx, dy, obstacles)
        
        # Случайная спец-атака для всех типов
        if random.random() < 0.008 and self.special_cooldown <= 0:
            self.special_attack()
        
        # Обновление пуль
        for bullet in self.bullets[:]:
            if not bullet.update():  # Если пуля вышла за границы
                self.bullets.remove(bullet)

# Стартовый экран
def start_screen():
    font_large = pygame.font.SysFont(None, 60)
    font_medium = pygame.font.SysFont(None, 36)
    font_small = pygame.font.SysFont(None, 28)
    font_tiny = pygame.font.SysFont(None, 24)
    
    # Позиции для кнопок
    play_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 60)
    profile_button = pygame.Rect(WIDTH - 120, 20, 100, 40)
    
    # Флаг для отображения статистики
    show_stats = False
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Проверка нажатия на кнопку Play
                if play_button.collidepoint(mouse_pos):
                    return True  # Переходим к выбору персонажа
                
                # Проверка нажатия на кнопку Профиль
                if profile_button.collidepoint(mouse_pos):
                    show_stats = not show_stats
        
        screen.fill(BACKGROUND)
        
        # Заголовок игры
        title = font_large.render("super fighters", True, YELLOW)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        
        # Кнопка Play
        pygame.draw.rect(screen, GREEN, play_button, border_radius=10)
        pygame.draw.rect(screen, WHITE, play_button, 3, border_radius=10)
        play_text = font_medium.render("ИГРАТЬ", True, WHITE)
        screen.blit(play_text, (play_button.centerx - play_text.get_width()//2, 
                               play_button.centery - play_text.get_height()//2))
        
        # Кнопка Профиль
        pygame.draw.rect(screen, BLUE, profile_button, border_radius=5)
        profile_text = font_tiny.render("ПРОФИЛЬ", True, WHITE)
        screen.blit(profile_text, (profile_button.centerx - profile_text.get_width()//2, 
                                  profile_button.centery - profile_text.get_height()//2))
        
        # Отображение статистики (если нажали на профиль)
        if show_stats:
            draw_stats_panel()
        
        # Управление
        controls_text = font_small.render("Управление: WASD - движение, ЛКМ - выстрел, ПКМ - спец-атака", True, WHITE)
        screen.blit(controls_text, (WIDTH//2 - controls_text.get_width()//2, HEIGHT - 50))
        
        # Подсказка
        hint_text = font_tiny.render("Нажмите на ПРОФИЛЬ чтобы увидеть статистику", True, YELLOW)
        screen.blit(hint_text, (WIDTH//2 - hint_text.get_width()//2, HEIGHT - 100))
        
        pygame.display.flip()

# Функция для отрисовки панели статистики
def draw_stats_panel():
    # Полупрозрачная панель
    panel = pygame.Surface((600, 400), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 200))
    screen.blit(panel, (WIDTH//2 - 300, HEIGHT//2 - 200))
    
    font_title = pygame.font.SysFont(None, 40)
    font_text = pygame.font.SysFont(None, 30)
    font_small = pygame.font.SysFont(None, 24)
    
    # Заголовок
    title = font_title.render("СТАТИСТИКА ИГРЫ", True, YELLOW)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 180))
    
    y_offset = HEIGHT//2 - 130
    line_height = 35
    
    # Общая статистика
    stats_data = [
        ("Всего убийств:", str(stats.stats["total_kills"]), WHITE),
        ("Сыграно игр:", str(stats.stats["games_played"]), WHITE),
        ("Лучший результат:", str(stats.stats["best_score"]), YELLOW),
    ]
    
    for label, value, color in stats_data:
        label_text = font_text.render(label, True, WHITE)
        value_text = font_text.render(value, True, color)
        screen.blit(label_text, (WIDTH//2 - 250, y_offset))
        screen.blit(value_text, (WIDTH//2 + 150 - value_text.get_width(), y_offset))
        y_offset += line_height
    
    y_offset += 10  # Отступ
    
    # Прогресс разблокировки Гения
    unlock_progress = stats.get_unlock_progress()
    progress_text = font_text.render(f"Разблокировка Гения: {unlock_progress}%", True, CYAN)
    screen.blit(progress_text, (WIDTH//2 - progress_text.get_width()//2, y_offset))
    
    # Полоска прогресса
    progress_bar = pygame.Rect(WIDTH//2 - 100, y_offset + 30, 200, 20)
    pygame.draw.rect(screen, GRAY, progress_bar)
    pygame.draw.rect(screen, CYAN, (progress_bar.x, progress_bar.y, 
                                   progress_bar.width * unlock_progress // 100, 
                                   progress_bar.height))
    pygame.draw.rect(screen, WHITE, progress_bar, 2)
    
    y_offset += 60
    
    # Статистика по классам
    classes_text = font_text.render("Статистика по классам:", True, WHITE)
    screen.blit(classes_text, (WIDTH//2 - classes_text.get_width()//2, y_offset))
    y_offset += 40
    
    class_names = {
        "1": "Стрелок",
        "2": "Танк", 
        "3": "Маг",
        "4": "Гений"
    }
    
    for class_id in ["1", "2", "3", "4"]:
        if class_id in stats.stats["class_stats"]:
            class_stat = stats.stats["class_stats"][class_id]
            class_name = class_names.get(class_id, f"Класс {class_id}")
            
            # Показываем Гения только если он разблокирован
            if class_id == "4" and not stats.stats["unlocked_genius"]:
                class_name = "Гений (заблокирован)"
            
            kills = class_stat["kills"]
            games = class_stat["games"]
            avg_kills = kills / games if games > 0 else 0
            
            stat_text = font_small.render(
                f"{class_name}: {kills} убийств, {games} игр (среднее: {avg_kills:.1f})", 
                True, WHITE if class_id != "4" or stats.stats["unlocked_genius"] else GRAY
            )
            screen.blit(stat_text, (WIDTH//2 - stat_text.get_width()//2, y_offset))
            y_offset += 25
    
    # Кнопка сброса статистики
    reset_button = pygame.Rect(WIDTH//2 - 80, y_offset + 20, 160, 40)
    pygame.draw.rect(screen, RED, reset_button, border_radius=5)
    reset_text = font_text.render("СБРОСИТЬ", True, WHITE)
    screen.blit(reset_text, (reset_button.centerx - reset_text.get_width()//2, 
                            reset_button.centery - reset_text.get_height()//2))
    
    # Проверка нажатия на кнопку сброса
    mouse_pos = pygame.mouse.get_pos()
    if pygame.mouse.get_pressed()[0] and reset_button.collidepoint(mouse_pos):
        stats.reset_stats()

# Экран выбора персонажа
def character_selection():
    selected = 0
    font_large = pygame.font.SysFont(None, 50)
    font_medium = pygame.font.SysFont(None, 30)
    font_small = pygame.font.SysFont(None, 24)
    
    characters = [
        {"name": "СТРЕЛОК", "desc": "Быстрый, скорострельный", "color": BLUE, "type": 1, "unlocked": True},
        {"name": "ТАНК", "desc": "Много HP, мощные выстрелы", "color": ORANGE, "type": 2, "unlocked": True},
        {"name": "МАГ", "desc": "Особые вращающиеся снаряды", "color": PURPLE, "type": 3, "unlocked": True},
        {"name": "ГЕНИЙ", "desc": "Турели и мины, тактика", "color": CYAN, "type": 4, "unlocked": stats.stats["unlocked_genius"]}
    ]
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                    selected = (selected - 1) % len(characters)
                if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    selected = (selected + 1) % len(characters)
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if characters[selected]["unlocked"]:
                        return characters[selected]["type"], characters[selected]["color"]
        
        screen.fill(BACKGROUND)
        
        # Заголовок
        title = font_large.render("ВЫБЕРИТЕ ПЕРСОНАЖА", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        # Описание управления
        controls1 = font_small.render("Управление: WASD - движение, ЛКМ - выстрел", True, WHITE)
        controls2 = font_small.render("ПКМ - спец-атака, Q - мина (только Гений)", True, WHITE)
        screen.blit(controls1, (WIDTH // 2 - controls1.get_width() // 2, HEIGHT - 80))
        screen.blit(controls2, (WIDTH // 2 - controls2.get_width() // 2, HEIGHT - 50))
        
        # Отображение персонажей
        character_width = WIDTH // len(characters)
        for i, char in enumerate(characters):
            x = character_width * i + character_width // 2
            y = HEIGHT // 2 - 50
            
            # Рамка выбранного персонажа
            if i == selected:
                pygame.draw.rect(screen, WHITE if char["unlocked"] else GRAY, 
                                (x - 70, y - 120, 140, 240), 3)
            
            # Персонаж (заблокированный серый)
            char_color = char["color"] if char["unlocked"] else GRAY
            pygame.draw.circle(screen, char_color, (x, y), 40)
            
            # Замок для заблокированных персонажей
            if not char["unlocked"]:
                lock_text = font_medium.render("🔒", True, WHITE)
                screen.blit(lock_text, (x - lock_text.get_width()//2, y - lock_text.get_height()//2))
            
            # Имя
            name_color = WHITE if char["unlocked"] else GRAY
            name_text = font_medium.render(char["name"], True, name_color)
            screen.blit(name_text, (x - name_text.get_width() // 2, y + 60))
            
            # Описание
            desc_lines = split_text(char["desc"], font_small, 180)
            for j, line in enumerate(desc_lines):
                desc_color = WHITE if char["unlocked"] else GRAY
                desc_text = font_small.render(line, True, desc_color)
                screen.blit(desc_text, (x - desc_text.get_width() // 2, y + 90 + j * 25))
        
        # Информация о выбранном персонаже
        selected_char = characters[selected]
        if not selected_char["unlocked"]:
            unlock_info = font_small.render(f"Разблокируется после 10 убийств", True, YELLOW)
            screen.blit(unlock_info, (WIDTH // 2 - unlock_info.get_width() // 2, HEIGHT - 150))
            progress = stats.get_unlock_progress()
            progress_text = font_small.render(f"Прогресс: {progress}%", True, YELLOW)
            screen.blit(progress_text, (WIDTH // 2 - progress_text.get_width() // 2, HEIGHT - 120))
        
        # Инструкция
        instruct = font_small.render("Используйте A/D для выбора, ENTER для подтверждения", True, YELLOW)
        screen.blit(instruct, (WIDTH // 2 - instruct.get_width() // 2, HEIGHT - 200))
        
        pygame.display.flip()

# Функция для разделения текста на строки
def split_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        # Проверяем ширину текущей строки с новым словом
        test_line = ' '.join(current_line + [word])
        test_width = font.size(test_line)[0]
        
        if test_width <= max_width:
            current_line.append(word)
        else:
            # Сохраняем текущую строку и начинаем новую
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    # Добавляем последнюю строку
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

# Основная игровая функция
def main_game(player_type, player_color):
    # Создание игрока
    player = Player(WIDTH // 2, HEIGHT // 2, player_color, 0)
    player.player_type = player_type
    
    # Установка характеристик в зависимости от выбранного типа
    if player_type == 1:  # Стрелок
        player.speed = 5
        player.cooldown_max = 15
        player.bullet_speed = 8
        player.bullet_damage = 10
        player.bullet_color = BLUE
        player.bullet_radius = 6
        player.name = "Игрок-Стрелок"
        
    elif player_type == 2:  # Танк
        player.radius = 32
        player.speed = 3
        player.health = 150
        player.max_health = 150
        player.cooldown_max = 30
        player.bullet_speed = 6
        player.bullet_damage = 20
        player.bullet_color = player_color
        player.bullet_radius = 10
        player.name = "Игрок-Танк"
        
    elif player_type == 3:  # Маг
        player.speed = 4
        player.cooldown_max = 25
        player.bullet_speed = 7
        player.bullet_damage = 15
        player.bullet_color = player_color
        player.bullet_radius = 8
        player.name = "Игрок-Маг"
    
    elif player_type == 4:  # Гений
        player.speed = 4
        player.cooldown_max = 20
        player.bullet_speed = 6
        player.bullet_damage = 12
        player.bullet_color = player_color
        player.bullet_radius = 7
        player.name = "Игрок-Гений"
        player.max_mines = 3
        player.max_turrets = 2
        player.turret_cooldown = 0
        player.mine_cooldown = 0
        player.mines = []
        player.turrets = []
    
    # Создание ботов
    bots = []
    bot_positions = [(200, 200), (WIDTH - 200, HEIGHT - 200), (WIDTH - 200, 200)]
    for i, pos in enumerate(bot_positions):
        bot_type = (player_type + i) % 3 + 1
        bot = Bot(pos[0], pos[1], bot_type)
        bots.append(bot)
    
    # Создание препятствий
    obstacles = [
        Obstacle(300, 300, 150, 30, GRID_COLOR),
        Obstacle(WIDTH - 450, 300, 150, 30, GRID_COLOR),
        Obstacle(400, 500, 200, 30, GRID_COLOR),
        Obstacle(WIDTH - 600, 500, 200, 30, GRID_COLOR),
        Obstacle(WIDTH // 2 - 100, 100, 30, 150, GRID_COLOR),
        Obstacle(WIDTH // 2 - 100, HEIGHT - 250, 30, 150, GRID_COLOR),
    ]
    
    # Шрифты для интерфейса
    font = pygame.font.SysFont(None, 28)
    font_large = pygame.font.SysFont(None, 50)
    
    # Счётчик убийств
    kills = 0
    
    # Основной игровой цикл
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Управление мышью
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # ЛКМ
                    player.shoot()
                elif event.button == 3:  # ПКМ
                    player.special_attack()
            
            # Управление клавишами для Гения
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and player.player_type == 4:  # Q - мина для Гения
                    player.place_mine()
        
        # Обновление направления игрока
        mouse_pos = pygame.mouse.get_pos()
        player.update_direction(mouse_pos)
        
        # Управление с клавиатуры
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
            dy += 1
        if keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1
        
        # Нормализация диагонального движения
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        
        # Движение игрока
        player.move(dx, dy, obstacles)
        
        # Обновление игрока
        player.update(obstacles, bots)
        
        # Обновление ботов
        all_players = [player] + bots
        for bot in bots:
            bot.update_ai(all_players, obstacles)
        
        # Проверка столкновений пуль игрока с ботами
        for bullet in player.bullets[:]:
            for bot in bots[:]:
                distance = math.sqrt((bullet.x - bot.x) ** 2 + (bullet.y - bot.y) ** 2)
                if distance < bullet.radius + bot.radius:
                    bot.health -= bullet.damage
                    if bullet in player.bullets:
                        player.bullets.remove(bullet)
                    
                    if bot.health <= 0:
                        kills += 1
                        bots.remove(bot)
                        # Создаем нового бота в безопасном месте
                        spawn_attempts = 0
                        while spawn_attempts < 10:
                            bot_type = random.randint(1, 3)
                            spawn_x = random.randint(50, WIDTH - 50)
                            spawn_y = random.randint(50, HEIGHT - 50)
                            
                            # Проверяем, чтобы бот не появился слишком близко к игроку
                            distance_to_player = math.sqrt((spawn_x - player.x) ** 2 + (spawn_y - player.y) ** 2)
                            if distance_to_player > 150:
                                bots.append(Bot(spawn_x, spawn_y, bot_type))
                                break
                            spawn_attempts += 1
                    break
        
        # Проверка столкновений пуль ботов с игроком
        for bot in bots:
            for bullet in bot.bullets[:]:
                distance = math.sqrt((bullet.x - player.x) ** 2 + (bullet.y - player.y) ** 2)
                if distance < bullet.radius + player.radius:
                    player.health -= bullet.damage
                    if bullet in bot.bullets:
                        bot.bullets.remove(bullet)
                    
                    if player.health <= 0:
                        # Сохраняем статистику перед выходом
                        stats.add_kills(kills, player_type)
                        return kills  # Конец игры
        
        # Проверка столкновений пуль турелей с ботами
        if player.player_type == 4:
            for turret in player.turrets:
                for bullet in turret.bullets[:]:
                    for bot in bots[:]:
                        distance = math.sqrt((bullet.x - bot.x) ** 2 + (bullet.y - bot.y) ** 2)
                        if distance < bullet.radius + bot.radius:
                            bot.health -= bullet.damage
                            if bullet in turret.bullets:
                                turret.bullets.remove(bullet)
                            
                            if bot.health <= 0:
                                kills += 1
                                bots.remove(bot)
                                # Создаем нового бота
                                spawn_attempts = 0
                                while spawn_attempts < 10:
                                    bot_type = random.randint(1, 3)
                                    spawn_x = random.randint(50, WIDTH - 50)
                                    spawn_y = random.randint(50, HEIGHT - 50)
                                    
                                    distance_to_player = math.sqrt((spawn_x - player.x) ** 2 + (spawn_y - player.y) ** 2)
                                    if distance_to_player > 150:
                                        bots.append(Bot(spawn_x, spawn_y, bot_type))
                                        break
                                    spawn_attempts += 1
                            break
        
        # Проверка столкновений с минами (для Гения)
        if player.player_type == 4:
            for mine in player.mines[:]:
                for bot in bots[:]:
                    distance = math.sqrt((mine.x - bot.x) ** 2 + (mine.y - bot.y) ** 2)
                    if distance < mine.radius + bot.radius and mine.active:
                        bot.health -= mine.damage
                        mine.active = False
                        
                        if bot.health <= 0:
                            kills += 1
                            bots.remove(bot)
                            # Создаем нового бота
                            spawn_attempts = 0
                            while spawn_attempts < 10:
                                bot_type = random.randint(1, 3)
                                spawn_x = random.randint(50, WIDTH - 50)
                                spawn_y = random.randint(50, HEIGHT - 50)
                                
                                distance_to_player = math.sqrt((spawn_x - player.x) ** 2 + (spawn_y - player.y) ** 2)
                                if distance_to_player > 150:
                                    bots.append(Bot(spawn_x, spawn_y, bot_type))
                                    break
                                spawn_attempts += 1
                        break
        
        # Отрисовка
        screen.fill(BACKGROUND)
        
        # Сетка на фоне
        grid_size = 50
        for x in range(0, WIDTH, grid_size):
            pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, grid_size):
            pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y), 1)
        
        # Отрисовка препятствий
        for obstacle in obstacles:
            obstacle.draw(screen)
        
        # Отрисовка ботов
        for bot in bots:
            bot.draw(screen)
            bot.draw_bullets(screen)
        
        # Отрисовка игрока
        player.draw(screen)
        player.draw_bullets(screen)
        
        # Интерфейс
        # Здоровье игрока
        health_text = font.render(f"Здоровье: {player.health}/{player.max_health}", True, WHITE)
        screen.blit(health_text, (20, 20))
        
        # Счётчик убийств
        kills_text = font.render(f"Убийств: {kills}", True, WHITE)
        screen.blit(kills_text, (20, 60))
        
        # Количество ботов
        bots_text = font.render(f"Ботов осталось: {len(bots)}", True, WHITE)
        screen.blit(bots_text, (20, 100))
        
        # Перезарядка
        if player.cooldown > 0:
            cooldown_text = font.render(f"Перезарядка: {player.cooldown}", True, YELLOW)
            screen.blit(cooldown_text, (20, 140))
        else:
            cooldown_text = font.render("Оружие готово!", True, GREEN)
            screen.blit(cooldown_text, (20, 140))
        
        # Спец-атака
        if player.special_cooldown > 0:
            special_text = font.render(f"Спец-атака: {player.special_cooldown}", True, PURPLE)
            screen.blit(special_text, (20, 180))
        else:
            special_text = font.render("Спец-атака готова! (ПКМ)", True, GREEN)
            screen.blit(special_text, (20, 180))
        
        # Информация о персонаже (в правом верхнем углу)
        player_info = font.render(f"Персонаж: {player.name}", True, WHITE)
        screen.blit(player_info, (WIDTH - player_info.get_width() - 20, 20))
        
        # Дополнительная информация для Гения
        if player.player_type == 4:
            mines_text = font.render(f"Мины: {len(player.mines)}/{player.max_mines}", True, CYAN)
            screen.blit(mines_text, (20, 220))
            
            turrets_text = font.render(f"Турели: {len(player.turrets)}/{player.max_turrets}", True, CYAN)
            screen.blit(turrets_text, (20, 260))
            
            gen_hint = font.render("Q - поставить мину", True, CYAN)
            screen.blit(gen_hint, (WIDTH - gen_hint.get_width() - 20, 60))
        
        # Управление (внизу по центру) - разделяем на две строки
        if player.player_type == 4:
            controls_line1 = font.render("WASD - движение, ЛКМ - выстрел, Q - мина", True, WHITE)
        else:
            controls_line1 = font.render("WASD - движение, ЛКМ - выстрел", True, WHITE)
        controls_line2 = font.render("ПКМ - спец-атака", True, WHITE)
        screen.blit(controls_line1, (WIDTH // 2 - controls_line1.get_width() // 2, HEIGHT - 60))
        screen.blit(controls_line2, (WIDTH // 2 - controls_line2.get_width() // 2, HEIGHT - 30))
        
        pygame.display.flip()
        clock.tick(60)
    
    return kills

# Экран окончания игры
def game_over_screen(kills):
    font_large = pygame.font.SysFont(None, 70)
    font_medium = pygame.font.SysFont(None, 40)
    font_small = pygame.font.SysFont(None, 30)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return True  # Начать заново
                elif event.key == pygame.K_ESCAPE:
                    return False  # Выйти
        
        screen.fill(BACKGROUND)
        
        # Заголовок
        title = font_large.render("ИГРА ОКОНЧЕНА", True, RED)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
        
        # Счёт
        score_text = font_medium.render(f"Ваш счёт: {kills} убийств", True, WHITE)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 250))
        
        # Общий счет
        total_text = font_medium.render(f"Всего убийств: {stats.stats['total_kills']}", True, YELLOW)
        screen.blit(total_text, (WIDTH // 2 - total_text.get_width() // 2, 300))
        
        # Инструкция
        restart_text = font_small.render("Нажмите ENTER для повторной игры", True, YELLOW)
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, 380))
        
        exit_text = font_small.render("Нажмите ESC для выхода", True, YELLOW)
        screen.blit(exit_text, (WIDTH // 2 - exit_text.get_width() // 2, 420))
        
        pygame.display.flip()

# Главная функция
def main():
    while True:
        # Стартовый экран
        if not start_screen():
            break
        
        # Выбор персонажа
        player_type, player_color = character_selection()
        
        # Основная игра
        kills = main_game(player_type, player_color)
        
        # Сохраняем статистику
        stats.add_kills(kills, player_type)
        
        # Экран окончания игры
        if not game_over_screen(kills):
            break
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
