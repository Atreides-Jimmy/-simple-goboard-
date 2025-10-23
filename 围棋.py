import pygame
import time
from functimer import outer

#棋盘、棋子
class Go_Board:
    def __init__(self,screen):
        self.image = pygame.image.load('./材料/棋盘.png') #928*934,左上角坐标为（41，45），间隔约为47
        self.screen = screen
        self.stones = {(i,j):"empty" for i in range(1,20) for j in range(1, 20)}
        self.black_stone = pygame.image.load('./材料/黑子.png')  # 22*24
        self.white_stone = pygame.image.load('./材料/白子.png')

    def display(self):
        self.screen.blit(self.image, (0, 0))
        for coord in self.stones.keys():
            if self.stones[coord] == "black":
                self.screen.blit(self.black_stone, (45 + (coord[0] - 1) * 47 - 22 / 2, 45 + (coord[1] - 1) * 47 - 24 / 2))
            if self.stones[coord] == "white":
                self.screen.blit(self.white_stone, (45 + (coord[0] - 1) * 47 - 22 / 2, 45 + (coord[1] - 1) * 47 - 24 / 2))


class Judge:
    def __init__(self,screen):
        self.screen = screen

    def near_stones(self,x,y,stones):
        near = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        for coord in near[::]:
            if coord not in stones.keys():
                near.remove(coord)
        return near

    def chunk_near_stones(self,chunk,stones):
        nears = set()
        for coord in chunk:
            for near in self.near_stones(coord[0],coord[1],stones):
                if near not in chunk:
                    nears.add(near)
        return list(nears)

    def chunk_proliferation(self,little_chunk,stones):
        start = len(little_chunk)
        nears = self.chunk_near_stones(little_chunk,stones)
        for coord in nears:
            if stones[coord] == stones[little_chunk[0]]:
                little_chunk.append(coord)
        if len(little_chunk) > start:
            return True
        else:
            return False

    def chunk_proliferations(self,x,y,stones):
        chunk = [(x,y)]
        while self.chunk_proliferation(chunk,stones):
            pass
        return chunk

    #去除棋盘中的空位置,得到有棋子的坐标列表
    def empty_remove(self,stones):
        temp_stones = list(stones.keys())
        for coord in stones.keys():
            if stones[coord] == 'empty':
                temp_stones.remove(coord)
        return temp_stones

    # 分子入库
    def fzrk(self,stones):
        temp_stones = self.empty_remove(stones)
        chunks = []
        while len(temp_stones) > 0:
            _ = self.chunk_proliferations(*temp_stones[-1],stones)
            chunks.append(_)
            for coord in _:
                temp_stones.remove(coord)
        return chunks

    #全局同行判定(只往前回溯10次加快速度)
    def qjtx(self,x,y,color,stones,records):
        if_added = stones.copy()
        if_added[(x, y)] = color
        self.sizi_remove(color,if_added)
        for record in records[-1:-11:-1]:
            if if_added == record and not self.suicide(x,y,color,stones):
                print('全局同形！')
                return True
        return False

    #全包围
    def qbw(self,chunk,stones):
        nears = self.chunk_near_stones(chunk,stones)
        for coord in nears:
            if stones[coord] == 'empty':
                return False
        return True

    #绝对死子
    def sizi(self,stones):
        all_qbw = []
        chunks = self.fzrk(stones)
        if chunks:
            for chunk in chunks:
                if self.qbw(chunk,stones):
                    all_qbw.append(chunk)
        return all_qbw

    #提取死子
    def sizi_remove(self,color,stones):
        if self.sizi(stones):
            for dead in self.sizi(stones):
                if stones[list(dead)[0]] != color:
                    for dead_stone in dead:
                        stones[dead_stone] = 'empty'

    #落子后造成自己的一块棋没气了
    def suicide(self,x,y,color,stones):
        if_added = stones.copy()
        if_added[(x, y)] = color
        if len(self.sizi(if_added)) == 1:
            if if_added[list(self.sizi(if_added)[0])[0]] == color:
                print('suicide!')
                return True
        return False

    #判断落子是否合法
    def is_legalstep(self,pos,color,stones,history,records):
        for position in stones:
            if (stones[position] == 'empty'
                    and 41 + (position[0]-1)*47 - 20 < pos[0] < 41 + (position[0]-1)*47 + 20
                    and 45 + (position[1]-1)*47 - 20 < pos[1] < 45 + (position[1]-1)*47 + 20):
                pos = position
                if not self.qjtx(pos[0],pos[1],color,stones,records) and not self.suicide(pos[0],pos[1],color,stones):
                    records.append(stones.copy())
                    stones[pos] = color
                    history.append(pos)
                    self.sizi_remove(color,stones)

    #下一手该谁落子
    def which_color_next(self,his_num:int):
        if his_num % 2 == 0:
            color_next = 'black'
        else:
            color_next = 'white'
        return color_next

class GameSound(object):
    def __init__(self):
        pygame.mixer.init() #音乐模块初始化
        pygame.mixer.music.load(('./材料/The One You Love - Glenn Frey.mp3')) #导入背景音乐
        pygame.mixer.music.set_volume(0.5) #声音大小

    def playBackgroundMusic(self):
        pygame.mixer.music.play(-1) #开始播放音乐

class Manager:
    go_board_size = (928,934)
    def __init__(self):
        pygame.init()
        # 创建窗口
        self.screen = pygame.display.set_mode(Manager.go_board_size, 0, 32)
        #导入棋盘
        self.go_board = Go_Board(self.screen)
        self.history = []
        self.records = []
        self.judge = Judge(self.screen)
        # 初始化一个声音播放的对象
        self.sound = GameSound()
        self.game_state = '进行中'

    # 绘制文字
    def drawText(self, text, x, y, textHeight=30, fontColor=(255, 0, 0), backgroundColor=None):
        # 通过字体文件获取字体对象
        font_obj = pygame.font.Font('./材料/喵字摄影体.ttf', textHeight) #选择下载好的字体
        # 配置要显示的文字
        text_obj = font_obj.render(text, True, fontColor, backgroundColor)
        # 获取要显示的对象的rect
        text_rect = text_obj.get_rect()
        # 设置显示对象坐标
        text_rect.topleft = (x, y)
        # 绘制字到指定区域
        self.screen.blit(text_obj, text_rect)

    #记录棋局,black:○;empty:+;white:●
    def record(self,stones,history):
        date = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())
        with open(f'record\\{date}.txt', 'w') as f:
            f.write(f'{date}对局记录\n')
            f.write("棋局 ：\n")
            for i in range(1,20):
                seq =''
                for j in range(1,20):
                    if stones[(j,i)] == 'empty':
                        seq += "+" + " "*2
                    elif stones[(j,i)] == 'black':
                        seq += "○" + " "*2
                    else:
                        seq += "●" + " "*2
                f.write(seq + '\n')
            f.write('落子位置历史记录 ： \n')
            for i in range(1,len(history)//5):
                f.write(str(5*i - 4) + ':' + str(history[5*i - 4 - 1]) +' '*2 +
                        str(5*i - 3) + ':' + str(history[5*i - 3 - 1]) + ' ' * 2 +
                        str(5*i - 2) + ':' + str(history[5*i - 2 - 1]) + ' ' * 2 +
                        str(5*i - 1) + ':' + str(history[5*i - 1 - 1]) + ' ' * 2 +
                        str(5*i) + ':' + str(history[5*i - 0 - 1]) + '\n')
            for i in range(1 + 5*len(history)//5,1+len(history)):
                seq = ''
                seq += str(i) + ':' + str(history[i-1])
                f.write(seq + '\n')
            # f.write(str(stones) + '\n') #选择是否要写入棋盘字典

    #结束一局游戏并刷新
    def gameover(self):
        if self.game_state != '进行中':
            self.drawText(self.game_state,928/2-70,934/2-100/2,fontColor=(225,0,0))
            pygame.display.update()
            time.sleep(1.5)
            self.record(self.go_board.stones,self.history)
            self.go_board.stones = {(i,j):"empty" for i in range(1,20) for j in range(1, 20)}
            self.history.clear()
            self.game_state = '进行中'

    #认输
    def submit(self,color):
        if len(self.history) <= 4:
            self.drawText('少于4手棋，不得投子！', 928 / 2 - 80, 934 / 2 - 30 / 2 + 50, fontColor=(255, 0, 0))
            pygame.display.update()
            time.sleep(1)
        else:
            self.game_state = '游戏结束！'
            self.drawText(color + '投子！', 928 / 2 - 80, 934 / 2 - 30 / 2 + 50, fontColor=(0, 0, 255))
            pygame.display.update()
            time.sleep(1)
            self.gameover()

    #悔棋
    def regret(self):
        if not self.history:
            self.drawText('未落子，无法悔棋！', 928 / 2 - 80, 934 / 2 - 30 / 2, fontColor=(0, 0, 255))
            pygame.display.update()
            time.sleep(1)
        else:
            self.go_board.stones = self.records[-1]
            self.records.pop()
            self.history.pop()

    #停一手
    def step_giveup(self):
        self.history.append((-1,-1))
        self.records.append(self.go_board.stones)

    def main(self):
        self.sound.playBackgroundMusic()
        running = True
        while running:
            self.go_board.display()
            self.drawText('悔棋', 0, 934 - 35, textHeight=30, fontColor=(0, 255, 0), backgroundColor=(0, 0, 0))
            self.drawText('认输', 928-60, 934 - 35, textHeight=30, fontColor=(0, 255, 0), backgroundColor=(0, 0, 0))
            self.drawText('停一手', 928/2 - 30, 934 - 35, textHeight=30, fontColor=(0, 255, 0), backgroundColor=(0, 0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.gameover()
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 获取鼠标点击位置的像素坐标
                    last_click_pos = pygame.mouse.get_pos()
                    if 0 < last_click_pos[0] < 50 and 934-30 < last_click_pos[1] < 934:
                        self.regret()
                    elif 928-60 < last_click_pos[0] < 928 and 934-30 < last_click_pos[1] < 934:
                        self.submit(self.judge.which_color_next(len(self.history)))
                    elif 928/2-30 < last_click_pos[0] < 928/2 + 30 and 934-30 < last_click_pos[1] < 934:
                        self.step_giveup()
                    else:
                        color_then = self.judge.which_color_next(len(self.history))
                        self.judge.is_legalstep(last_click_pos,color_then,self.go_board.stones,self.history,self.records)

            pygame.display.update()
            time.sleep(0.01)

if __name__ == '__main__':
    manager = Manager()
    manager.main()
