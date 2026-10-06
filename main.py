import pygame
import sys

# Размеры и настройки
TILE_SIZE = 32
ATLAS_TILE_SIZE = 32
SCREEN_W = 1024
SCREEN_H = 720
FPS = 60
ZOOM_STEP = 4
MIN_ZOOM = 8
MAX_ZOOM = 96


# Загружаем карту из файла
def zagruzit_kartu(put_k_failu):
    grid = []
    file = open(put_k_failu, 'r', encoding='utf-8')
    for line in file:
        line = line.strip()
        if line == "":
            continue
        chisla = line.split()
        ryad = []
        for x in chisla:
            ryad.append(int(x))
        grid.append(ryad)
    file.close()
    return grid


# Загружаем атлас тайлов
def zagruzit_atlas(put_k_failu, razmer_tayla):
    atlas = pygame.image.load(put_k_failu).convert_alpha()
    tiles = []
    cols = atlas.get_width() // razmer_tayla
    rows = atlas.get_height() // razmer_tayla
    for r in range(rows):
        for c in range(cols):
            x = c * razmer_tayla
            y = r * razmer_tayla
            rect = pygame.Rect(x, y, razmer_tayla, razmer_tayla)
            tile = atlas.subsurface(rect).copy()
            tiles.append(tile)
    return tiles


# Если tiles.png нет — рисуем простые квадратики
def sdelat_prostoy_atlas(razmer_tayla=32):
    surf = pygame.Surface((razmer_tayla * 4, razmer_tayla), pygame.SRCALPHA)
    colors = [(40, 90, 200), (80, 160, 70), (35, 90, 40), (140, 130, 110)]
    i = 0
    for col in colors:
        rect = pygame.Rect(i * razmer_tayla, 0, razmer_tayla, razmer_tayla)
        pygame.draw.rect(surf, col, rect)
        pygame.draw.rect(surf, (0, 0, 0), rect, 1)
        i = i + 1
    return surf


# Камера — храним позицию, зум, флаг таскания
cam_x = 0.0
cam_y = 0.0
cam_zoom = TILE_SIZE
taskaem = False
poslednaya_mysh = (0, 0)


def ogranichit_kameru(map_w_px, map_h_px):
    global cam_x, cam_y
    world_w = map_w_px * cam_zoom / TILE_SIZE
    world_h = map_h_px * cam_zoom / TILE_SIZE
    min_x = -world_w + SCREEN_W * 0.3
    max_x = SCREEN_W * 0.7
    min_y = -world_h + SCREEN_H * 0.3
    max_y = SCREEN_H * 0.7
    if cam_x < min_x:
        cam_x = min_x
    if cam_x > max_x:
        cam_x = max_x
    if cam_y < min_y:
        cam_y = min_y
    if cam_y > max_y:
        cam_y = max_y


def zum_k_myshke(pozitsiya_myshi, delta):
    global cam_x, cam_y, cam_zoom
    old_zoom = cam_zoom
    cam_zoom = cam_zoom + delta
    if cam_zoom < MIN_ZOOM:
        cam_zoom = MIN_ZOOM
    if cam_zoom > MAX_ZOOM:
        cam_zoom = MAX_ZOOM
    if cam_zoom == old_zoom:
        return
    mx = pozitsiya_myshi[0]
    my = pozitsiya_myshi[1]
    world_x = (mx - cam_x) / old_zoom
    world_y = (my - cam_y) / old_zoom
    cam_x = mx - world_x * cam_zoom
    cam_y = my - world_y * cam_zoom


# Отрисовка карты — только те тайлы, что видно
def narisovat_kartu(screen, grid, tiles):
    map_h = len(grid)
    map_w = len(grid[0])

    start_col = int(-cam_x / cam_zoom) - 1
    if start_col < 0:
        start_col = 0
    end_col = int((SCREEN_W - cam_x) / cam_zoom) + 2
    if end_col > map_w:
        end_col = map_w

    start_row = int(-cam_y / cam_zoom) - 1
    if start_row < 0:
        start_row = 0
    end_row = int((SCREEN_H - cam_y) / cam_zoom) + 2
    if end_row > map_h:
        end_row = map_h

    zoom = int(cam_zoom)

    for row in range(start_row, end_row):
        for col in range(start_col, end_col):
            tile_idx = grid[row][col]
            if tile_idx < 0:
                continue
            if tile_idx >= len(tiles):
                continue

            tile_img = tiles[tile_idx]

            if zoom != ATLAS_TILE_SIZE:
                tile_img = pygame.transform.scale(tile_img, (zoom, zoom))

            sx = col * cam_zoom + cam_x
            sy = row * cam_zoom + cam_y
            screen.blit(tile_img, (sx, sy))

    # Сеточка
    if zoom >= 24:
        for col in range(start_col, end_col + 1):
            x = col * cam_zoom + cam_x
            pygame.draw.line(screen, (0, 0, 0), (x, 0), (x, SCREEN_H))
        for row in range(start_row, end_row + 1):
            y = row * cam_zoom + cam_y
            pygame.draw.line(screen, (0, 0, 0), (0, y), (SCREEN_W, y))


# Мини-карта
def narisovat_minikartu(screen, grid):
    mm_w = 200
    mm_h = 150
    mm_x = SCREEN_W - mm_w - 10
    mm_y = SCREEN_H - mm_h - 10

    pygame.draw.rect(screen, (20, 20, 20), (mm_x, mm_y, mm_w, mm_h))

    map_h = len(grid)
    map_w = len(grid[0])
    cell_w = mm_w / map_w
    cell_h = mm_h / map_h

    colors = [(40, 90, 200), (80, 160, 70), (35, 90, 40), (140, 130, 110)]

    for r in range(map_h):
        for c in range(map_w):
            idx = grid[r][c]
            col = colors[idx % 4]
            x = mm_x + c * cell_w
            y = mm_y + r * cell_h
            pygame.draw.rect(screen, col, (x, y, cell_w + 0.5, cell_h + 0.5))

    pygame.draw.rect(screen, (255, 255, 255), (mm_x, mm_y, mm_w, mm_h), 1)

    view_w = SCREEN_W / cam_zoom * cell_w
    view_h = SCREEN_H / cam_zoom * cell_h
    view_x = mm_x + (-cam_x / cam_zoom) * cell_w
    view_y = mm_y + (-cam_y / cam_zoom) * cell_h
    pygame.draw.rect(screen, (255, 255, 0),
                     (view_x, view_y, view_w, view_h), 1)


def main():
    global cam_x, cam_y, cam_zoom, taskaem, poslednaya_mysh

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Моя стратегия")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 14)

    print("Загружаю карту...")
    grid = zagruzit_kartu("map.txt")
    map_h = len(grid)
    map_w = len(grid[0])
    print("Карта загружена:", map_w, "x", map_h)

    # Пытаемся загрузить tiles.png
    try:
        tiles = zagruzit_atlas("tiles.png", ATLAS_TILE_SIZE)
        print("tiles.png загружен")
    except:
        print("Не нашёл tiles.png, рисую свои квадратики")
        atlas = sdelat_prostoy_atlas(ATLAS_TILE_SIZE)
        tiles = []
        i = 0
        while i < 4:
            rect = pygame.Rect(i * ATLAS_TILE_SIZE, 0,
                               ATLAS_TILE_SIZE, ATLAS_TILE_SIZE)
            tiles.append(atlas.subsurface(rect).copy())
            i = i + 1

    map_w_px = map_w * TILE_SIZE
    map_h_px = map_h * TILE_SIZE

    running = True
    while running == True:
        dt = clock.tick(FPS) / 1000.0

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    taskaem = True
                    poslednaya_mysh = event.pos
                elif event.button == 4:
                    zum_k_myshke(event.pos, ZOOM_STEP)
                    ogranichit_kameru(map_w_px, map_h_px)
                elif event.button == 5:
                    zum_k_myshke(event.pos, -ZOOM_STEP)
                    ogranichit_kameru(map_w_px, map_h_px)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    taskaem = False
            elif event.type == pygame.MOUSEMOTION:
                if taskaem == True:
                    mx = event.pos[0]
                    my = event.pos[1]
                    dx = mx - poslednaya_mysh[0]
                    dy = my - poslednaya_mysh[1]
                    cam_x = cam_x + dx
                    cam_y = cam_y + dy
                    poslednaya_mysh = (mx, my)
                    ogranichit_kameru(map_w_px, map_h_px)

        # Клавиатура для движения
        keys = pygame.key.get_pressed()
        speed = 400 * dt
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            cam_x = cam_x + speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            cam_x = cam_x - speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            cam_y = cam_y + speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            cam_y = cam_y - speed
        ogranichit_kameru(map_w_px, map_h_px)

        # Рисуем
        screen.fill((15, 15, 20))
        narisovat_kartu(screen, grid, tiles)
        narisovat_minikartu(screen, grid)

        info = font.render("Зум: " + str(int(cam_zoom)) +
                           " | ЛКМ — тащить, колесо — зум, WASD — двигать",
                           True, (255, 255, 255))
        screen.blit(info, (10, 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()