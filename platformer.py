import os
import random
import math
import time
import pygame
import sys
from os import listdir
from os.path import isfile, join
from button import Button

pygame.init()
font_big = pygame.font.SysFont('Lucida Sans', 40)
font_small = pygame.font.SysFont('Lucida Sans', 30)

pygame.display.set_caption("Platformer Game")

# global variables needed for setup
WIDTH, HEIGHT = 1920, 1080
FPS = 60
PLAYER_VEL = 7.5
BLOCK_SIZE = 96
OFFSET_X = 0
WIN_CONDITION = False
PLAYER_SCORE = 0
REDRAW = False
# traps and items
FIRE_TRAPS = []
APPLES = []

# create a pygame window instance
window = pygame.display.set_mode((WIDTH, HEIGHT))

def get_font(size):
    return pygame.font.Font("assets/MainMenu/font.ttf", size)

def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, 1, color)
    text_rect = text_obj.get_rect()
    text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)

# flipping sprite images from right to left for moving left
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    # obtain every file/filename inside the directory
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}
    # for every image in the character directory
    for image in images:
        # load the image for every file with a transparent background added
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()        
        sprites = []
        # for every sprite frame in the image
        for i in range(sprite_sheet.get_width() // width):
            # create a game surface to hold an individual animation frame
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            # get the animation frame from the image
            rect = pygame.Rect(i * width, 0, width, height)
            # draw individual sprite frame on the surface then add surface to dictionary
            surface.blit(sprite_sheet, (0, 0), rect)            
            sprites.append(pygame.transform.scale2x(surface))
        
        # adding two keys to each item in the dictionary for both directions
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

# get the dirt block image from the directory
def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    # 96, 0 is top left hand corner of dirt block in image, adjust if needed
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

# represents the player character object and inherits pygame sprites for collision detection
class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1.8
    SPRITES = load_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True)
    ANIMATION_DELAY = 3
    
    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        # for collision
        self.mask = None
        # tracking facing direction to show correct sprite animations
        self.direction = "right"
        self.animation_count = 0
        # how long character has been in the air for (falling and jumping)
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.score = 0
        self.reset = False

    def jump(self):
        self.y_vel = -self.GRAVITY * 6
        self.animation_count = 0
        self.jump_count += 1
        # reset gravity when jumping during first jump only
        if self.jump_count == 1:
            self.fall_count = 0

    # changes the character position based on x/y displacement given
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    # if the player hits a trap, reset position and score
    def make_hit(self):
        self.hit = True
        self.hit_count = 0
        self.rect.x = 100
        self.rect.y = 300
        self.score = 0
        self.fall_count = 0
        self.reset = True

    def move_left(self, vel):
        # left in pygame is a negative value
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self,vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    # called once every frame(while loop run) to manage characters movement/animations/actions 
    def loop(self, fps):
        # increase y acceleration based on time falling and gravity
        self.y_vel += min(1, (self.fall_count / fps) * (self.GRAVITY + 1))
        self.move(self.x_vel, self.y_vel)

        # change hit count if the player is hit to trigger an animation
        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    # if the player lands on an object, reset gravity and stop movement
    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    # if the player hits their head, reverse velocity to move down
    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_score(self):
        self.score += 1

    def update_sprite(self):
        # get the correct sprite images based on the current action
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        # jumping or double jumping if negative velocity (going up)
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        # falling if positive y velocity (going down)
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        # running left or right if non zero x velocity
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction 
        sprites = self.SPRITES[sprite_sheet_name]
        # update sprite animation every 5 frames looping through the images
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    # update rectangle that represents the character based on the sprite showing
    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        # mapping of pixels on the sprite for collision purposes
        self.mask = pygame.mask.from_surface(self.sprite)

    # draw the character on the screen
    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

# base class for all objects in the game
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

# basic block object for the level
class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

# fire object for the level
class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        # update sprite animation every 5 frames looping through the images
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        # mapping of pixels on the sprite for collision purposes
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

# Apple collectable 
class Apple(Object):
    ANIMATION_DELAY = 3
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "apple")
        self.apple = load_sprite_sheets("Items", "Fruits", width, height)
        self.image = self.apple["Apple"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "Apple"
        self.id = 0

    def loop(self):
        sprites = self.apple[self.animation_name]
        # update sprite animation every 5 frames looping through the images
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        # mapping of pixels on the sprite for collision purposes
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

# create a grid of tiles from assets in the background folder
# returns a list of all the background tiles needed to draw/fill the current screen size
def get_background(name):
    # obtain the tile asset image
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []
    # divide screen height/width by tile height/width to get required # of tiles and record positions
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

# draws all of the assets onto the pygame display
def draw(window, background, bg_image, player, objects, offset_x):
    # fill the screen with the background, objects, and player
    for tile in background:
        window.blit(bg_image, tile)
    for obj in objects:
        obj.draw(window, offset_x)
    player.draw(window, offset_x)
    # draw the score
    draw_text("APPLES COLLECTED: " + str(player.score) + "/2", font_big, (255, 255, 255), window, 20, 10)
    draw_text("Collect all apples to complete level.", font_small, (255, 255, 255), window, 20, 55)
    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            # if moving down set bottom of player hitbox to top of object so you stand
            if dy > 0:                
                player.rect.bottom = obj.rect.top
                player.landed()
            # if moving up set top of player to bottom of object to hit head
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)
    return collided_objects

# checking if player would hit the side of a block
def collide(player, objects, dx):
    # move player, check for collison, then move player back to check if the player would move into an object to avoid improper collision
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    player.move(-dx, 0)
    player.update()
    return collided_object
            
# checks keyboard presses,moves character, and checks for collision
def handle_move(player, objects):
    keys = pygame.key.get_pressed()
    player.x_vel = 0
    # check if the player is about to hit the side of a block
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)
    # moving player left or right when pressing A/D
    if keys[pygame.K_a] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    # check for type of object hit
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()
        if obj and obj.name == "apple":
            player.update_score()

# create a section of the level platform
def create_level_platform(block_distance, block_height, num_of_blocks):
    block_size = 96
    platform_objects = []
    for i in range(num_of_blocks):
        print("tes")
        new_block = Block(block_size * (block_distance + i), HEIGHT - block_size * block_height, block_size)
        platform_objects.append(new_block)
    return platform_objects


def create_fire_trap(block_distance, block_height):
    fire_trap = Fire(BLOCK_SIZE*block_distance - 64, (HEIGHT - BLOCK_SIZE - (64 * block_height + 32)), 16, 32)
    fire_trap.on()
    return fire_trap

def create_apple(block_distance, block_height, id):
    apple = Apple(BLOCK_SIZE*block_distance - 64, (HEIGHT - BLOCK_SIZE - (64 * block_height + 32)), 32, 32)
    apple.id = id
    return apple

# main game loop that allows the user to play and restart the game
def main_menu(window, objects):
    running = True
    global WIN_CONDITION
    while running:
        # draw background
        background, bg_image = get_background("Blue.png")
        for tile in background:
            window.blit(bg_image, tile)
        # draw floor
        floor = [Block(i * BLOCK_SIZE, HEIGHT - BLOCK_SIZE, BLOCK_SIZE) for i in range(0, (WIDTH * 2 // BLOCK_SIZE) * 2)]
        for tile in floor:
            tile.draw(window, OFFSET_X)

        MENU_MOUSE_POS = pygame.mouse.get_pos()
        # replace the main menu text with a winning screen if you complete the level
        if WIN_CONDITION:
            MENU_TEXT = get_font(100).render("YOU WIN!", True, "#b68f40")
            MENU_RECT = MENU_TEXT.get_rect(center=(960, 100))

            PLAY_BUTTON = Button(image=pygame.image.load("assets/MainMenu/Play Again Rect.png"), pos=(960, 250), text_input="PLAY MORE", font=get_font(75), base_color="#d7fcd4", hovering_color="White")
            OPTIONS_BUTTON = Button(image=pygame.image.load("assets/MainMenu/Options Rect.png"), pos=(960, 400), text_input="OPTIONS", font=get_font(75), base_color="#d7fcd4", hovering_color="White")
            QUIT_BUTTON = Button(image=pygame.image.load("assets/MainMenu/Quit Rect.png"), pos=(960, 550), text_input="QUIT", font=get_font(75), base_color="#d7fcd4", hovering_color="White")
        else:
            MENU_TEXT = get_font(100).render("MAIN MENU", True, "#b68f40")
            MENU_RECT = MENU_TEXT.get_rect(center=(960, 100))

            PLAY_BUTTON = Button(image=pygame.image.load("assets/MainMenu/Play Rect.png"), pos=(960, 250), text_input="PLAY", font=get_font(75), base_color="#d7fcd4", hovering_color="White")
            OPTIONS_BUTTON = Button(image=pygame.image.load("assets/MainMenu/Options Rect.png"), pos=(960, 400), text_input="OPTIONS", font=get_font(75), base_color="#d7fcd4", hovering_color="White")
            QUIT_BUTTON = Button(image=pygame.image.load("assets/MainMenu/Quit Rect.png"), pos=(960, 550), text_input="QUIT", font=get_font(75), base_color="#d7fcd4", hovering_color="White")

        window.blit(MENU_TEXT, MENU_RECT)

        for button in [PLAY_BUTTON, OPTIONS_BUTTON, QUIT_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(window)
        
        # button handling to play or quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BUTTON.checkForInput(MENU_MOUSE_POS):
                    WIN_CONDITION = play_level_one(window, objects)
                if OPTIONS_BUTTON.checkForInput(MENU_MOUSE_POS):
                    options()
                if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pygame.quit()
                    sys.exit()
        pygame.display.update()


def create_game_objects():
    FIRE_TRAPS.append(create_fire_trap(6, 3.5))
    FIRE_TRAPS.append(create_fire_trap(13, 6.5))
    FIRE_TRAPS.append(create_fire_trap(12, 12.5))
    APPLES.append(create_apple(18.85, 10.25, 1))
    APPLES.append(create_apple(4.85, 12.5, 2))
    # creating a list of blocks that goes left and right of the screen length
    floor = [Block(i * BLOCK_SIZE, HEIGHT - BLOCK_SIZE, BLOCK_SIZE) for i in range(0, (WIDTH * 2 // BLOCK_SIZE) * 2)]
    # consists of the floor and any objects/blocks on the level
    objects = [
        *floor,
        *create_level_platform(1, 5, 2),
        *create_level_platform(4, 3, 2),
        *create_level_platform(7, 5, 2),
        *create_level_platform(11, 5, 3),
        *create_level_platform(15, 6, 2),
        *create_level_platform(18, 7.5, 1),
        *create_level_platform(15, 9, 2),
        *create_level_platform(11, 9, 3),
        *create_level_platform(9, 9, 2),
        *create_level_platform(4, 9, 3),
        *FIRE_TRAPS,
        *APPLES
        ]
    return objects

def play_level_one(window, objects):
    global REDRAW
    clock = pygame.time.Clock()
    # get asset variables
    background, bg_image = get_background("Blue.png")
    player = Player(100, 300, 50, 50)
    removed_objects = []
    scroll_area_width = 300
    apples_removed = 0
    run = True
    while run:
        # set the event loop to run at 60 frames per second
        clock.tick(FPS)
        # close the game and end program if user quits the game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
                break
            # jumping using spacebar
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
        # re-add the collectables to the game if they were collected during last play
        if REDRAW:
            for apple in APPLES:
                objects.append(apple)
            REDRAW = False
        # call loop function on every object to update animations
        player.loop(FPS)
        for fire in FIRE_TRAPS:
            fire.loop()
        for apple in APPLES:
            apple.loop()
        handle_move(player, objects)

        # remove apples if they have been collected from the game
        removed = False
        if player.score != apples_removed:
            for obj in objects:
                if obj.name == "apple" and removed != True:
                    removed_objects.append(obj)
                    objects.remove(obj)
                    apples_removed += 1
                    removed = True

        # reset the level objects that were collected and set score to 0
        if player.hit and player.reset:
            apples_removed = 0
            player.score = 0
            player.reset = False
            for obj in removed_objects:
                objects.append(obj)
            removed_objects.clear()

        # constantly draw the screen objects with an offset to simulate movement
        draw(window, background, bg_image, player, objects, OFFSET_X)

        # change to use global offset if needed later
        # if the player is moving and passes the left or right boundary, increase offset by player speed to simulate a moving background
        #if ((player.rect.right - OFFSET_X >= WIDTH - scroll_area_width) and player.x_vel > 0) or #((player.rect.left - OFFSET_X <= scroll_area_width) and player.x_vel < 0):
        #    OFFSET_X += player.x_vel

        # check if the player has completed the level
        if player.score == 2:
            run = False
            REDRAW = True
        
    return True

def options():
    return None

def main(window):
        # create the main menu and objects
        objects = create_game_objects()
        main_menu(window, objects)

# only run main if main is run from this file directly,not imported
if __name__ == "__main__":
    main(window)
