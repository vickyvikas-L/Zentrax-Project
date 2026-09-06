import pygame
import sys

class HillClimbGame:
    def __init__(self):
        pygame.init()
        self.width, self.height = 800, 400
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Hill Climb - Gesture Controlled")

        self.clock = pygame.time.Clock()
        self.car_x = 100
        self.car_y = 300
        self.car_speed = 0
        self.gravity = 0.5
        self.jump_speed = -10
        self.velocity_y = 0

        self.running = True
        self.brake = False
        self.accelerate = False

        self.car = pygame.Rect(self.car_x, self.car_y, 50, 30)

    def handle_gesture(self, gesture):
        """Receive gesture input from Zentrax and act on it."""
        if gesture == "closed_fist":
            self.brake = True
            self.accelerate = False
        elif gesture == "open_palm":
            self.accelerate = True
            self.brake = False
        elif gesture == "thumbs_up":
            self.velocity_y = self.jump_speed  # boost/jump
        elif gesture == "thumbs_down":
            self.car_speed = 0
            self.accelerate = False
            self.brake = False

    def update(self):
        if self.accelerate:
            self.car_speed += 0.2
        elif self.brake:
            self.car_speed -= 0.3

        self.car_speed = max(0, min(self.car_speed, 10))
        self.car.x += self.car_speed

        # Apply gravity
        self.velocity_y += self.gravity
        self.car.y += self.velocity_y
        if self.car.y >= 300:
            self.car.y = 300
            self.velocity_y = 0

    def draw(self):
        self.screen.fill((135, 206, 235))  # Sky blue
        pygame.draw.rect(self.screen, (34, 139, 34), (0, 330, 800, 70))  # Ground
        pygame.draw.rect(self.screen, (255, 0, 0), self.car)  # Car
        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()
