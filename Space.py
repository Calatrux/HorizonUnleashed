import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" # stops pygame from printing welcome message on game launch
import pygame

pygame.mixer.pre_init(44100, 16, 2, 4096) # Preinitialize mixer for sound quality
pygame.init() # initialize pygame

dir_name = os.getcwd()

width, height = 1200, 635
icon = pygame.image.load(rf"{dir_name}\ShipFrames\Frames\tile001.png") # load icon
display = pygame.display.set_mode((width, height)) # set width and height
pygame.display.set_caption("Horizon Unleashed") # Set title
pygame.display.set_icon(icon) # set icon

clock = pygame.time.Clock() # Create Clock

# Optmization
display.set_alpha(None)

game_sfx_volume = 100

import os
class Animation:
    def __init__(self, packed_frames, speed, type, size, animating, always_animating, first_frame, white_frame_location):
        self.frames = [] # all loaded images
        self.speed = speed # speed of anim
        self.type = type # for clarity 
        self.size = size # easiest to change size while loading images here
        self.animating = animating # controls if you want to animate
        self.always_animating = always_animating # if you're too lazy to use above var
        self.first_frame = first_frame # for idle frame
        self.white_frame = False # play a fully white version of the frame when the player/enemy gets hit
        self.white_frame_location = white_frame_location

        for frame in os.listdir(packed_frames): # loop through folder which contains the frames
            self.frames.append(f"{packed_frames}\{frame}") # add to frames

        for i in range(len(self.frames)):
            self.frames[i] = pygame.image.load(self.frames[i]).convert_alpha() # load frames with convert_alpha for performance
            self.frames[i] = pygame.transform.scale(self.frames[i], self.size) # scale frames using size

        self.current_frame = 0
        self.image = self.frames[self.current_frame] # define image that will be used by draw funcs

    def update(self):
        if self.animating or self.always_animating: # should you be animating?
            self.current_frame += self.speed # add float value and round so you can control speed      
            if self.current_frame >= len(self.frames):
                self.current_frame = 0 # reset current_frame
                self.animating = False
            self.image = self.frames[int(self.current_frame)] # redefine image and round current frame
            if self.white_frame: # checks if the entity that made the animation class has a white frame for when they are hit (only player/enemy)
                self.image = pygame.image.load(self.white_frame_location).convert_alpha() # since hit period small, no point animating
                self.image = pygame.transform.scale(self.image, self.size)
        else:
            self.current_frame = self.first_frame # set to idle frame
            self.image = self.frames[int(self.current_frame)] 
            if self.white_frame:
                self.image = pygame.image.load(self.white_frame_location).convert_alpha()
                self.image = pygame.transform.scale(self.image, self.size)
            return True


class UI():
    def draw_text(self, text, smooth_edges, pos, font, color):
        rendered_text = font.render(text, smooth_edges, color) # uses font to render text
        display.blit(rendered_text, pos) # draws rendered text on screen

    def draw_image(self, image, pos):
        display.blit(image, pos)

    def draw_shape(self, shape, pos, color):
        if shape == 'rectangle': # checks shape
            pygame.draw.rect(display, color, pos, 5) # draws rounded rectangle
            pygame.draw.rect(display, color, pos) # draws normal rect
        if shape == 'triangle':
            pygame.draw.polygon(display, color, pos)

class Timer:
    def __init__(self, time_until_event):
        self.time_until_event = time_until_event
        self.current_time = self.time_until_event

    def decrease_time(self, updated_time): # updated_time for non-constant timer
        if self.current_time > 0:
            self.current_time -= 1 / 60 # decreases timer by delta time (1 / fps)
            return False
        elif self.current_time <= 0:
            if updated_time is not None:
                self.current_time = updated_time # resets time
            else:
                self.current_time = self.time_until_event
            return True

class QuitInputReciever(): # lots of other classes checking for quit, so it's easier to make a class for it
    def check_if_quit(self): 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()


import random
class Powerup():
    def __init__(self):
        self.x = 0
        self.y = 0

        self.type = 'none'

        self.rarity = 'none'
        self.powerups = {'medkit' : 'common', 'speedup' : 'rare', 'damage' : 'rare', 'invincibility' : 'epic', 'doublelaser' : 'legendary'} # list of powerups with rarities

        self.pickup_fx = pygame.mixer.Sound(rf"{dir_name}\SFX\Powerup.wav") # load pickup sfx
        self.pickup_fx.set_volume(0.13 * (game_sfx_volume / 100))

        self.lifespan = Timer(45) # timer for lifespan

        self.parent_folder = rf"{dir_name}\Powerups" # parent folder with all powerups
        self.image = None

        self.destroyed = False

        self.create()

    def update(self):
        if not self.destroyed:
            self.decrease_lifespan()
            self.draw()

    def create(self):
        self.x = random.randrange(100, 1100) # generate random pos
        self.y = random.randrange(100, 535)

        rand_rarity = random.randrange(100) + 1 # generate random rarity
        
        if rand_rarity <= 45: # assign rarity
            self.rarity = 'common'
        elif rand_rarity <= 75:
            self.rarity = 'rare'
        elif rand_rarity <= 90:
            self.rarity = 'epic'
        elif rand_rarity <= 100:
            self.rarity = 'legendary'


        rand_powerups_list = []

        for key, value in self.powerups.items(): # appends all powerups of a specific rarity to a list
            if value == self.rarity:
                rand_powerups_list.append(key)

        self.type = random.choice(rand_powerups_list)  # randomly chooses powerup from list

        self.image = pygame.transform.scale(pygame.image.load(f"{self.parent_folder}\{self.type}.png").convert_alpha(), (25, 25)) # loads and scales image

    def draw(self):
        display.blit(self.image, (self.x, self.y))

    def decrease_lifespan(self):
        if self.lifespan.decrease_time(None):
            self.destroyed = True # destroy if lifespan runs out

    def picked_up(self):
        self.destroyed = True
        self.pickup_fx.play() # play sfx
        return self.type # return type to player

class PowerupSpawner():
    def __init__(self, timespan):
        self.timer = Timer(timespan) # period of time between powerup spawns

    def update(self, player_dead):
        if not player_dead:
            if self.timer.decrease_time(None): # if timer runs out, spawn powerup
                powerup = Powerup()
                return powerup

class Explosion():
    def __init__(self, position, size):
        self.animation = Animation(rf"{dir_name}\ExplosionFrames", 0.2, 'explosion', size, True, False, 0, None) # load animation
        self.position = position
        self.destroyed = False

    def update(self):
        if not self.destroyed:
            return self.draw()

    def draw(self):
        finished = self.animation.update() # checks to see if animation finished
        if not finished:
            display.blit(self.animation.image, self.position)
            return False
        else:
            self.destroyed = True # if finished, destroy
            return True
import math
class Laser():
    def __init__(self, x, y, rotation, damage):
        self.x = x
        self.y = y
        self.name = 'laser'

        self.rotation = rotation
        self.speed = 8
        self.damage = damage

        self.destroyed = False
        self.collision_tolerance = 25

        self.animation = Animation(rf"{dir_name}\LaserFrames", 0.05, 'laser', (18,18), True, True, 0, None)

        self.calc_init_movement() 

    def update(self):
        if not self.destroyed:
            self.move()
            self.animation.update()
            self.contain_laser()
            self.draw()

    def draw(self):
        image, pos = self.rotate() # gathers vars from rotate 
        display.blit(image, pos) # draws laser

    def calc_init_movement(self):
        self.dx = math.cos(math.radians(self.rotation)) # the movement system for player and lasers is not right
        self.dy = math.sin(math.radians(self.rotation)) # tried to follow tutorials but didn't work

    def move(self):
        self.x -= self.dy * self.speed # so i started experimenting
        self.y -= self.dx * self.speed # and landed on this

    def rotate(self):
        rotated_image = pygame.transform.rotate(self.animation.image, self.rotation) # rotate image
        new_rect = self.animation.image.get_rect(center=(self.x, self.y)) 
        new_rect = rotated_image.get_rect(center = new_rect.center) 
        return rotated_image, new_rect # return so that draw func can use it

    def collide(self, other):
        dx, dy = other.x - self.x, other.y - self.y # calc delta
        dist = math.hypot(dx, dy) # calc distance
        if dist < self.collision_tolerance and not other.destroyed:
            self.destroyed = True
            if other.damage_enemy(self.damage):
                return True
        return "none"

    def contain_laser(self):
        if self.x >= 1250:
            self.destroyed = True
        if self.x <= -50:
            self.destroyed = True
        if self.y >= 685:
            self.destroyed = True
        if self.y <= -50:
            self.destroyed = True

import sys
class Player():
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.slx = x + 4 # x-coord for second laser
        self.sly = y + 4 # y-coord for second laser
        self.name = 'player'

        self.angle = 0

        self.speed = 3
        self.delta = [0,0,0] # delta movement x, delta movement y, delta mouse down

        self.max_health = 300
        self.health = self.max_health
        self.destroyed = False

        self.invincible = False
        self.invincibility_timer = None

        self.collision_tolerance = 30

        self.animation = Animation(rf"{dir_name}\ShipFrames\Frames", 0.3, 'player', (46, 46), False, False, 0, rf"{dir_name}\ShipFrames\Whited\tile004.png")

        self.lasers = [] # list of all lasers created
        self.shooting_speed = 0.2
        self.can_shoot = True
        self.shooting_timer = Timer(self.shooting_speed)
        self.laser_damage = 50
        self.double_lasers = False

        self.shoot_fx = pygame.mixer.Sound(rf"{dir_name}\SFX\Laser.wav") # load shoot sfx
        self.shoot_fx.set_volume(0.045 * (game_sfx_volume / 100))

        self.hit_fx = pygame.mixer.Sound(rf"{dir_name}\SFX\Hit.wav") # load hit sfx
        self.hit_fx.set_volume(0.15 * (game_sfx_volume / 100))

        self.quit_reciever = QuitInputReciever() # load quit reciever

        self.hit_timer = Timer(0.1)
        self.pause_button_timer = Timer(0.1)
        self.can_pause = True

        self.player_reset = False
        self.paused = False

    def update(self, powerups):
        self.get_input()
        if not self.destroyed:
            self.rotate()
            self.collide_with_powerups(powerups)
            self.update_effects()
            self.contain_player()
            self.shoot_timer()
            self.draw()
            if self.hit_timer.decrease_time(None):
                self.animation.white_frame = False
                self.hit_timer = Timer(0.1)
            self.slx = self.x + 4
            self.sly = self.y + 4

    def get_input(self):
        self.quit_reciever.check_if_quit() # check if quit

        if self.pause_button_timer.decrease_time(None):
            self.can_pause = True

        keystate = pygame.key.get_pressed() # get key presses
        if keystate[pygame.K_a]:
            self.move('x', -self.speed) # move player on axis
        if keystate[pygame.K_d]:
            self.move('x', self.speed)
        if keystate[pygame.K_w]:
            self.move('y', -self.speed)
        if keystate[pygame.K_s]:
            self.move('y', self.speed)
        if keystate[pygame.K_SPACE] and self.destroyed:
            self.player_reset = True # reset if space and destroyed
        if keystate[pygame.K_ESCAPE] and self.destroyed:
            MainMenu()
        if keystate[pygame.K_TAB] and not self.destroyed and self.can_pause:
            if self.can_pause and not self.paused:
                self.can_pause = False
                self.paused = True
                self.pause_button_timer = Timer(0.1)
            if self.can_pause and self.paused:
                self.can_pause = False
                self.paused = False
                self.pause_button_timer = Timer(0.1)
        if keystate[pygame.K_ESCAPE] and not self.destroyed and self.paused:
            MainMenu()
                
        if pygame.mouse.get_pressed()[0] and self.can_shoot and not self.destroyed:
            self.shoot() # shoot when left mouse button clicked

    def move(self, axis, speed):
        if axis == 'x':
            self.x += speed
        if axis == 'y':
            self.y += speed
        self.animation.animating = True # start animating when moving
        
    def rotate(self):
        mouse_pos = pygame.mouse.get_pos() # get mouse pos
        dx, dy =  mouse_pos[0] - self.x, mouse_pos[1] - self.y
        self.angle = math.degrees(math.atan2(dx, dy))
        self.angle = self.angle % 360

    def draw(self):
        image, pos = self.rotate_ship(self.angle + 180) # run it through rotate first to get angled image and rect
        display.blit(image, pos) # draw player

    def rotate_ship(self, angle):
        rotated_image = pygame.transform.rotate(self.animation.image, angle) # rotate image
        new_rect = self.animation.image.get_rect(center=(self.x, self.y))
        new_rect = rotated_image.get_rect(center = new_rect.center)
        return rotated_image, new_rect # return rect

    def contain_player(self):
        if self.x >= 1200:
            self.x = 1200
        if self.x <= 10:
            self.x = 10 
        if self.y >= 620:
            self.y = 620
        if self.y <= 10:
            self.y = 10

    def shoot(self):
        self.laser = Laser(self.slx - 8, self.sly - 8, self.angle + 180, self.laser_damage) # creates new laser
        self.lasers.append(self.laser) # adds laser to list
        if self.double_lasers:
            self.second_laser = Laser(self.slx, self.sly, self.angle + 180, self.laser_damage) # creates new laser
            self.lasers.append(self.second_laser)
        self.can_shoot = False
        self.shoot_fx.play()

    def collide_with_powerups(self, other):
        for powerup in other:
            dx, dy = powerup.x - self.x, powerup.y - self.y # calc delta
            dist = math.hypot(dx, dy) # calc distance
            if dist < self.collision_tolerance and not powerup.destroyed:
                effect = powerup.picked_up()
                self.apply_powerup_effect(effect)

    def apply_powerup_effect(self, effect): # applies effect
        if effect == 'medkit':
            self.health += 50
            if self.health > self.max_health: self.health = self.max_health
        elif effect == 'speedup':
            self.speed += 0.3
        elif effect == 'invincibility':
            self.invincibility_timer = Timer(10)
        elif effect == 'damage':
            self.laser_damage += 15
        elif effect == 'doublelaser':
            self.double_lasers = True

    def update_effects(self): # update func for temp buffs
        if self.invincibility_timer != None:
            if self.invincibility_timer.decrease_time(None):
                self.invincible = False
                self.invincibility_timer = None
            else:
                if self.invincible == False:
                    self.invincible = True

        if self.invincible:
            self.invincible_icon = pygame.image.load(rf"{dir_name}\Powerups\invincibility.png").convert_alpha()
            self.invincible_icon = pygame.transform.scale(self.invincible_icon, (40,40))
            display.blit(self.invincible_icon, (1140, 20))

    def shoot_timer(self):
        if self.shooting_timer.decrease_time(None) and self.can_shoot == False: # timer to stop infinite shooting
            self.can_shoot = True

    def damage_player(self, damage):
        self.health -= damage
        self.hit_fx.play()
        self.animation.white_frame = True
        if self.health <= 0:
            self.destroyed = True



class Enemy():
    def __init__(self):
        self.x = 0
        self.y = 0

        self.angle = 0
        self.speed = 0
        self.damage = 0
        self.name = 'none' # type of enemy, none as default
        self.size = (0,0)
        self.explosion = None

        self.destroyed = False

        self.collision_tolerance = 15
        self.collided_with_player = False

        self.hit_fx = pygame.mixer.Sound(rf"{dir_name}\SFX\Hit.wav") # load hit sfx
        self.hit_fx.set_volume(0.08 * (game_sfx_volume / 100))

        self.explosion_sfx = pygame.mixer.Sound(rf"{dir_name}\SFX\Explosion.wav") # load sfx
        self.explosion_sfx.set_volume(0.1 * (game_sfx_volume / 100))

        self.hit_timer = Timer(0.1)
        
        self.spawn()

    def spawn(self):
        direction = random.randrange(4) # gets random direction for enemy
        if direction == 0:
            self.x = random.randrange(20, 1180)
        elif direction == 1:
            self.y = random.randrange(20, 615)
            self.x = 1180   
        elif direction == 2:
            self.x = random.randrange(0, 1180)
            self.y = 610
        elif direction == 3:
            self.y = random.randrange(20, 580)

        self.determine_enemy_type()

    def determine_enemy_type(self):
        enemy_type = random.randrange(10) # random enemy type
        if enemy_type <= 5:
            self.animation = Animation(rf"{dir_name}\EnemyFrames\Small", 0.125, 'enemy_small', (20,20), True, True, 0, rf"{dir_name}\EnemyFrames\Whited\Small\tile000.png")
            self.name = 'enemy_small'
            self.size = (20,20)
            self.speed = 2.3
            self.damage = 25
            self.health = 150
            self.reward = 3000

        elif enemy_type <= 8:
            self.animation = Animation(rf"{dir_name}\EnemyFrames\Medium", 0.125, 'enemy_medium', (28,28), True, True, 0, rf"{dir_name}\EnemyFrames\Whited\Medium\tile000.png")
            self.name = 'enemy_medium'
            self.size = (28,28)
            self.speed = 1.75
            self.damage = 50
            self.health = 300
            self.reward = 5000

        elif enemy_type <= 9:
            self.animation = Animation(rf"{dir_name}\EnemyFrames\Big", 0.125, 'enemy_big', (50,50), True, True, 0, rf"{dir_name}\EnemyFrames\Whited\Big\tile000.png")
            self.name = 'enemy_big'
            self.size = (45,45)
            self.speed = 1
            self.damage = 100
            self.health = 450
            self.reward = 10000

    def update(self, player):
        if not self.destroyed:
            self.move_to_player(player)
            self.calc_rotate(player)
            rot_image, pos = self.rotate_ship(self.angle)
            self.draw(rot_image, pos)
            if self.hit_timer.decrease_time(None):
                self.animation.white_frame = False

    def draw(self, image, pos):
        display.blit(image, pos) # run through rotate, this time if update

    def move_to_player(self, player): # WARNING: math ahead
        if player.destroyed: self.destroyed = True
        dx, dy = player.x - self.x, player.y - self.y # calc delta
        dist = math.hypot(dx, dy) # calc distance
        dx, dy = dx / dist, dy / dist # normalize
        self.x += dx * self.speed # add delta x and y
        self.y += dy * self.speed

    def calc_rotate(self, player):
        dx, dy = player.x - self.x, player.y - self.y # recalculate because move_to_player func normalizes it
        self.angle = math.degrees(math.atan2(dx, dy)) # don't know why x goes first (it's supposed to be other way around)
        self.angle = self.angle % 360 # for aesthetic

    def rotate_ship(self, angle): # same rotate func as always
        rotated_image = pygame.transform.rotate(self.animation.image, angle) 
        new_rect = self.animation.image.get_rect(center=(self.x, self.y))
        new_rect = rotated_image.get_rect(center = new_rect.center)
        return rotated_image, new_rect

    def damage_enemy(self, damage):
        self.health -= damage
        self.hit_fx.play()
        self.animation.white_frame = True
        self.hit_timer = Timer(0.1)
        return self.check_if_dead()

    def check_if_dead(self):
        if self.health <= 0:
            self.explosion = Explosion((self.x, self.y), self.size)
            self.explosion_sfx.play()
            self.destroyed = True
            return True
        return False

    def collide(self, player):
        dx, dy = player.x - self.x, player.y - self.y # calc delta
        dist = math.hypot(dx, dy) # calc distance
        if dist < self.collision_tolerance and not player.destroyed and not self.collided_with_player:
            if player.invincible:
                self.collided_with_player = True
                self.damage_enemy(self.health) # takes out health bar which causes an explosion
                return True
            self.collided_with_player = True
            player.damage_player(self.damage)
            self.destroyed = True
            return True
        return False

class EnemySpawner():
    def __init__(self, fps):
        self.time_between_spawns = 2
        self.timer = Timer(self.time_between_spawns)

        self.fps = fps

    def update(self, player_dead):
        if not player_dead:
            if self.timer.decrease_time(self.time_between_spawns): # if timer finished, spawn enemy
                return Enemy()

class MainMenu():
    def __init__(self):
        self.ui = UI() # ui element for text and buttons
        self.quit_reciever = QuitInputReciever()

        self.hovering = 'none'

        self.global_music_volume = 100
        self.global_sfx_volume = 100

        self.menu_music = pygame.mixer.music.load(rf"{dir_name}\Music\menu.ogg")
        pygame.mixer.music.set_volume(0.2 * (self.global_music_volume / 100))
        self.select_sfx = pygame.mixer.Sound(rf"{dir_name}\SFX\Select.wav")

        self.playing_music = False
        self.played_select = False

        pygame.mixer.music.play(-1)

        self.loading = False
        self.options_up = False

        self.background = pygame.transform.scale(pygame.image.load(rf"{dir_name}\Back2.png").convert_alpha(), (width, height)) # load and scale background

        self.play_color = (180,180,180) # load colors thru var so that they can become darker when hovered over
        self.settings_color = (180,180,180)
        self.quit_color = (180,180,180)
        self.back_color = (180,180,180)
        self.settings_left_tri_color = (180,180,180)
        self.settings_right_tri_color = (180,180,180)
        self.music_left_tri_color = (180,180,180)
        self.music_right_tri_color = (180,180,180)
        self.sfx_left_tri_color = (180,180,180)
        self.sfx_right_tri_color = (180,180,180)

        self.difficulty_position = {1 : "Easy", 2 : "Medium", 3 : "Hard", 4 : "Impossible"} # dict helps with difficulty select mechanism
        self.position = 1
        self.triangle_offsets = {"Easy" : 0, "Medium" : 65, "Hard" : 0, "Impossible" : 190} # x-coord position offsets to accomodate larger strings
        self.game_difficulty = "Easy"

        self.change_pos_timer = Timer(0.3) # to stop cycling thru difficulties with one click
        self.can_change_pos = True

        self.up = True
        self.update()


    def update(self):
        while self.up and not self.loading and not self.options_up:
            self.quit_reciever.check_if_quit()

            self.create_ui()
            self.detect_button_hover()
            self.change_color()
            self.detect_mouse_press()

            pygame.display.update()
            clock.tick(60)

    def load_game(self): # loads game after play button clicked
        self.loading = True
        loading_timer = Timer(2.5)
        while self.loading:
            display.fill((0,0,0))
            self.ui.draw_text(f"LOADING", False,  (275, 200), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 100), (180,180,180))
            pygame.mixer.music.fadeout(2500)
            pygame.display.update()
            if loading_timer.decrease_time(None):
                self.loading = False
        Game(self.game_difficulty, self.global_music_volume)

    def settings_menu(self): # called when settings menu clicked
        self.options_up = True
        while self.options_up:
            display.fill((0,0,0))
            display.blit(self.background, (0,0))
            self.quit_reciever.check_if_quit()
            # draws buttons and text thru ui class
            self.ui.draw_text(f"Back", False,  (40, 25), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 40), self.back_color)
            
            self.ui.draw_text(f"Diffuculty: ", False,  (40, 100), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 40), (180,180,180))
            self.ui.draw_shape('triangle', [(500,100), (500,150), (450,125)], self.settings_left_tri_color)
            self.ui.draw_text(self.determine_difficulty(), False, (525, 105), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 40), (180,180,180))
            self.ui.draw_shape('triangle', [(710 + self.tri_offset(),100), (710 + self.tri_offset(),150), (760 + self.tri_offset(),125)], self.settings_right_tri_color)

            self.ui.draw_text("MUSIC VOLUME: ", False,  (40, 200), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 33), (180,180,180))
            self.ui.draw_shape('triangle', [(500,200), (500,250), (450,225)], self.music_left_tri_color)
            self.ui.draw_text(str(self.global_music_volume), False,  (560, 207), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 40), (180,180,180))
            self.ui.draw_shape('triangle', [(710,200), (710,250), (760,225)], self.music_right_tri_color)

            self.ui.draw_text("SFX VOLUME: ", False,  (40, 300), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 38), (180,180,180))
            self.ui.draw_shape('triangle', [(500,300), (500,350), (450,325)], self.sfx_left_tri_color)
            self.ui.draw_text(str(self.global_sfx_volume), False,  (560, 307), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 40), (180,180,180))
            self.ui.draw_shape('triangle', [(710,300), (710,350), (760,325)], self.sfx_right_tri_color)


            self.detect_settings_hover()
            self.change_color()
            self.detect_mouse_press()
            pygame.display.update()

    def tri_offset(self): # move triangle to prevent triangle and text overlap
        offset = self.triangle_offsets.get(self.determine_difficulty())
        return offset

    def create_ui(self): # main menu ui
        display.blit(self.background, (0,0))
        self.ui.draw_text(f"HORIZON UNLEASHED", False,  (40, 100), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 70), (180,180,180))
        self.ui.draw_text(f"PLAY", False,  (515, 290), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 55), self.play_color)
        self.ui.draw_text(f"SETTINGS", False,  (435, 400), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 55), self.settings_color)
        self.ui.draw_text(f"QUIT", False,  (530, 500), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 55), self.quit_color)

    def detect_settings_hover(self): # detects when mouse hovers over button in settings menu
        mouse_x, mouse_y = pygame.mouse.get_pos()
        offset = self.tri_offset()
        if self.options_up == False: return

        if mouse_x > 30 and mouse_x < 210 and mouse_y > 25 and mouse_y < 75:
            if not self.hovering == 'back':
                self.hovering = 'back'
                self.play_sfx(False)
        elif mouse_x > 440 and mouse_x < 510 and mouse_y > 95 and mouse_y < 155:
            if not self.hovering == 'left_tri':
                self.hovering = 'left_tri'
                self.play_sfx(False)
        elif mouse_x > 705 + offset and mouse_x < 765 + offset and mouse_y > 95 and mouse_y < 155:
            if not self.hovering == 'right_tri':
                self.hovering = 'right_tri'
                self.play_sfx(False)
        elif mouse_x > 440 and mouse_x < 510 and mouse_y > 195 and mouse_y < 255:
            if not self.hovering == 'music_left_tri':
                self.hovering = 'music_left_tri'
                self.play_sfx(False)
        elif mouse_x > 705 + offset and mouse_x < 765 + offset and mouse_y > 195 and mouse_y < 255:
            if not self.hovering == 'music_right_tri':
                self.hovering = 'music_right_tri'
                self.play_sfx(False)
        elif mouse_x > 440 and mouse_x < 510 and mouse_y > 295 and mouse_y < 355:
            if not self.hovering == 'sfx_left_tri':
                self.hovering = 'sfx_left_tri'
                self.play_sfx(False)
        elif mouse_x > 705 + offset and mouse_x < 765 + offset and mouse_y > 295 and mouse_y < 355:
            if not self.hovering == 'sfx_right_tri':
                self.hovering = 'sfx_right_tri'
                self.play_sfx(False)
        else: self.hovering = "none"

    

    def detect_button_hover(self): # detects button hover in main menu
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_x > 490 and mouse_x < 760 and mouse_y > 260 and mouse_y < 390:
            if not self.hovering == 'play':
                self.hovering = 'play'
                self.play_sfx(False)
        elif mouse_x > 450 and mouse_x < 800 and mouse_y > 400 and mouse_y < 460:
            if not self.hovering == 'settings':
                self.hovering = 'settings'
                self.play_sfx(False)
        elif mouse_x > 540 and mouse_x < 700 and mouse_y > 510 and mouse_y < 570:
            if not self.hovering == 'quit':
                self.hovering = 'quit'
                self.play_sfx(False)
        else: self.hovering = 'none'

    def detect_mouse_press(self): # detects if mouse is pressed and then executes code
        if pygame.mouse.get_pressed()[0]:
            if self.hovering == 'play':
                self.play()
            elif self.hovering == 'settings':
                self.settings()
            elif self.hovering == 'quit':
                self.quit()
            elif self.hovering == "back":
                self.options_up = False
                self.play_sfx(True)
            elif self.hovering == "left_tri" and self.can_change_pos:
                self.reduce_position()
                self.can_change_pos = False
                self.change_pos_timer = Timer(0.5)
                self.play_sfx(True)
            elif self.hovering == "right_tri" and self.can_change_pos:
                self.increase_position()
                self.can_change_pos = False
                self.change_pos_timer = Timer(0.3)
                self.play_sfx(True)
            elif self.hovering == "music_left_tri":
                self.decrease_volume("music")
            elif self.hovering == "music_right_tri":
                self.increase_volume("music")
            elif self.hovering == "sfx_left_tri":
                self.decrease_volume("sfx")
            elif self.hovering == "sfx_right_tri":
                self.increase_volume("sfx")
            else:
                if self.change_pos_timer.decrease_time(None):
                    self.can_change_pos = True

            
    def change_color(self): # change button color when hovered over, more feedback
        if self.hovering == 'play':
            self.play_color = (100,100,100)
        else:
            self.play_color = (180,180,180)
        if self.hovering == 'settings':
            self.settings_color = (100,100,100)
        else:
            self.settings_color = (180,180,180)
        if self.hovering == 'quit':
            self.quit_color = (100,100,100)
        else:
            self.quit_color = (180,180,180)
        if self.hovering == 'back':
            self.back_color = (100,100,100)
        else:
            self.back_color = (180,180,180)
        if self.hovering == 'left_tri':
            self.settings_left_tri_color = (100,100,100)
        else:
            self.settings_left_tri_color = (180,180,180)
        if self.hovering == 'right_tri':
            self.settings_right_tri_color = (100,100,100)
        else:
            self.settings_right_tri_color = (180,180,180)
        if self.hovering == 'music_left_tri':
            self.music_left_tri_color = (100,100,100)
        else:
            self.music_left_tri_color = (180,180,180)
        if self.hovering == 'music_right_tri':
            self.music_right_tri_color = (100,100,100)
        else:
            self.music_right_tri_color = (180,180,180)
        if self.hovering == 'sfx_left_tri':
            self.sfx_left_tri_color = (100,100,100)
        else:
            self.sfx_left_tri_color = (180,180,180)
        if self.hovering == 'sfx_right_tri':
            self.sfx_right_tri_color = (100,100,100)
        else:
            self.sfx_right_tri_color = (180,180,180)



    def play_sfx(self, clicked): # play small sound effect when button hovered or clicked
        if self.hovering != 'none' and not clicked:
            self.select_sfx.set_volume(0.01 * (game_sfx_volume / 100))
            self.select_sfx.play()
        elif clicked:
            self.select_sfx.set_volume(0.04 * (game_sfx_volume / 100))
            self.select_sfx.play()

    def play(self): # plays game
        self.play_sfx(True)
        self.load_game()
        self.up = False

    def settings(self): # opens settings
        self.play_sfx(True)
        self.settings_menu()

    def quit(self): # quits game
        self.play_sfx(True)
        pygame.quit()
        sys.exit()


    def reduce_position(self): # left arrow for difficulty select
        if self.position == 1:
            self.position = 4
        else:
            self.position -= 1

    def increase_position(self): # right arrow for difficulty select
        if self.position == 4:
            self.position = 1
        else:
            self.position += 1

    def increase_volume(self, audio_type):
        if audio_type == "music" and self.global_music_volume < 100:
            self.global_music_volume += 1
            pygame.mixer.music.set_volume(0.2 * (self.global_music_volume / 100))
        if audio_type == "sfx" and self.global_sfx_volume < 100:
            self.global_sfx_volume += 1

        global game_sfx_volume
        game_sfx_volume = self.global_sfx_volume # since other classes use this, better to use global var
        
        
    def decrease_volume(self, audio_type):
        if audio_type == "music" and self.global_music_volume > 0:
            self.global_music_volume -= 1
            pygame.mixer.music.set_volume(0.2 * (self.global_music_volume / 100))
        if audio_type == "sfx" and self.global_sfx_volume > 0:
            self.global_sfx_volume -= 1

        global game_sfx_volume
        game_sfx_volume = self.global_sfx_volume


    def determine_difficulty(self):
        difficulty = self.difficulty_position.get(self.position)
        self.game_difficulty = difficulty
        return difficulty


class Game():
    def __init__(self, difficulty, music_volume):
        self.fps = 60
        self.score = 0

        self.difficulty_time = 4

        self.difficulty = difficulty

        self.player = Player(600, 317)
        self.enemy_spawner = EnemySpawner(self.fps)
        self.moving_entities = [self.player] # master list of all moving entities on screen
        self.powerups = [] # keeps track of powerups
        self.powerup_timespan = {"Easy" : 30, "Medium" : 35, "Hard" : 40, "Impossible" : 45}
        self.powerup_spawner = PowerupSpawner(self.powerup_timespan.get(self.difficulty))

        self.explosions = [] # keeps track of explosions

        self.ui = UI()
        
        self.quit_reciever = QuitInputReciever()

        self.background = pygame.transform.scale(pygame.image.load(rf"{dir_name}\Back2.png").convert_alpha(), (width, height)) # load and scale background

        self.global_music_volume = music_volume

        self.battle_music = pygame.mixer.music.load(rf"{dir_name}\Music\battle2.ogg")
        self.play_music('battle')
        self.playing_music = False

        self.run_game()

    def run_game(self):
        while not self.player.paused:
            display.fill((0,0,0)) # fill backgound
            display.blit(self.background, (0,0)) # draw background
            self.update_moving_entity() # updates all entities that are moving on screen
            self.update_powerups() # updates all powerups
            self.update_explosions() # updates all explosions
            self.update_moving_entity_anim() # updates the animations of all moving entities on screen
            self.add_entity() # adds entity to master entity list
            self.remove_entity() # removes entity from list
            self.handle_game_ui() # handles score and health bar
            pygame.display.update() # update display
            self.quit_reciever.check_if_quit()
            clock.tick(self.fps)
        self.paused() # pauses game on [esc]

    def paused(self):
        while self.player.paused:
            self.quit_reciever.check_if_quit()
            self.player.get_input()
            self.ui.draw_text(f"PAUSED", False,  (450, 100), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 50), (180,180,180))
            self.ui.draw_text(f"EXIT TO MAIN MENU [ESC]", False,  (250, 250), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 38), (180,180,180))
            pygame.mixer.music.set_volume(0.04 * (self.global_music_volume / 100)) # quiet the music when paused
            clock.tick(60)
            pygame.display.update()
        pygame.mixer.music.set_volume(0.1 * (self.global_music_volume / 100))
        self.run_game()

    def play_music(self, music): # plays music using music volume set in the settings 
        if music == 'battle':
            pygame.mixer.music.set_volume(0.1 * (self.global_music_volume / 100))
            if self.player.paused: pygame.mixer.music.set_volume(0.03 * (self.global_music_volume / 100))
            pygame.mixer.music.play(-1, fade_ms=1500)
        if music == 'gameover' and not self.playing_music:
            pygame.mixer.music.unload()
            self.game_over_music = pygame.mixer.music.load(rf"{dir_name}\Music\in-the-wreckage.ogg")
            pygame.mixer.music.set_volume(0.3 * (self.global_music_volume / 100))
            pygame.mixer.music.play(-1, fade_ms=2000)
            self.playing_music = True

    def update_moving_entity(self):
        for entity in self.moving_entities:
            if 'enemy' in entity.name:
                entity.update(self.player)
                entity.collide(self.player) # calls func that detects if there is a collision
                continue
            if 'player' == entity.name:
                entity.update(self.powerups) # calls func that detetcts if it collides with powerup
                continue
            entity.update()

    def update_powerups(self):
        for powerup in self.powerups:
            powerup.update()

    def update_moving_entity_anim(self):
        for x in range(len(self.player.lasers)):
            if len(self.player.lasers) > 0 and not self.player.lasers[x].destroyed: # if there are lasers on screen
                for entity in self.moving_entities:
                    if 'enemy' in entity.name and not entity.destroyed: # and there are enemies
                        if self.player.lasers[x].collide(entity) == True: # check if laser hits enemies and if that is true
                            self.increase_score(entity.reward) # increase the score
                if self.player.lasers[x] not in self.moving_entities: # if laser not part of moving entities
                    self.moving_entities.append(self.player.lasers[x]) # append it

        for i in range(len(self.moving_entities)):
            self.moving_entities[i].animation.update() # updates all animations

    def update_explosions(self):
        for explosion in self.explosions:
            if explosion != None:
                if explosion.update(): # if explosion anim has finished
                    self.explosions.remove(explosion) # remove it from the list
                    del explosion # and delete it so that there is no memory leak

    def remove_entity(self):
        for i in range(len(self.moving_entities) - 1):
            if len(self.moving_entities) > 0 and i < len(self.moving_entities) and self.moving_entities[i].destroyed: # if entity is destroyed
                if self.moving_entities[i].name == 'player': # continue if it's a player
                    continue
                if 'enemy' in self.moving_entities[i].name: # spawn explosion if it's an enemy
                    if self.moving_entities[i].explosion != None:
                        self.explosions.append(self.moving_entities[i].explosion)
                del self.moving_entities[i] # then delete it to prevent memory leak

    def add_entity(self):
        enemy = self.enemy_spawner.update(self.player.destroyed)
        if enemy != None:
            self.moving_entities.append(enemy) # append enemy once it has spawned
            self.increase_diffuculty() # increase difficulty for every enemy spawned (exponential difficulty curve)

        powerup = self.powerup_spawner.update(self.player.destroyed)
        if powerup is not None:
            self.powerups.append(powerup) # append powerup to list

    def increase_diffuculty(self):
        if self.difficulty == 'Easy': # constants for each difficulty level, determines how fast the difficulty increases
            self.difficulty_time = 0.6 # when the difficulty stops getting harder
            self.diffuculty_denominator = 225 # how many enemies it takes for spawn time to decrease by one sec
        if self.difficulty_time == 'Medium':
            self.difficulty_time = 0.4
            self.diffuculty_denominator = 150 # eg. here, after 150 enemies spawn the spawn time would have gone from 2 to 1 sec
        if self.difficulty_time == 'Hard':
            self.difficulty_time = 0.3
            self.diffuculty_denominator = 100
        if self.difficulty == 'Impossible':
            self.difficulty_time = 0.2
            self.diffuculty_denominator = 75

        if self.enemy_spawner.time_between_spawns > self.difficulty_time:
            self.enemy_spawner.time_between_spawns -= 1 / self.diffuculty_denominator # decrease the spawn time between enemies

    def increase_score(self, increased_score):
        self.score += increased_score

    def handle_game_ui(self):
        if self.player.destroyed:
            self.ui.draw_text(f"GAME OVER", False,  (385, 100), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 50), (180,180,180))
            self.ui.draw_text(f"Score: {self.score}", False,  (510 - (len(str(self.score)) * 10), 280), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 31), (180,180,180))
            self.ui.draw_text("Restart [Space]", False,  (420, 375), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 31), (180,180,180))
            self.ui.draw_text("Exit to Main Menu [Esc]", False,  (340, 440), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 31), (180,180,180))
            self.powerups = [] # gets rid of all powerups
            self.player.laser = [] # gets rid of all leftover lasers on screen as well
            self.play_music('gameover')

            if self.player.player_reset: # player class still alive so it can detect if spacebar is pressed and game needs to be reset
                self.score = 0
                self.__init__(self.difficulty, self.global_music_volume) # restarts game class
            return


        if self.player.health > 0:
            self.ui.draw_shape('rectangle', (20, 25, 300, 25), (240, 40, 40)) # red bar that stays of constant dimensions 
            self.ui.draw_shape('rectangle', (20, 25, self.player.health, 25), (40, 240, 40)) # green bar whose length is dependent on health
        else:
            self.ui.draw_shape('rectangle', (20, 25, 300, 25), (255, 0, 0)) # another red bar if health = 0

        self.ui.draw_text(f"Score: {self.score}", False,  (20, 65), pygame.font.Font(rf"{dir_name}\Fonts\xirod.ttf", 28), (180,180,180))

    def pause_game(self):
        pass

MainMenu()