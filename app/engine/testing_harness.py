import pygame
import cProfile

from app.constants import WINWIDTH, WINHEIGHT
from app.shaders import shaders

num_frames = 360

def main():
    pr = cProfile.Profile()
    pygame.init()
    screen_size = (WINWIDTH*2, WINHEIGHT*2)
    screen = pygame.display.set_mode(screen_size)
    surf = pygame.Surface((WINWIDTH, WINHEIGHT))
    img = pygame.image.load('../west_march/west_march.ltproj/resources/panoramas/title_background.png')
    print(img)
    pr.enable()
    for _ in range(num_frames):
        tmp_surf = surf.copy()
        tmp_surf.blit(img, (0, 0))
        shaders.bloom(tmp_surf, 176, True)
        # shaders.invert(tmp_surf)
        pygame.transform.scale(tmp_surf, screen_size, screen)
        pygame.display.update()
    pr.disable()
    pr.print_stats(sort='cumtime')
    pygame.quit()


if __name__ == '__main__':
    main()
