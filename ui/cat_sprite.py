"""
Sistema visual de la mascota (pixel art).

Responsable de:
- Dibujar el gato
- Manejar animaciones (blink, respiración)
- Cambiar expresiones según estado

Representa la mascota en pantalla.
"""

import math
import random
import pygame

WINDOW_SCALE = 4   
SPRITE_SIZE = 32
SURFACE_WIDTH = SPRITE_SIZE * WINDOW_SCALE    
SURFACE_HEIGHT = SPRITE_SIZE * WINDOW_SCALE   

BLACK = (0, 0, 0)
WHITE = (245, 245, 245)
GRAY = (140, 140, 140)
PINK = (255, 182, 193)

def px(surface, x, y, color=WHITE):
    pygame.draw.rect(
        surface,
        color,
        (x * WINDOW_SCALE, y * WINDOW_SCALE, WINDOW_SCALE, WINDOW_SCALE),
    )


def draw_pixels(surface, pixels, color=WHITE):
    for x, y in pixels:
        px(surface, x, y, color)


def rect_pixels(x, y, w, h):
    return [(px_, py_) for px_ in range(x, x + w) for py_ in range(y, y + h)]


def mirror_pixels(pixels, center_x=15.5):
    return [(int(round(2 * center_x - x)), y) for x, y in pixels]


def get_head_pixels():
    pixels = set()
    for y in range(7, 25):
        if y in (7, 24):
            x1, x2 = 9, 22
        elif y in (8, 23):
            x1, x2 = 7, 24
        elif y in (9, 22):
            x1, x2 = 6, 25
        else:
            x1, x2 = 5, 26
        for x in range(x1, x2 + 1):
            pixels.add((x, y))

    left_ear = [
        (7, 6), (8, 5), (9, 4), (10, 4), (11, 5), (12, 6),
        (8, 6), (9, 5), (10, 5), (11, 6)
    ]
    pixels.update(left_ear)
    pixels.update(mirror_pixels(left_ear))
    return pixels


def get_inner_ear_pixels():
    left = [(9, 6), (10, 6), (10, 7)]
    return left + mirror_pixels(left)


def get_outline_pixels():
    outline = [(5, 20), (4, 20), (5, 21), (4, 22), (5, 22)]
    outline += mirror_pixels(outline)
    return outline


def eyes_neutral():
    return rect_pixels(9, 12, 3, 4) + rect_pixels(20, 12, 3, 4)


def eyes_sleep():
    return rect_pixels(8, 14, 5, 1) + rect_pixels(19, 14, 5, 1)


def eyes_blink():
    return rect_pixels(9, 14, 4, 1) + rect_pixels(19, 14, 4, 1)


def eyes_surprised():
    return rect_pixels(9, 11, 3, 5) + rect_pixels(20, 11, 3, 5)


def eyebrows_angry():
    left = [(8, 8), (9, 9), (10, 10)]
    right = [(21, 10), (22, 9), (23, 8)]
    return left + right


def mouth_neutral():
    return [(15, 19), (16, 18), (17, 19)]


def mouth_happy():
    return [(14, 18), (18, 18), (15, 19), (16, 20), (17, 19)]


def mouth_sad():
    return [(14, 20), (18, 20), (15, 19), (16, 18), (17, 19)]


def mouth_sleep():
    return [(14, 19), (15, 20), (16, 20), (17, 19), (18, 19)]


def mouth_surprised():
    return rect_pixels(15, 18, 2, 4)


def mouth_angry():
    return [(14, 20), (15, 19), (16, 19), (17, 19), (18, 20)]

def eyes_love():
    left = [
        (9, 11), (11, 11),   
        (8, 12), (9, 12), (10, 12), (11, 12), (12, 12),  
        (8, 13), (9, 13), (10, 13), (11, 13), (12, 13),  
        (9, 14), (10, 14), (11, 14),                      
        (10, 15),                                          
    ]
    return left + mirror_pixels(left)

def cheeks():
    left = [(7, 18), (8, 18), (7, 19), (8, 19)]
    return left + mirror_pixels(left)

def eyes_wink():
    return rect_pixels(9, 14, 4, 1) + rect_pixels(20, 12, 3, 4)

def eyes_squint():
    return rect_pixels(9, 13, 3, 2) + rect_pixels(20, 13, 3, 2)

def eyes_halfopen():
    return rect_pixels(8, 14, 5, 1) + rect_pixels(20, 13, 3, 2)

def eyes_lookdown():
    return rect_pixels(9, 14, 4, 1) + rect_pixels(19, 14, 4, 1)

def mouth_nervous():
    return [(14, 19), (15, 18), (16, 19), (17, 18), (18, 19)]

def mouth_smug():
    return [(15, 19), (16, 19), (17, 18), (18, 18)]

def mouth_wavy():
    return [(14, 20), (15, 19), (16, 20), (17, 19), (18, 20)]

def mouth_open_big():
    return rect_pixels(14, 17, 4, 4)

def eyebrow_question():
    return [(21, 10), (22, 10), (22, 11)]

def zzz_pixels():
    return [(24, 8), (26, 7), (24, 6)]

def whiskers():
    left = [(5, 17), (6, 17), (7, 17), (5, 19), (6, 19), (7, 19)]
    return left + mirror_pixels(left)


def nose():
    return [(15, 17), (16, 17), (17, 17)]


def render_cat(expression="neutral"):
    surf = pygame.Surface((SURFACE_WIDTH, SURFACE_HEIGHT))
    surf.fill(BLACK)

    draw_pixels(surf, get_outline_pixels(), GRAY)
    draw_pixels(surf, get_head_pixels(), WHITE)
    draw_pixels(surf, get_inner_ear_pixels(), GRAY)

    draw_pixels(surf, whiskers(), BLACK)
    draw_pixels(surf, nose(), BLACK)

    if expression == "neutral":
        draw_pixels(surf, eyes_neutral(), BLACK)
        draw_pixels(surf, mouth_neutral(), BLACK)
    elif expression == "happy":
        draw_pixels(surf, eyes_neutral(), BLACK)
        draw_pixels(surf, mouth_happy(), BLACK)
    elif expression == "sad":
        draw_pixels(surf, eyes_neutral(), BLACK)
        draw_pixels(surf, mouth_sad(), BLACK)
    elif expression == "sleep":
        draw_pixels(surf, eyes_sleep(), BLACK)
        draw_pixels(surf, mouth_sleep(), BLACK)
        draw_pixels(surf, zzz_pixels(), GRAY)
    elif expression == "blink":
        draw_pixels(surf, eyes_blink(), BLACK)
        draw_pixels(surf, mouth_neutral(), BLACK)
    elif expression == "surprised":
        draw_pixels(surf, eyes_surprised(), BLACK)
        draw_pixels(surf, mouth_surprised(), BLACK)
    elif expression == "angry":
        draw_pixels(surf, eyebrows_angry(), BLACK)
        draw_pixels(surf, eyes_neutral(), BLACK)
        draw_pixels(surf, mouth_angry(), BLACK)
    elif expression == "love":
        draw_pixels(surf, eyes_love(), BLACK)
        draw_pixels(surf, mouth_happy(), BLACK)
        draw_pixels(surf, cheeks(), PINK)
    elif expression == "wink":
        draw_pixels(surf, eyes_wink(), BLACK)
        draw_pixels(surf, mouth_happy(), BLACK)
    elif expression == "confused":
        draw_pixels(surf, eyes_neutral(), BLACK)
        draw_pixels(surf, eyebrow_question(), BLACK)
        draw_pixels(surf, mouth_wavy(), BLACK)
    elif expression == "smug":
        draw_pixels(surf, eyes_squint(), BLACK)
        draw_pixels(surf, mouth_smug(), BLACK)
    elif expression == "nervous":
        draw_pixels(surf, eyes_surprised(), BLACK)
        draw_pixels(surf, mouth_nervous(), BLACK)
    elif expression == "embarrassed":
        draw_pixels(surf, eyes_lookdown(), BLACK)
        draw_pixels(surf, mouth_neutral(), BLACK)
        draw_pixels(surf, cheeks(), PINK)
    elif expression == "sick":
        draw_pixels(surf, eyes_squint(), BLACK)
        draw_pixels(surf, mouth_wavy(), BLACK)
    elif expression == "excited":
        draw_pixels(surf, eyes_surprised(), BLACK)
        draw_pixels(surf, mouth_open_big(), BLACK)
        draw_pixels(surf, cheeks(), PINK)
    elif expression == "happy_blink":
        draw_pixels(surf, eyes_blink(), BLACK)
        draw_pixels(surf, mouth_happy(), BLACK)
    elif expression == "sad_blink":
        draw_pixels(surf, eyes_blink(), BLACK)
        draw_pixels(surf, mouth_sad(), BLACK)
    elif expression == "love_blink":
        draw_pixels(surf, eyes_blink(), BLACK)
        draw_pixels(surf, mouth_happy(), BLACK)
        draw_pixels(surf, cheeks(), PINK)
    elif expression == "confused_blink":
        draw_pixels(surf, eyes_blink(), BLACK)
        draw_pixels(surf, eyebrow_question(), BLACK)
        draw_pixels(surf, mouth_wavy(), BLACK)
    elif expression == "smug_blink":
        draw_pixels(surf, eyes_blink(), BLACK)
        draw_pixels(surf, mouth_smug(), BLACK)
    elif expression == "nervous_blink":
        draw_pixels(surf, eyes_blink(), BLACK)
        draw_pixels(surf, mouth_nervous(), BLACK)
    elif expression == "embarrassed_blink":
        draw_pixels(surf, eyes_blink(), BLACK)
        draw_pixels(surf, mouth_neutral(), BLACK)
        draw_pixels(surf, cheeks(), PINK)
    elif expression == "sick_blink":
        draw_pixels(surf, eyes_blink(), BLACK)
        draw_pixels(surf, mouth_wavy(), BLACK)
    elif expression == "excited_blink":
        draw_pixels(surf, eyes_blink(), BLACK)
        draw_pixels(surf, mouth_open_big(), BLACK)
        draw_pixels(surf, cheeks(), PINK)
    elif expression == "surprised_blink":
        draw_pixels(surf, eyes_blink(), BLACK)
        draw_pixels(surf, mouth_surprised(), BLACK)
    elif expression == "angry_blink":
        draw_pixels(surf, eyebrows_angry(), BLACK)
        draw_pixels(surf, eyes_blink(), BLACK)
        draw_pixels(surf, mouth_angry(), BLACK)
    return surf


class CatAnimator:
    def __init__(self):
        self.mode = "neutral"
        self.manual_override = False

        self.frames = {
            "neutral": [render_cat("neutral"), render_cat("blink"), render_cat("neutral")],
            "happy": [render_cat("happy"), render_cat("happy_blink"), render_cat("happy")],
            "sad": [render_cat("sad"), render_cat("sad_blink"), render_cat("sad")],
            "sleep": [render_cat("sleep")],
            "surprised": [render_cat("surprised"), render_cat("surprised_blink"), render_cat("surprised")],
            "angry": [render_cat("angry") , render_cat("angry_blink"), render_cat("angry")],
            "love":        [render_cat("love"), render_cat("love_blink"), render_cat("love")],
            "wink":        [render_cat("wink")],
            "confused":    [render_cat("confused"), render_cat("confused_blink"), render_cat("confused")],
            "smug":        [render_cat("smug") , render_cat("smug_blink"), render_cat("smug")],
            "nervous":     [render_cat("nervous"), render_cat("nervous_blink"), render_cat("nervous")],
            "embarrassed": [render_cat("embarrassed"), render_cat("embarrassed_blink"), render_cat("embarrassed")],
            "sick":        [render_cat("sick"), render_cat("sick_blink"), render_cat("sick")],
            "excited":     [render_cat("excited"), render_cat("excited_blink"), render_cat("excited")],
        }

        self.current_frame_index = 0
        self.frame_timer = 0
        self.idle_blink_timer = random.randint(120, 240)
        self.is_blinking = False

        self.breath_time = 0.0
        self.breath_speed = 0.040
        self.breath_amplitude = 0.5
        self.breath_offset = 0.0

    def set_mode(self, mode):
        self.mode = mode
        self.manual_override = False  
        self.is_blinking = False
        self.current_frame_index = 0

    def set_idle_mode(self):
        self.manual_override = False
        self.mode = "neutral"

    def trigger_blink(self):
        if self.mode != "sleep":
            self.is_blinking = True
            self.current_frame_index = 0

    def update(self):
        self.breath_time += self.breath_speed

        raw = math.sin(self.breath_time)
        smoothed = math.copysign(abs(raw) ** 0.6, raw)
        self.breath_offset = smoothed * self.breath_amplitude

        if self.mode == "sleep":
            return

        if not self.manual_override:
            self.idle_blink_timer -= 1
            if self.idle_blink_timer <= 0:
                self.is_blinking = True
                self.current_frame_index = 0
                self.idle_blink_timer = random.randint(120, 240)

        if self.is_blinking:
            self.frame_timer += 1
            if self.frame_timer >= 5:
                self.frame_timer = 0
                self.current_frame_index += 1
                if self.current_frame_index >= len(self.frames[self.mode]):
                    self.current_frame_index = 0
                    self.is_blinking = False

    def get_surface(self):
        if self.is_blinking:
            frames = self.frames.get(self.mode, self.frames["neutral"])
            idx = min(self.current_frame_index, len(frames) - 1)
            return frames[idx]
        return self.frames[self.mode][0]