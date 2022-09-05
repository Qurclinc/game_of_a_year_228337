import pygame as pg
import os
import random
import sqlite3
import sys

pg.init()
size = width, height = 1000, 600
screen = pg.display.set_mode(size)
pg.display.set_icon(pg.image.load('data/sprites/1heart.png'))
step = 3
clock = pg.time.Clock()
FONT = pg.font.SysFont('Arial', 32)
COLOR_INACTIVE = (77, 93, 83)
COLOR_ACTIVE = (87, 94, 78)
START = False
CONTROLS = False
END = False
CAN_START = False
SCORES = 0
WIN = False
tick = 0
NAME = ''
PLAYING = False
WHAT = False
ship_top, ship_bottom = None, None

sound_life = pg.mixer.Sound('data/sounds/minusLife.mp3')
sound_dead = pg.mixer.Sound('data/sounds/youDied.mp3')
sound_shot = pg.mixer.Sound('data/sounds/shot.wav')

music_lost = pg.mixer.Sound('data/sounds/youLose.mp3')
music_win = pg.mixer.Sound('data/sounds/youWin.mp3')

sound_life.set_volume(3.5)
sound_dead.set_volume(3.5)
sound_shot.set_volume(3.5)


def load_image(name, colorkey=None):
    fullname = os.path.join('data\sprites', name)
    try:
        image = pg.image.load(fullname)
    except pg.error as e:
        print(e, '\n', type(e))
        print('Невозможно загрузить картинку')
        raise SystemExit(e)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Enemy(pg.sprite.Sprite):
    image = load_image('pirateship.png', -1)
    explosion = load_image('boom.png', -1)
    quantity = 0

    def __init__(self, group):
        super(Enemy, self).__init__(group)
        if WHAT:
            image = load_image('r_rofl.png', -1)
            self.image = image
        else:
            self.image = Enemy.image
        self.rect = self.image.get_rect()
        self.mask = pg.mask.from_surface(self.image)
        self.rect.right, self.rect.top = width, random.randint(0, height - 71)
        self.delta_coord = random.choice([-1, 1, -1.5, 1.5, 0])
        self.shooted = False
        self.destroyed = False
        self.start_sec = 0

    def update(self):
        if self.destroyed:
            self.image = Enemy.explosion
        if not self.destroyed:
            self.rect.left -= 1
            if self.delta_coord:
                if self.rect.bottom >= height or self.rect.top <= 0:
                    self.delta_coord *= -1
                self.rect.top += self.delta_coord
            else:
                if self.rect.top >= ship_top - 10:
                    self.rect.top -= 1
                elif self.rect.bottom <= ship_bottom + 10:
                    self.rect.top += 1
            if self.rect.right <= 0:
                self.kill()
                Enemy.quantity -= 1
                LifeСounter.life_count -= 1

            if self.shooted:
                Bullet(enemy_bullet_sprites, (self.rect.top, self.rect.left), False)
                self.shooted = False
                Bullet.enemy_bullet_number += 1


class Bullet(pg.sprite.Sprite):
    bullet = load_image('bomb.png', -1)
    enemy_bullet = load_image('enemyBullet.png', -1)
    step = 2
    bullet_number = 0
    enemy_bullet_number = 0

    def __init__(self, group, coord, affiliation, point=None):
        Bullet.enemy_bullet_number = 0
        self.affiliation = affiliation
        self.point = point
        if self.affiliation:
            super(Bullet, self).__init__(group)
            if WHAT:
                self.image = load_image('rofl_bullet.png', -1)
            else:
                self.image = Bullet.bullet
            self.rect = self.image.get_rect()
            self.mask = pg.mask.from_surface(self.image)
            self.coord = coord
            self.rect.top, self.rect.left = coord[0] + 25, coord[1] + 73
        else:
            super(Bullet, self).__init__(group)
            if WHAT:
                self.image = load_image('enemy_rofl_bullet.png', -1)
            else:
                self.image = Bullet.enemy_bullet
            self.rect = self.image.get_rect()
            self.mask = pg.mask.from_surface(self.image)
            self.rect.right = coord[1]
            self.rect.top = coord[0] + 24

    def update(self):
        if self.affiliation:
            if self.rect.left < width:
                self.rect.left += Bullet.step
            else:
                self.kill()
                Bullet.bullet_number -= 1
            for sprite in enemy_sprites:
                if pg.sprite.collide_mask(self, sprite):
                    if not sprite.destroyed:
                        self.kill()
                        Bullet.bullet_number -= 1
                        sprite.destroyed = True
                        sprite.start_sec = tick % 60
                        Enemy.quantity -= 1
                        self.point.point_append()
                        sound_shot.play()
            for spr in enemy_bullet_sprites:
                if pg.sprite.collide_mask(self, spr):
                    self.kill()
                    Bullet.bullet_number -= 1
                    spr.kill()
                    Bullet.enemy_bullet_number -= 1
        else:
            if self.rect.right <= 0:
                self.kill()
                Bullet.enemy_bullet_number -= 1
            else:
                self.rect.left -= 2
                for spr in ship_sprite:
                    if pg.sprite.collide_mask(self, spr):
                        self.kill()
                        Bullet.enemy_bullet_number -= 1
                        LifeСounter.life_count -= 1
                        sound_life.play()


class Ship(pg.sprite.Sprite):
    image = load_image('spaceship.png', -1)

    def __init__(self, group):
        super(Ship, self).__init__(group)
        if WHAT:
            image = load_image('rofl.png', -1)
            self.image = image
        else:
            self.image = Ship.image
        self.rect = self.image.get_rect()
        self.mask = pg.mask.from_surface(self.image)
        self.rect.top, self.rect.left = 250, 100
        self.pos = self.rect.top, self.rect.left

    def update(self):
        global ship_top, ship_bottom
        ship_top, ship_bottom = self.rect.top, self.rect.bottom

    def move(self, command):
        if command == 'up':
            if self.rect.top > 5:
                self.rect.top -= step
                self.pos = self.rect.top, self.rect.left
        elif command == 'down':
            if self.rect.bottom < height - 5:
                self.rect.top += step
                self.pos = self.rect.top, self.rect.left
        elif command == 'left':
            if self.rect.left > 5:
                self.rect.left -= step
                self.pos = self.rect.top, self.rect.left
        elif command == 'right':
            if self.rect.right < width / 2 + 50:
                self.rect.left += step
                self.pos = self.rect.top, self.rect.left


class LifeСounter(pg.sprite.Sprite):  # Счетчик жизней

    life_count = 3
    life1 = load_image('1heart.png', -1)
    life2 = load_image('2heart.png', -1)
    life3 = load_image('3heart.png', -1)

    def __init__(self, group):
        super(LifeСounter, self).__init__(group)
        self.image = LifeСounter.life3
        self.rect = self.image.get_rect()
        self.rect.top, self.rect.left = 10, 400
        LifeСounter.life_count = 3

    def update(self):
        if LifeСounter.life_count == 0:
            pass
        if LifeСounter.life_count == 1:
            self.image = LifeСounter.life1
        if LifeСounter.life_count == 2:
            self.image = LifeСounter.life2


class PointsCounter(pg.sprite.Sprite):
    def __init__(self):
        super(PointsCounter, self).__init__()
        self.points = 0
        self.font = pg.font.Font(None, 25)
        self.text = ''

    def point_append(self):
        self.points += 10

    def update(self):
        self.text = self.font.render('Score: ' + str(self.points), True, pg.Color('white'))
        screen.blit(self.text, (250, 20))


class Button:
    def __init__(self, w, h):
        self.width = w
        self.height = h

    def draw(self, x, y, mes, action, xText, yText):
        x += 20
        y += 20
        mouse = pg.mouse.get_pos()
        click = pg.mouse.get_pressed()
        pg.draw.rect(screen, COLOR_INACTIVE, (x, y, self.width, self.height))
        if x < mouse[0] < x + self.width:
            if y < mouse[1] < y + self.height:
                if click[0] == 1 and action is not None:
                    pg.time.delay(300)
                    action()
        print_text(mes, xText, yText, screen, (255, 255, 255), font_size=20)


class InputBox:
    def __init__(self, x, y, w, h, text=''):
        x += 20
        y += 20
        self.rect = pg.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        global CAN_START
        key = pg.key.get_pressed()
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pg.KEYDOWN:
            if self.active:
                if self.text != '':
                    CAN_START = True
                if event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key == pg.K_RETURN or event.key == pg.K_LSHIFT or event.key == pg.K_LCTRL\
                        or key[pg.K_LCTRL] or key[pg.K_LSHIFT]:
                    pass
                else:
                    self.text += event.unicode
                self.txt_surface = FONT.render(self.text, True, self.color)

    def update(self):
        w = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = w

    def draw(self, surf):
        surf.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pg.draw.rect(surf, self.color, self.rect, 2)

    def get_text(self):
        return self.text


def print_text(msg, x, y, surf, font_color=(0, 0, 0), font_type='arial', font_size=30):
    x += 20
    y += 20
    font_type = pg.font.SysFont(font_type, font_size)
    text = font_type.render(msg, True, font_color)
    surf.blit(text, (x, y))


def start_game():
    global CAN_START
    global START
    if CAN_START:
        START = True


def is_back():
    mouse = pg.mouse.get_pos()
    click = pg.mouse.get_pressed()
    if 30 < mouse[0] < 230 and 30 < mouse[1] < 65:
        if click[0] == 1:
            return False
    return True


def exit_game():
    mouse = pg.mouse.get_pos()
    click = pg.mouse.get_pressed()
    if 455 < mouse[0] < 510 and 275 < mouse[1] < 330:
        if click[0] == 1:
            do_exit()
    return True


def retry():
    global END
    mouse = pg.mouse.get_pos()
    click = pg.mouse.get_pressed()
    if 525 < mouse[0] < 580 and 275 < mouse[1] < 330:
        if click[0] == 1:
            END = False
            return False
    return True


def show_controls():
    screen.fill((0, 0, 0))
    running = True
    space = load_image('resized.png')
    arrows = load_image('resized_arrows.png')
    back_btn = load_image('resized_back.png')
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                do_exit()
            running = is_back()
        screen.fill((0, 0, 0))
        screen.blit(space, (220, 350))
        screen.blit(arrows, (270, 285))
        screen.blit(back_btn, (30, 30))
        print_text(' - Shoot', 360, 335, screen, (219, 219, 219), font_size=24)
        print_text(' - Movement', 360, 275, screen, (219, 219, 219), font_size=24)
        pg.display.flip()


def sorted_database():
    way = 'data/database/gamescore.db'
    with sqlite3.connect(way) as con:
        cur = con.cursor()
        dict_names = {}
        leaderboard = {}
        names = [i[0] for i in cur.execute(f'SELECT name FROM players').fetchall()]
        for i in range(len(names)):
            dict_names[i] = names[i]
        scores = [int(i[0]) for i in cur.execute(f'SELECT score FROM scores')]
        for i in range(len(scores)):
            leaderboard[dict_names[i]] = scores[i]
        return [(k, v) for k, v in leaderboard.items()]


def show_table():
    leaders = sorted_database()
    leaders = sorted(leaders, key=lambda x: x[1])[::-1]
    leaders = leaders[:3]

    screen.fill((0, 0, 0))
    running = True
    back_btn = load_image('resized_back.png')
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
            running = is_back()
        screen.fill((0, 0, 0))
        screen.blit(back_btn, (30, 30))
        print_text('Leaderboard', 405, 45, screen, (219, 219, 219), font_size=44)

        print_text('Top #1', 245, 135, screen, (255, 215, 0), font_size=34)
        print_text('Top #2', 245, 210, screen, (192, 192, 192), font_size=34)
        print_text('Top #3', 245, 285, screen, (205, 127, 50), font_size=34)

        print_text(leaders[0][0], 445, 135, screen, (255, 215, 0), font_size=34)
        print_text(leaders[1][0], 445, 210, screen, (192, 192, 192), font_size=34)
        print_text(leaders[2][0], 445, 285, screen, (205, 127, 50), font_size=34)

        print_text(str(leaders[0][1]), 645, 135, screen, (255, 215, 0), font_size=34)
        print_text(str(leaders[1][1]), 645, 210, screen, (192, 192, 192), font_size=34)
        print_text(str(leaders[2][1]), 645, 285, screen, (205, 127, 50), font_size=34)
        pg.display.flip()


def do_exit():
    sys.exit(0)


def record_database():
    global NAME, SCORES
    way = 'data/database/gamescore.db'
    with sqlite3.connect(way) as con:
        cur = con.cursor()
        lst = cur.execute(f'SELECT name FROM players')
        names = [i[0] for i in lst]
        if NAME not in names:
            cur.execute(f"INSERT INTO players (id, name) VALUES ('{len(names)}', '{NAME}')")
        lst = cur.execute(f'SELECT name FROM players')
        id = cur.execute(f"SELECT id FROM players WHERE name = '{NAME}'").fetchall()[0][0]
        ids = [i[0] for i in cur.execute(f'SELECT id FROM scores')]
        if id not in ids:
            cur.execute(f"INSERT INTO scores (id, score) VALUES ('{id}', '{SCORES}')")
        else:
            score = int(cur.execute(f"SELECT score FROM scores WHERE id = '{id}'").fetchall()[0][0])
            if SCORES > score:
                cur.execute(f"REPLACE INTO scores (id, score) VALUES ('{id}', '{SCORES}')")
        con.commit()


def menu():
    global NAME, PLAYING, WHAT
    pg.mixer.music.load('data/sounds/menu.mp3')
    pg.mixer.music.set_volume(0.5)
    if not PLAYING:
        pg.mixer.music.play(-1)
        PLAYING = True

    back = load_image('background.png')
    pg.display.set_caption('Space Breakthrough')
    running = True
    username = InputBox(420, 200, 500, 50)
    start_button = Button(150, 35)
    controls_button = Button(150, 35)
    scores_button = Button(150, 35)
    exit_button = Button(150, 35)
    input_boxes = [username]
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                do_exit()
            if event.type == pg.KEYDOWN:
                key = pg.key.get_pressed()
                if key[pg.K_LCTRL] and key[pg.K_LSHIFT] and key[pg.K_n]:
                    WHAT = True
            if START or CONTROLS or SCORES:
                running = False
            for box in input_boxes:
                box.handle_event(event)
                NAME = box.get_text()

        for box in input_boxes:
            box.update()
        screen.blit(back, (-20, -20))
        for box in input_boxes:
            box.draw(screen)
        print_text('Enter Nickname:', 465, 170, screen, (255, 255, 255), font_size=22)
        start_button.draw(450, 260, 'Start', start_game, 505, 265)
        controls_button.draw(450, 300, 'Show Controls', show_controls, 475, 305)
        scores_button.draw(450, 340, 'Show Scores', show_table, 485, 345)
        exit_button.draw(450, 380, 'Exit', do_exit, 505, 385)
        pg.display.flip()


ship_sprite = pg.sprite.Group()
enemy_bullet_sprites = pg.sprite.Group()
self_bullet_sprites = pg.sprite.Group()
enemy_sprites = pg.sprite.Group()
lifes = pg.sprite.Group()


def main():
    global tick
    pg.mixer.music.load('data/sounds/gameplay.mp3')
    pg.mixer.music.set_volume(0.5)
    pg.mixer.music.play()
    global SCORES, WIN
    fps = 60
    running = True
    pg.display.set_caption('Space Breakthrough')
    ship = Ship(ship_sprite)
    seconds = 90
    points = PointsCounter()
    LifeСounter(lifes)
    main_back = load_image('font.jpg')

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                do_exit()
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                if Bullet.bullet_number < 15:
                    Bullet.bullet_number += 1
                    Bullet(self_bullet_sprites, ship.pos, True, points)
        key = pg.key.get_pressed()
        if key[pg.K_DOWN]:
            ship.move("down")
        if key[pg.K_UP]:
            ship.move("up")
        if key[pg.K_LEFT]:
            ship.move("left")
        if key[pg.K_RIGHT]:
            ship.move("right")
        screen.blit(main_back, (0, 0))

        for enemy in enemy_sprites:
            if pg.sprite.collide_mask(ship, enemy):
                enemy.kill()
                LifeСounter.life_count -= 1

        ship_sprite.draw(screen)
        enemy_bullet_sprites.draw(screen)
        self_bullet_sprites.draw(screen)
        enemy_sprites.draw(screen)
        lifes.draw(screen)

        ship_sprite.update()
        enemy_bullet_sprites.update()
        self_bullet_sprites.update()
        enemy_sprites.update()
        points.update()
        lifes.update()

        if tick % 60 == 0:
            seconds -= 1
            if random.choice([0, 1, 1, 1]):
                if Enemy.quantity < 15:
                    Enemy(enemy_sprites)
                    Enemy.quantity += 1
            for spr in enemy_sprites:
                if random.choice([0, 1, 1]) and Bullet.enemy_bullet_number <= 15 and \
                        spr.rect.left >= width / 2 + 100 and not spr.shooted:
                    spr.shooted = True
        tick += 1
        minute = str(seconds // 60)
        second = str(seconds % 60)
        if int(second) < 10:
            second = f'0{second}'
        print_text(f'Remaining time: {minute}:{second}', 0, 0, screen, (255, 255, 255), None, 25)
        for spr in enemy_sprites:
            if spr.destroyed:
                if (tick % 60) - spr.start_sec < 1:
                    spr.kill()
        pg.display.flip()
        clock.tick(fps)
        if LifeСounter.life_count == 0:
            sound_dead.play()
        if seconds == 0 or LifeСounter.life_count == 0:
            WIN = LifeСounter.life_count
            SCORES = points.points
            running = False

    pg.mixer.music.stop()
    pg.mixer.music.unload()


def end_game():
    global END, SCORES, WIN, NAME
    record_database()
    exit_btn = load_image('exit.png')
    retry_btn = load_image('retry.png')
    running = True
    if WIN:
        music_win.play()
    else:
        music_lost.play()
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                do_exit()
        screen.fill((0, 0, 0))
        if WIN:
            msg = 'YOU WIN'
            color = (0, 255, 0)
        else:
            msg = 'YOU LOSE'
            color = (255, 0, 0)
        print_text(msg, 410, 75, screen, color, None, 52)
        print_text(f'Your score: {SCORES}', 405, 125, screen, (219, 219, 219), None, 40)
        screen.blit(exit_btn, (455, 275))
        screen.blit(retry_btn, (525, 275))
        running = retry()
        exit_game()
        pg.display.flip()
    pg.mixer.music.stop()
    pg.mixer.music.unload()
    pg.quit()


if __name__ == '__main__':
    while not END:
        while not START:
            menu()
            if CONTROLS:
                show_controls()
            elif SCORES:
                show_table()
        pg.mixer.music.stop()
        pg.mixer.music.unload()
        main()
        end_game()
        if END is False:
            pg.init()
            size = width, height = 1000, 600
            screen = pg.display.set_mode(size)
            step = 3
            clock = pg.time.Clock()
            FONT = pg.font.SysFont('Arial', 32)
            COLOR_INACTIVE = (77, 93, 83)
            COLOR_ACTIVE = (87, 94, 78)
            START = False
            CONTROLS = False
            WHAT = False
            END = False
            CAN_START = False
            SCORES = 0
            WIN = False
            tick = 0
            PLAYING = False
            NAME = ''
            ship_top, ship_bottom = None, None
            ship_sprite = pg.sprite.Group()
            enemy_bullet_sprites = pg.sprite.Group()
            self_bullet_sprites = pg.sprite.Group()
            cargo_sprite = pg.sprite.Group()
            enemy_sprites = pg.sprite.Group()
            lifes = pg.sprite.Group()
