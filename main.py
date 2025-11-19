import pygame as p
import engine

width=height=512
dimension=8
square_size=width//dimension
max_fps=15
images={}

def loadimages():
    pieces=['wp','wr','wn','wb','wq','wk','bp','br','bn','bb','bq','bk']
    for piece in pieces:
        images[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (square_size, square_size))


def main():
    p.init()
    screen=p.display.set_mode((width,height))
    clock=p.time.Clock()
    screen.fill(p.Color("white"))
    gs=engine.GameState()
    validmoves=gs.getValid()
    for move in validmoves:
        print(move.getNotation())
    moveMade=False
    loadimages()
    running=True
    sqSelected =() #last click of user
    playerclicks=[] #keeps track of all user clicks
    gameOver=False
    aiLastMove=None
    while running:
        for e in p.event.get():
            if e.type==p.QUIT:
                running=False
            elif e.type==p.MOUSEBUTTONDOWN:
                location=p.mouse.get_pos()
                col=location[0]//square_size
                row=location[1]//square_size
                if sqSelected==(row,col):
                    sqSelected=()
                    playerclicks=[]
                else:
                    sqSelected = (row, col)
                    playerclicks.append(sqSelected)
                if len(playerclicks)==2:
                    move=engine.Moves(playerclicks[0],playerclicks[1],gs.board)
                    print(move.getNotation())
                    for i in range(len(validmoves)):
                        if move == validmoves[i]:
                            gs.makeMove(validmoves[i])
                            moveMade=True
                            sqSelected=()
                            playerclicks=[]
                    if not moveMade:
                        playerclicks=[sqSelected]
            elif e.type==p.KEYDOWN:
                if e.key==p.K_q:
                    gs.undoMove()
                    moveMade=True
                if e.key==p.K_r:
                    gs=engine.GameState()
                    validmoves=gs.getValid()
                    sqSelected=()
                    playerclicks=[]
                    moveMade=False
        if moveMade:
            validmoves=gs.getValid()
            moveMade=False

            # if not gs.whiteMove:  # assuming white = player, black = AI
            #     ai_move_str = engine.get_best_move_from_stockfish(gs)
            #     if ai_move_str:
            #         start = (8 - int(ai_move_str[1]), ord(ai_move_str[0]) - ord('a'))
            #         end = (8 - int(ai_move_str[3]), ord(ai_move_str[2]) - ord('a'))
            #         ai_move = engine.Moves(start, end, gs.board)
            #         aiLastMove=ai_move
            #         gs.makeMove(ai_move)
            #         moveMade = True

        drawGameState(screen, gs,validmoves,sqSelected,aiLastMove)
        gs.CheckForMate()

        if gs.checkMate:
            gameOver=True
            if gs.whiteMove:
                drawText(screen,'Black Wins by Checkmate')
            else:
                drawText(screen,'White Wins by Checkmate')
        if gs.staleMate:
            gameOver=True
            drawText(screen,'Congratulations, Nobody Wins')
        clock.tick(max_fps)
        p.display.flip()
        # if gameOver:
        #     running = False

def highlightSquares(screen,gs,validmoves,sqSelected):
    if sqSelected!=():
        i,j=sqSelected
        if gs.board[i][j][0]==('w' if gs.whiteMove else 'b'):
            #highlight the selected square
            s=p.Surface((square_size,square_size))
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s,(j*square_size,i*square_size))
            #highlight possible moves from the selected square
            s.fill(p.Color('yellow'))
            for move in validmoves:
                if move.startRow==i and move.startCol==j:
                    screen.blit(s,(square_size*move.endCol,square_size*move.endRow))

def highlightAImoves(screen,move):
    if move is None:
        return
    s=p.Surface((square_size,square_size))
    s.set_alpha(100)
    s.fill(p.Color('orange'))
    screen.blit(s,(square_size*move.startCol,square_size*move.startRow))
    screen.blit(s,(square_size*move.endCol,square_size*move.endRow))



def drawGameState(screen,gs,validMoves,sqSelected,aiLastMove):
    drawBoard(screen)
    highlightSquares(screen,gs,validMoves,sqSelected)
    highlightAImoves(screen,aiLastMove)
    drawPieces(screen,gs.board)

def drawBoard(screen):
    colors=[p.Color("white"),p.Color("dark green")]
    for i in range(dimension):
        for j in range(dimension):
            color=colors[((i+j)%2)]
            p.draw.rect(screen,color,p.Rect(j*square_size,i*square_size,square_size,square_size))

def drawPieces(screen,board):
    for i in range(dimension):
        for j in range(dimension):
            piece=board[i][j]
            if piece!='--':
                screen.blit(images[piece],p.Rect(j*square_size,i*square_size,square_size,square_size))

def drawText(screen,text):
    font=p.font.SysFont("Calibri",32,True,False)
    textObject=font.render(text,0,p.Color('Black'))
    textLocation=p.Rect(0,0,width,height).move(width/2-textObject.get_width()/2,height/2-textObject.get_height()/2)
    screen.blit(textObject,textLocation)
    textObject=font.render(text,0,p.Color('Gold'))
    screen.blit(textObject,textLocation.move(2,2))


if __name__=="__main__":
    main()



