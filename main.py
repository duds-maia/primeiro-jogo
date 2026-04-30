import pygame # pyright: ignore[reportMissingImports]
import random
import sys
import json
import os

# CONFIGURAÇÕES GERAIS DO JOGO

pygame.init()

LARGURA = 800
ALTURA = 600
TAMANHO_BLOCO = 20

# Paleta de Cores
COR_FUNDO = (30, 30, 30)       # Cinza escuro
COR_COBRA = (50, 205, 50)      # Verde Neon
COR_BORDA_COBRA = (0, 100, 0)  # Verde escuro
COR_COMIDA = (255, 69, 0)      # Laranja avermelhado
COR_TEXTO = (240, 240, 240)    # Branco suave
COR_GAMEOVER = (220, 20, 60)   # Vermelho Crimson

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_RANKING = os.path.join(DIRETORIO_ATUAL, 'ranking.json')

def obter_nome_usuario(tela, fonte):
    nome = ""
    ativo = True
    while ativo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN:
                    if nome.strip() != "":
                        ativo = False
                elif evento.key == pygame.K_BACKSPACE:
                    nome = nome[:-1]
                else:
                    if len(nome) < 15: # Limita o nome a 15 caracteres
                        nome += evento.unicode
                        
        tela.fill(COR_FUNDO)
        texto_titulo = fonte.render("Digite seu nome e aperte ENTER:", True, COR_TEXTO)
        texto_nome = fonte.render(nome + "_", True, COR_COMIDA)
        
        tela.blit(texto_titulo, (LARGURA//2 - texto_titulo.get_width()//2, ALTURA//2 - 50))
        tela.blit(texto_nome, (LARGURA//2 - texto_nome.get_width()//2, ALTURA//2 + 10))
        pygame.display.update()
        
    return nome.strip()

def gerenciar_ranking(nome, pontuacao):
    ranking = []
    if os.path.exists(ARQUIVO_RANKING):
        with open(ARQUIVO_RANKING, 'r', encoding='utf-8') as f:
            try:
                ranking = json.load(f)
            except json.JSONDecodeError:
                ranking = []
                
    jogador_existente = None
    for registro in ranking:
        if registro["nome"] == nome:
            jogador_existente = registro
            break
            
    if jogador_existente:
        if pontuacao > jogador_existente["pontuacao"]:
            jogador_existente["pontuacao"] = pontuacao
    else:
        jogador_existente = {"nome": nome, "pontuacao": pontuacao}
        ranking.append(jogador_existente)
        
    # Ordena do maior para o menor com base na pontuação
    ranking.sort(key=lambda x: x["pontuacao"], reverse=True)
    
    # Pega o índice do registro e soma 1 para obter a colocação
    colocacao = ranking.index(jogador_existente) + 1
    
    with open(ARQUIVO_RANKING, 'w', encoding='utf-8') as f:
        json.dump(ranking, f, ensure_ascii=False, indent=4)
        
    return ranking, colocacao

# CLASSES

class Cobra:
    def __init__(self):
        self.resetar()
        self.cor = COR_COBRA

    def get_cabeca(self):
        return self.posicoes[0]

    def virar(self, direcao_x, direcao_y):
        # Impede que a cobra dê ré nela mesma
        if self.tamanho > 1 and (direcao_x * -1, direcao_y * -1) == self.direcao:
            return
        self.direcao = (direcao_x, direcao_y)

    def mover(self):
        atual = self.get_cabeca()
        x, y = self.direcao
        novo = (atual[0] + (x * TAMANHO_BLOCO), atual[1] + (y * TAMANHO_BLOCO))
        
        # Lógica de Colisão com as Paredes
        if novo[0] < 0 or novo[0] >= LARGURA or novo[1] < 0 or novo[1] >= ALTURA:
            return False # Retorna Falso indicando Game Over

        # Lógica de Colisão com o Próprio Corpo
        if len(self.posicoes) > 2 and novo in self.posicoes[2:]:
            return False # Retorna Falso indicando Game Over

        # Insere a nova posição da cabeça
        self.posicoes.insert(0, novo)
        
        # Remove a cauda se não comeu a maçã (mantém o tamanho)
        if len(self.posicoes) > self.tamanho:
            self.posicoes.pop()
            
        return True

    def resetar(self):
        self.tamanho = 1
        self.posicoes = [(LARGURA // 2, ALTURA // 2)]
        self.direcao = (0, -1) # Começa subindo

    def desenhar(self, superficie):
        for p in self.posicoes:
            retangulo = pygame.Rect((p[0], p[1]), (TAMANHO_BLOCO, TAMANHO_BLOCO))
            pygame.draw.rect(superficie, self.cor, retangulo)
            pygame.draw.rect(superficie, COR_BORDA_COBRA, retangulo, 1)

class Comida:
    def __init__(self):
        self.cor = COR_COMIDA
        self.posicao_aleatoria()

    def posicao_aleatoria(self):
        # Garante que a comida spawne alinhada com o grid da cobra
        x = random.randint(0, (LARGURA - TAMANHO_BLOCO) // TAMANHO_BLOCO) * TAMANHO_BLOCO
        y = random.randint(0, (ALTURA - TAMANHO_BLOCO) // TAMANHO_BLOCO) * TAMANHO_BLOCO
        self.posicao = (x, y)

    def desenhar(self, superficie):
        retangulo = pygame.Rect((self.posicao[0], self.posicao[1]), (TAMANHO_BLOCO, TAMANHO_BLOCO))
        pygame.draw.rect(superficie, self.cor, retangulo)


# LOOP PRINCIPAL DO JOGO

def main():
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption('Projeto: Snake Game Orientado a Objetos')
    relogio = pygame.time.Clock()
    
    # Fontes
    fonte_hud = pygame.font.SysFont('consolas', 24)
    fonte_gameover = pygame.font.SysFont('consolas', 48, bold=True)
    fonte_ranking = pygame.font.SysFont('consolas', 20)

    # Pede o nome do jogador antes do jogo começar
    nome_jogador = obter_nome_usuario(tela, fonte_hud)

    cobra = Cobra()
    comida = Comida()

    pontuacao = 0
    velocidade_base = 12
    game_over = False
    salvou_ranking = False
    ranking_atual = []
    colocacao_atual = 0

    while True:
        # Captura de Eventos do Teclado e Sistema
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif evento.type == pygame.KEYDOWN:
                if game_over:
                    # Aperte 'Espaço' para reiniciar
                    if evento.key == pygame.K_SPACE:
                        cobra.resetar()
                        comida.posicao_aleatoria()
                        pontuacao = 0
                        game_over = False
                        salvou_ranking = False
                    # Aperte 'N' para reiniciar com um novo usuário
                    elif evento.key == pygame.K_n:
                        nome_jogador = obter_nome_usuario(tela, fonte_hud)
                        cobra.resetar()
                        comida.posicao_aleatoria()
                        pontuacao = 0
                        game_over = False
                        salvou_ranking = False
                else:
                    if evento.key == pygame.K_UP or evento.key == pygame.K_w:
                        cobra.virar(0, -1)
                    elif evento.key == pygame.K_DOWN or evento.key == pygame.K_s:
                        cobra.virar(0, 1)
                    elif evento.key == pygame.K_LEFT or evento.key == pygame.K_a:
                        cobra.virar(-1, 0)
                    elif evento.key == pygame.K_RIGHT or evento.key == pygame.K_d:
                        cobra.virar(1, 0)

        # Atualização da Lógica
        if not game_over:
            # Se a função mover retornar False, ocorreu uma colisão
            if not cobra.mover():
                game_over = True

            # Checa se a cobra alcançou a comida
            if cobra.get_cabeca() == comida.posicao:
                cobra.tamanho += 1
                pontuacao += 10
                
                # Impede que a comida nasça dentro do corpo da cobra
                comida.posicao_aleatoria()
                while comida.posicao in cobra.posicoes:
                    comida.posicao_aleatoria()

        # Renderização (Desenhar na tela)
        tela.fill(COR_FUNDO)
        
        cobra.desenhar(tela)
        comida.desenhar(tela)

        # Desenhar HUD de Pontuação
        texto_pontos = fonte_hud.render(f'Pontuação: {pontuacao}', True, COR_TEXTO)
        tela.blit(texto_pontos, (15, 15))

        # Desenhar Tela de Game Over
        if game_over:
            # Salva no arquivo apenas na primeira vez que a tela de game over é renderizada
            if not salvou_ranking:
                ranking_atual, colocacao_atual = gerenciar_ranking(nome_jogador, pontuacao)
                salvou_ranking = True

            texto_go = fonte_gameover.render('GAME OVER', True, COR_GAMEOVER)
            texto_restart_mesmo = fonte_hud.render('ESPAÇO - Jogar novamente', True, COR_TEXTO)
            texto_restart_novo = fonte_hud.render('N - Novo jogador', True, COR_TEXTO)
            
            tela.blit(texto_go, (LARGURA//2 - texto_go.get_width()//2, ALTURA//4 - 50))
            tela.blit(texto_restart_mesmo, (LARGURA//2 - texto_restart_mesmo.get_width()//2, ALTURA//4 + 10))
            tela.blit(texto_restart_novo, (LARGURA//2 - texto_restart_novo.get_width()//2, ALTURA//4 + 40))
            
            # Exibir a lista do Ranking e a Colocação do Jogador
            texto_titulo_ranking = fonte_hud.render('--- RANKING TOP 5 ---', True, COR_COMIDA)
            tela.blit(texto_titulo_ranking, (LARGURA//2 - texto_titulo_ranking.get_width()//2, ALTURA//2 - 20))
            
            y_offset = ALTURA//2 + 20
            for i, rank in enumerate(ranking_atual[:5]):
                texto_rank = fonte_ranking.render(f"{i+1}º - {rank['nome']} : {rank['pontuacao']} pts", True, COR_TEXTO)
                tela.blit(texto_rank, (LARGURA//2 - texto_rank.get_width()//2, y_offset))
                y_offset += 30
                
            texto_colocacao = fonte_hud.render(f'Sua colocação atual: {colocacao_atual}º lugar!', True, COR_COBRA)
            tela.blit(texto_colocacao, (LARGURA//2 - texto_colocacao.get_width()//2, y_offset + 10))

        pygame.display.update()

        # Controle de FPS (Dificuldade aumenta 1 "tick" a cada 50 pontos)
        velocidade_atual = velocidade_base + (pontuacao // 50)
        relogio.tick(velocidade_atual)

if __name__ == '__main__':
    main()