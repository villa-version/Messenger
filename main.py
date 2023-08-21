import pygame
from socket import socket, AF_INET, SOCK_STREAM
import select


HOST = 'localhost'
PORT = 8432


def connect_server():
    try:
        client = socket(AF_INET, SOCK_STREAM)
        client.connect((HOST, PORT))
        client.setblocking(False)
        return client
    except ConnectionRefusedError:
        print('You were not connected to server.')
        return False


class App:
    width, height = 1024, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Messenger')
    clouds = []
    font_size = 24
    sent = None
    new_msg = ''

    def __init__(self, client):
        self.input_place = PlaceInputText(0, self.height-40, self.width, 40, 24, self.screen)
        self.font = pygame.font.SysFont(pygame.font.get_fonts()[0], self.font_size)
        self.client = client

    def update(self):
        self.draw_elem()
        self.data_operations()

    def draw_elem(self):
        for cloud in self.clouds:
            if -cloud.h < cloud.y < self.height:
                cloud.draw()
        self.input_place.update()

    def get_message(self, msg):
        w, h = 0, self.font.size(msg[0])[1]
        for letter in msg:
            w += self.font.size(letter)[0]
        self.clouds.append(Cloud(50, 2 * (h * len(self.clouds)), w, h,
                                 msg, self.font, self.font_size, self.screen, 'not mine'))

    def send_msg(self):
        w, h = 0, self.font.size(self.input_place.text[0])[1]
        for letter in self.input_place.text:
            w += self.font.size(letter)[0]
        self.clouds.append(Cloud(self.width-w-50, 2*(h*len(self.clouds)), w, h,
                                 self.input_place.text, self.font, self.font_size, self.screen, 'mine'))
        self.new_msg = self.input_place.text
        self.input_place.text = ''
        self.sent = True

    def scrolling(self, dir):
        y = 0
        if dir == 'UP':
            y = -40
        elif dir == 'DOWN':
            y = 40
        for cloud in self.clouds:
            cloud.y += y

    def send_data(self, msg):
        if self.sent:
            self.sent = False
            self.client.send(msg.encode())

    def accept_data(self):
        info_player = ''
        while True:
            response = self.client.recv(1).decode()
            if response == '\n':
                return info_player
            info_player += response

    def data_operations(self):
        try:
            socket_ready_to_read, socket_ready_to_write, _ = select.select([self.client], [self.client], [], 0)
            if self.client in socket_ready_to_write:
                self.send_data(self.new_msg + '\n')
            if self.client in socket_ready_to_read:
                self.get_message(self.accept_data())
        except ConnectionAbortedError:
            self.client.close()


class Cloud:
    def __init__(self, x, y, w, h, text, font, size, screen, type_msg):
        self.x, self.y = x, y
        self.w = w
        self.h = h
        self.font = font
        self.font_size = size
        self.text = text
        self.type = type_msg
        self.app_screen = screen

    def draw(self):
        self.draw_cloud()
        self.draw_text()

    def draw_text(self):
        img = self.font.render(self.text, True, (255, 255, 255))
        self.app_screen.blit(img, (self.x+5, self.y+3))

    def draw_cloud(self):
        pygame.draw.rect(self.app_screen, (0, 0, 0), pygame.Rect(self.x, self.y, self.w+10, self.h+10))


class PlaceInputText:
    def __init__(self, x, y, w, h, font_size, screen):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = ''
        self.font_size = font_size
        self.allow_to_write = False
        self.app_screen = screen

    def update(self):
        self.draw_field()
        self.draw_text()
        self.click_zone()

    def draw_field(self):
        pygame.draw.rect(self.app_screen, (0, 0, 0), pygame.Rect(self.x, self.y, self.w, self.h))
        # pygame.draw.rect(self.app_screen, (255, 255, 255), pygame.Rect(self.x+1, self.y+1, self.w-2, self.h-2))

    def draw_text(self):
        font = pygame.font.SysFont(pygame.font.get_fonts()[0], self.font_size)
        img = font.render(self.text, True, (255, 255, 255))
        self.app_screen.blit(img, (self.x, self.y))

    def click_zone(self):
        mx, my = pygame.mouse.get_pos()
        if self.x < mx < self.x+self.w and self.y < my < self.y+self.h:
            self.allow_to_write = True
        else:
            self.allow_to_write = False


def main():
    pygame.font.init()

    result = connect_server()
    if result is not False:
        app = App(result)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    app.client.close()
                elif event.type == pygame.KEYDOWN:
                    if event.unicode.isalpha() and app.input_place.allow_to_write:
                        app.input_place.text += event.unicode
                    if event.key == pygame.K_SPACE:
                        app.input_place.text += ' '
                    if event.key == pygame.K_BACKSPACE:
                        app.input_place.text = app.input_place.text[:-1]
                    if event.key == pygame.K_RETURN:
                        app.send_msg()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        app.scrolling('UP')
                    elif event.button == 5:
                        app.scrolling('DOWN')

            app.screen.fill((255, 255, 255))
            app.update()
            pygame.display.flip()


if __name__ == '__main__':
    main()

