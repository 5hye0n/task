import pygame
import random
import sys
import math
#화면 설정
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chacha basketball")
clock = pygame.time.Clock()

player_img = pygame.image.load('sprite/Chacha.png')
ball_img   = pygame.image.load('sprite/basketball.png')

GRAVITY = 0.5
#힘, 각도 초기값
DEFAULT_ANGLE = 45
DEFAULT_POWER = 15
#게임 진행 상태
time_stage = 0
score = 0
miss_count = 0
#차차 이미지 스케일링, 위치 설정 
class Player:
    def __init__(self, pos):
        self.image = pygame.transform.scale(player_img, (80, 110))
        self.rect = self.image.get_rect(midbottom=pos)
    def draw(self, surface):
        surface.blit(self.image, self.rect)
#포물선 궤적 미리 계산
def is_reachable(start_pos, angle, power, hoop_rect):
    x0, y0 = start_pos
    rad = math.radians(angle)
    vx = math.cos(rad) * power
    vy = -math.sin(rad) * power
    x, y = x0, y0
    for _ in range(200):
        vy += GRAVITY
        x += vx; y += vy
        if hoop_rect.collidepoint(int(x), int(y)):
            return True
        if x>WIDTH or y>HEIGHT:
            break
    return False

class Hoop:
    def __init__(self, start_pos, angle, power): self.randomize(start_pos, angle, power)
    def randomize(self, start_pos, angle, power):  #골대 랜덤화
        global time_stage, miss_count
        time_stage += 1; miss_count = 0 #스테이지 올라가면 실패 횟수 리셋
        while True: #계산한 궤적과 동일한 위치면 다른 곳에 생성하도록
            w = random.randint(100,200); h = random.randint(10,20)
            x = random.randint(WIDTH//2+50, WIDTH-50)
            y = random.randint(HEIGHT//4, HEIGHT//2)
            rot = random.uniform(-30,30)
            surf = pygame.Surface((w,h), pygame.SRCALPHA) #타원형 골대
            pygame.draw.ellipse(surf, (255,255,255), surf.get_rect(), 3)
            img = pygame.transform.rotate(surf, rot)
            rect = img.get_rect(center=(x,y))
            if not is_reachable(start_pos, angle, power, rect):
                self.image, self.rect = img, rect; 
                break
        if score >= 20: #20점 이상부터 움직임
            base = 2 + score*0.05
            if time_stage % 2 == 0:
                self.vx, self.vy = base, 0
            else:
                self.vx, self.vy = 0, base
        else:
            self.vx = self.vy = 0
    def update(self):
        if self.vx or self.vy:
            self.rect.x += self.vx; self.rect.y += self.vy
            if self.rect.left < WIDTH//2 or self.rect.right > WIDTH:
                self.vx *= -1
            if self.rect.top < 0 or self.rect.bottom > HEIGHT:
                self.vy *= -1
    def draw(self, surface):
        surface.blit(self.image, self.rect)

class FakeHoop:
    def __init__(self):
        self.randomize()
    def randomize(self):
        w = random.randint(100,200); h = random.randint(10,20)
        x = random.randint(WIDTH//2+50, WIDTH-50)
        y = random.randint(HEIGHT//4, HEIGHT//2)
        rot = random.uniform(-30,30)
        surf = pygame.Surface((w,h), pygame.SRCALPHA) #진짜 골대와 구분짓기 위해 회색으로
        pygame.draw.ellipse(surf, (100,100,100), surf.get_rect(), 3)
        img = pygame.transform.rotate(surf, rot)
        self.image, self.rect = img, img.get_rect(center=(x,y))
    def draw(self, surface): surface.blit(self.image, self.rect)

class Obstacle:
    def __init__(self, hoop_rect):
        self.randomize(hoop_rect)
    def randomize(self, hoop_rect): #장애물 크기 위치 각도 랜덤, 골대를 방해하지 않도록
        w = random.randint(30,60); h = random.randint(30,60)
        x = random.randint(hoop_rect.left-w, hoop_rect.right)
        min_y, max_y = hoop_rect.top, hoop_rect.bottom-h
        if max_y<min_y:
            max_y=min_y
        y = random.randint(min_y, max_y)
        rot = random.uniform(-45,45)
        surf=pygame.Surface((w,h),pygame.SRCALPHA)
        pygame.draw.rect(surf,(200,50,50),surf.get_rect())
        img = pygame.transform.rotate(surf, rot)
        self.image, self.rect = img, img.get_rect(topleft=(x,y))
    def draw(self, s):
        s.blit(self.image, self.rect)
#포물선 궤적을 그리는 공
class Ball:
    def __init__(self,pos,angle,power):
        self.x,self.y=pos
        rad=math.radians(angle)
        self.vx,self.vy=math.cos(rad)*power,-math.sin(rad)*power
        self.active=True
        size=32
        self.image=pygame.transform.scale(ball_img,(32,32))
        self.rect=self.image.get_rect(center=pos)
    def update(self): #중력 적용
        self.vy+=GRAVITY; self.x+=self.vx; self.y+=self.vy
        self.rect.center=(int(self.x),int(self.y))
        if self.y>HEIGHT:
            self.active=False
    def draw(self,s):
        s.blit(self.image,self.rect)
    def get_rect(self):
        return self.rect
#공의 힘, 각도 반영 포물선 궤적 표시
def draw_trajectory(surface,pos,angle,power):  
    x0,y0=pos; rad=math.radians(angle)
    vx,vy=math.cos(rad)*power,-math.sin(rad)*power
    x,y=x0,y0
    for _ in range(15):
        vy+=GRAVITY; x+=vx; y+=vy
        if y>HEIGHT:
            break
        pygame.draw.circle(surface,(200,200,200),(int(x),int(y)),3)

player=Player((100,HEIGHT-10))
hold_pos=(player.rect.right-5,player.rect.top+20)
launch_angle,launch_power=DEFAULT_ANGLE,DEFAULT_POWER
hoop=Hoop(hold_pos,launch_angle,launch_power)
ball=None; obstacles=[]; fake_hoops=[]
font=pygame.font.SysFont(None,36)

running=True
while running:
    clock.tick(60)
    for e in pygame.event.get(): #이벤트 처리
        if e.type==pygame.QUIT: running=False
        if e.type==pygame.KEYDOWN:
            if e.key==pygame.K_RIGHT:
                launch_angle=min(89,launch_angle+1)
            if e.key==pygame.K_LEFT:
                launch_angle=max(1,launch_angle-1)
            if e.key==pygame.K_UP:
                launch_power=min(30,launch_power+1)
            if e.key==pygame.K_DOWN:
                launch_power=max(5,launch_power-1)
            if e.key==pygame.K_SPACE and not ball and miss_count<3:
                ball=Ball(hold_pos,launch_angle,launch_power)
 #공이 발사됐을 때 물리 업데이트 및 충돌 처리
    if ball:
        ball.update()
        r=ball.get_rect()
        #골대 윗면에 닿았을 때 득점 처리
        if r.colliderect(hoop.rect) and ball.y < hoop.rect.top:
            score+=2; ball=None
            hoop.randomize(hold_pos,launch_angle,launch_power) #다음 스테이지 골대 재배치, 장애물 리셋
            obstacles=[]; fake_hoops=[]
            if score>=40:
                obstacles=[Obstacle(hoop.rect) for _ in range(3)]
            if score>=60:
                fake_hoops=[FakeHoop() for _ in range(2)]
        else:
            for o in obstacles: #장애물에 충돌했을 때 공 튀기기
                if r.colliderect(o.rect):
                    ball.vy*=-0.5
                    ball.y=o.rect.top-ball.rect.height//2 if ball.vy<0 else o.rect.bottom+ball.rect.height//2
                    break
            if not ball.active: #공이 화면 하단으로 떨어지면 실점
                miss_count+=1; ball=None

    hoop.update() 
    game_over=(miss_count>=3) #실점이 3이 되면 게임오버

    screen.fill((30,30,30))
    player.draw(screen)
    for o in obstacles:
        o.draw(screen)
    for f in fake_hoops:
        f.draw(screen)
    hoop.draw(screen)
    if not ball:
        preview_ball = pygame.transform.scale(ball_img, (32, 32))
        preview_rect = preview_ball.get_rect(center=hold_pos)
        screen.blit(preview_ball, preview_rect)
        draw_trajectory(screen, hold_pos, launch_angle, launch_power)
    else:
        ball.draw(screen)
#UI 정보
    screen.blit(font.render(f"Score: {score}",True,(255,255,255)),(20,20))
    screen.blit(font.render(f"Stage: {time_stage}",True,(255,255,255)),(20,60))
    screen.blit(font.render(f"Misses: {miss_count}/3",True,(255,100,100)),(20,100))
    screen.blit(font.render(f"Angle: {launch_angle}°",True,(255,255,255)),(20,140))
    screen.blit(font.render(f"Power: {launch_power}",True,(255,255,255)),(20,180))
    if game_over: #게임 오버 화면, 점수 표시
        t=font.render("Game Over!",True,(255,0,0)); screen.blit(t,t.get_rect(center=(WIDTH//2,HEIGHT//2-20)))
        fs=font.render(f"Final Score: {score}",True,(255,255,0)); screen.blit(fs,fs.get_rect(center=(WIDTH//2,HEIGHT//2+20)))

    pygame.display.flip()

pygame.quit()
sys.exit()
