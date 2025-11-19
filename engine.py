import numpy as np

#GameState represents the state of the board at any instant of time and
class GameState:
    def __init__(self):
        self.board = np.full((8, 8), '--', dtype='<U2')
        white_pieces = ['wr', 'wn', 'wb', 'wq', 'wk', 'wb', 'wn', 'wr']
        black_pieces = ['br', 'bn', 'bb', 'bq', 'bk', 'bb', 'bn', 'br']
        for i in range(8):
            self.board[1][i] = 'bp'
            self.board[6][i] = 'wp'
        self.moveFunctions = {
            'p': self.PawnMoves, 'r': self.RookMoves, 'n': self.KnightMoves,
            'b': self.BishopMoves, 'q': self.QueenMoves, 'k': self.KingMoves
        }
        self.board[7] = white_pieces
        self.board[0] = black_pieces
        self.pins = []
        self.whiteKingPos = (7, 4)
        self.blackKingPos = (0, 4)
        self.checkMate=False
        self.staleMate=False
        self.checks = []
        self.inCheck = False
        self.whiteMove = True
        self.moves = []
        self.possibleEnPassant = ()  # coordinates for square where there can be an en passant (row,col)

        # castling
        self.currentCastleRights = CastleRights(True, True, True, True)
        # CastleRightsLog stores snapshots of CastleRights BEFORE each move so undo can restore
        self.CastleRightsLog = [CastleRights(
            self.currentCastleRights.wks, self.currentCastleRights.wqs,
            self.currentCastleRights.bks, self.currentCastleRights.bqs
        )]

    #Checks if the Check is a Checkmate/Stalemate, needed to win/draw a game
    def CheckForMate(self):
        moves = self.getValid()
        if len(moves)==0:
            if self.inCheck:
                self.checkMate=True
            else:
                self.staleMate=True

    def makeMove(self, move):
        # record castle rights snapshot BEFORE updating (for undo)
        self.CastleRightsLog.append(CastleRights(
            self.currentCastleRights.wks, self.currentCastleRights.wqs,
            self.currentCastleRights.bks, self.currentCastleRights.bqs
        ))

        # move piece
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moves.append(move)
        # flip turn
        self.whiteMove = not self.whiteMove

        # update king position
        if move.pieceMoved == "wk":
            self.whiteKingPos = (move.endRow, move.endCol)
        elif move.pieceMoved == "bk":
            self.blackKingPos = (move.endRow, move.endCol)

        # en passant possible square (store integers)
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.possibleEnPassant = ((move.startRow + move.endRow) // 2, move.endCol)
        else:
            self.possibleEnPassant = ()

        # handle en passant capture
        if move.enPassant:
            # captured pawn is on the startRow of the moving pawn and endCol of move
            if move.pieceMoved[0] == 'w':
                self.board[move.endRow + 1][move.endCol] = "--"
            else:
                self.board[move.endRow - 1][move.endCol] = "--"

        # pawn promotion
        if move.pawnPromotion:
            # allow for input  but default to queen if invalid/no input
            promotedPiece = input("Promote to (q/r/b/n): ").strip().lower()
            mapping = {'q': 'q', 'r': 'r', 'b': 'b', 'n': 'n'}
            pieceChar = mapping.get(promotedPiece, 'q')
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + pieceChar

        # update castling rights because rook/king moved or rook captured
        self.updateCastleRights(move)

        # castling move (move rook accordingly)
        if move.Castling:
            # king-side castle
            if move.endCol - move.startCol == 2:
                # rook moves from (endRow, 7) to (endRow, endCol - 1)
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][7]
                self.board[move.endRow][7] = "--"
            else:
                # queen-side castle: rook from (endRow, 0) to (endRow, endCol + 1)
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][0]
                self.board[move.endRow][0] = "--"

    def undoMove(self):
        if len(self.moves) != 0:
            move = self.moves.pop()
            # restore pieces
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            # flip turn back
            self.whiteMove = not self.whiteMove

            # restore king position
            if move.pieceMoved == "wk":
                self.whiteKingPos = (move.startRow, move.startCol)
            elif move.pieceMoved == "bk":
                self.blackKingPos = (move.startRow, move.startCol)

            # undo en passant
            if move.enPassant:
                # the capturing pawn is moved back; the captured pawn must be restored
                if move.pieceMoved == "wp":
                    # white captured black pawn en passant, black pawn was on endRow+1
                    self.board[move.endRow + 1][move.endCol] = 'bp'
                else:
                    self.board[move.endRow - 1][move.endCol] = 'wp'
                self.board[move.endRow][move.endCol] = "--"
                self.possibleEnPassant = (move.endRow, move.endCol)
            # reset possible en passant if the undone move was the two-square pawn move
            if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
                self.possibleEnPassant = ()

            # undo castling rook movement
            if move.Castling:
                if move.endCol - move.startCol == 2:  # kingside
                    # move rook back from endCol-1 to 7
                    self.board[move.endRow][7] = self.board[move.endRow][move.endCol - 1]
                    self.board[move.endRow][move.endCol - 1] = "--"
                else:  # queenside
                    self.board[move.endRow][0] = self.board[move.endRow][move.endCol + 1]
                    self.board[move.endRow][move.endCol + 1] = "--"

            # restore castling rights from log (last snapshot is the state BEFORE the undone move)
            lastRights = self.CastleRightsLog.pop()
            self.currentCastleRights = CastleRights(lastRights.wks, lastRights.wqs, lastRights.bks, lastRights.bqs)

    def updateCastleRights(self, move):
        # if king moves, lose both castling rights for that colour
        if move.pieceMoved == 'wk':
            self.currentCastleRights.wks = False
            self.currentCastleRights.wqs = False
        elif move.pieceMoved == 'bk':
            self.currentCastleRights.bks = False
            self.currentCastleRights.bqs = False
        # if a rook moves from its original square, lose respective right
        elif move.pieceMoved == 'wr':
            if move.startRow == 7 and move.startCol == 0:
                self.currentCastleRights.wqs = False
            elif move.startRow == 7 and move.startCol == 7:
                self.currentCastleRights.wks = False
        elif move.pieceMoved == 'br':
            if move.startRow == 0 and move.startCol == 0:
                self.currentCastleRights.bqs = False
            elif move.startRow == 0 and move.startCol == 7:
                self.currentCastleRights.bks = False
        # if a rook is captured from original squares, update rights too
        if move.pieceCaptured == 'wr':
            if move.endRow == 7 and move.endCol == 0:
                self.currentCastleRights.wqs = False
            elif move.endRow == 7 and move.endCol == 7:
                self.currentCastleRights.wks = False
        elif move.pieceCaptured == 'br':
            if move.endRow == 0 and move.endCol == 0:
                self.currentCastleRights.bqs = False
            elif move.endRow == 0 and move.endCol == 7:
                self.currentCastleRights.bks = False

    def getValid(self):
        validmoves = []
        self.inCheck, self.pins, self.checks = self.checkPinsChecks()
        if self.whiteMove:
            kingRow, kingCol = self.whiteKingPos
        else:
            kingRow, kingCol = self.blackKingPos
        if self.inCheck:
            if len(self.checks) == 1:  # single check -> block, capture or king move
                validmoves = self.getAllMoves()
                check = self.checks[0]
                checkRow, checkCol = check[0], check[1]
                pieceChecking = self.board[checkRow][checkCol]
                validSquares = []
                if pieceChecking[1] == 'n':
                    validSquares = [(checkRow, checkCol)]
                else:
                    # add squares between king and checking piece (inclusive)
                    for i in range(1, 8):
                        endRow = kingRow + check[2] * i
                        endCol = kingCol + check[3] * i
                        if 0 <= endRow < 8 and 0 <= endCol < 8:
                            validSquares.append((endRow, endCol))
                            print("Valid Square: ", validSquares)
                            if endRow == checkRow and endCol == checkCol:
                                break
                # remove moves that don't block check (except king moves)
                for i in range(len(validmoves) - 1, -1, -1):
                    if validmoves[i].pieceMoved[1] != 'k':
                        if (validmoves[i].endRow, validmoves[i].endCol) not in validSquares:
                            validmoves.remove(validmoves[i])
            else:
                # double check -> only king moves allowed
                self.KingMoves(kingRow, kingCol, validmoves)
        else:
            validmoves = self.getAllMoves()

        return validmoves

    def getAllMoves(self): #All moves that are possible without taking checks & pins into consideration
        allMoves = []
        for i in range(len(self.board)):
            for j in range(len(self.board[i])):
                turn = self.board[i][j][0]
                if (turn == 'w' and self.whiteMove) or (turn == 'b' and not self.whiteMove):
                    piece = self.board[i][j][1]
                    self.moveFunctions[piece](i, j, allMoves) #i and j are starting and ending rows/columns
        return allMoves

    def PawnMoves(self, i, j, allMoves):
        #Pin Logic
        piecePinned = False
        pinDirection = ()
        for k in range(len(self.pins) - 1, -1, -1):
            if self.pins[k][0] == i and self.pins[k][1] == j:
                piecePinned = True
                pinDirection = (self.pins[k][2], self.pins[k][3])
                self.pins.remove(self.pins[k])
                break

        #Pawn Promotion Logic
        if self.whiteMove:
            moveAmount = -1
            startRow = 6
            backRow = 0
            enemyColor = 'b'
        else:
            moveAmount = 1
            startRow = 1
            backRow = 7
            enemyColor = 'w'
        pawnPromotion = False

        # Move Logic
        # One Square Forward
        if 0 <= i + moveAmount < 8 and self.board[i + moveAmount][j] == "--":
            if not piecePinned or pinDirection == (moveAmount, 0):
                if i + moveAmount == backRow:
                    pawnPromotion = True
                allMoves.append(Moves((i, j), (i + moveAmount, j), self.board, pawnPromotion=pawnPromotion))
                # Two Squares from Starting Position
                if i == startRow and self.board[i + 2 * moveAmount][j] == "--":
                    allMoves.append(Moves((i, j), (i + 2 * moveAmount, j), self.board))

        # captures
        if j - 1 >= 0:
            if not piecePinned or pinDirection == (moveAmount, -1):
                if self.board[i + moveAmount][j - 1][0] == enemyColor:
                    if i + moveAmount == backRow:
                        pawnPromotion = True
                    allMoves.append(Moves((i, j), (i + moveAmount, j - 1), self.board, pawnPromotion=pawnPromotion))
                if (i + moveAmount, j - 1) == self.possibleEnPassant:
                    allMoves.append(Moves((i, j), (i + moveAmount, j - 1), self.board, enPassant=True))
        if j + 1 <= 7:
            if not piecePinned or pinDirection == (moveAmount, 1):
                if self.board[i + moveAmount][j + 1][0] == enemyColor:
                    if i + moveAmount == backRow:
                        pawnPromotion = True
                    allMoves.append(Moves((i, j), (i + moveAmount, j + 1), self.board, pawnPromotion=pawnPromotion))
                if (i + moveAmount, j + 1) == self.possibleEnPassant:
                    allMoves.append(Moves((i, j), (i + moveAmount, j + 1), self.board, enPassant=True))

    def RookMoves(self, i, j, allMoves):
        piecePinned = False
        pinDirection = ()
        for k in range(len(self.pins) - 1, -1, -1):
            if self.pins[k][0] == i and self.pins[k][1] == j:
                piecePinned = True
                pinDirection = (self.pins[k][2], self.pins[k][3])
                if self.board[i][j][1] != 'q':  # can't remove queen from pin
                    self.pins.remove(self.pins[k])
                break
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemy = "b" if self.whiteMove else "w"
        for d in directions:
            for a in range(1, 8):
                endRow = i + d[0] * a
                endCol = j + d[1] * a
                if 0 <= endRow < 8 and 0 <= endCol < 8:  # on the board
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            allMoves.append(Moves((i, j), (endRow, endCol), self.board))
                        elif endPiece[0] == enemy:
                            allMoves.append(Moves((i, j), (endRow, endCol), self.board))
                            break
                        else:
                            break
                else:
                    break

    def KnightMoves(self, i, j, allMoves):
        piecePinned = False
        for k in range(len(self.pins) - 1, -1, -1):
            if self.pins[k][0] == i and self.pins[k][1] == j:
                piecePinned = True
                self.pins.remove(self.pins[k])
                break
        directions = ((-1, -2), (-2, -1), (-1, 2), (-2, 1), (1, 2), (2, 1), (1, -2), (2, -1))
        enemy = "b" if self.whiteMove else "w"
        for d in directions:
            endRow = i + d[0]
            endCol = j + d[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                if not piecePinned:
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--" or endPiece[0] == enemy:
                        allMoves.append(Moves((i, j), (endRow, endCol), self.board))

    def BishopMoves(self, i, j, allMoves):
        piecePinned = False
        pinDirection = ()
        for k in range(len(self.pins) - 1, -1, -1):
            if self.pins[k][0] == i and self.pins[k][1] == j:
                piecePinned = True
                pinDirection = (self.pins[k][2], self.pins[k][3])
                self.pins.remove(self.pins[k])
                break
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        enemy = "b" if self.whiteMove else "w"
        for d in directions:
            for a in range(1, 8):
                endRow = i + d[0] * a
                endCol = j + d[1] * a
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            allMoves.append(Moves((i, j), (endRow, endCol), self.board))
                        elif endPiece[0] == enemy:
                            allMoves.append(Moves((i, j), (endRow, endCol), self.board))
                            break
                        else:
                            break
                    else:
                        break

    def QueenMoves(self, i, j, allMoves):
        self.BishopMoves(i, j, allMoves)
        self.RookMoves(i, j, allMoves)

    def KingMoves(self, i, j, allMoves):
        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = "w" if self.whiteMove else "b"
        for k in range(8):
            endRow = i + rowMoves[k]
            endCol = j + colMoves[k]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:  # not an ally
                    # place king on end square and check for checks
                    originalWhiteKing = self.whiteKingPos
                    originalBlackKing = self.blackKingPos
                    if allyColor == 'w':
                        self.whiteKingPos = (endRow, endCol)
                    else:
                        self.blackKingPos = (endRow, endCol)
                    inCheck, pins, checks = self.checkPinsChecks()
                    if not inCheck:
                        allMoves.append(Moves((i, j), (endRow, endCol), self.board))
                    # restore king pos
                    self.whiteKingPos = originalWhiteKing
                    self.blackKingPos = originalBlackKing
        # add castling moves (efficient checks)
        self.getCastleMoves(i, j, allMoves, allyColor)

    def getCastleMoves(self, i, j, allMoves, allyColor):
        # can't castle out of check
        if self.inCheck:
            return
        # king-side
        if (self.whiteMove and self.currentCastleRights.wks) or (not self.whiteMove and self.currentCastleRights.bks):
            self.getKingsideCastleMoves(i, j, allMoves, allyColor)
        # queen-side
        if (self.whiteMove and self.currentCastleRights.wqs) or (not self.whiteMove and self.currentCastleRights.bqs):
            self.getQueensideCastleMoves(i, j, allMoves, allyColor)

    def getKingsideCastleMoves(self, r, c, allMoves, allyColor):
        # squares between king and rook must be empty and not under attack
        if self.board[r][c + 1] == "--" and self.board[r][c + 2] == "--":
            if not self.squareUnderAttack(r, c + 1, allyColor) and not self.squareUnderAttack(r, c + 2, allyColor):
                # ensure rook is at expected square
                rook_piece = self.board[r][7]
                if rook_piece == (allyColor + 'r'):
                    m = Moves((r, c), (r, c + 2), self.board)
                    m.Castling = True
                    allMoves.append(m)

    def getQueensideCastleMoves(self, r, c, allMoves, allyColor):
        # squares between king and rook (queenside) must be empty and not under attack
        if self.board[r][c - 1] == "--" and self.board[r][c - 2] == "--" and self.board[r][c - 3] == "--":
            if not self.squareUnderAttack(r, c - 1, allyColor) and not self.squareUnderAttack(r, c - 2, allyColor):
                rook_piece = self.board[r][0]
                if rook_piece == (allyColor + 'r'):
                    m = Moves((r, c), (r, c - 2), self.board)
                    m.Castling = True
                    allMoves.append(m)

    def squareUnderAttack(self, r, c, allyColor): #with reference to castling, not used for anything else
        enemyColor = "b" if allyColor == "w" else "w"

        # pawn attacks
        pawn_dirs = [(-1, -1), (-1, 1)] if allyColor == "w" else [(1, -1), (1, 1)]
        for d in pawn_dirs:
            row, col = r + d[0], c + d[1]
            if 0 <= row < 8 and 0 <= col < 8:
                if self.board[row][col] == enemyColor + 'p':
                    return True

        # knights
        knight_dirs = [(-2, -1), (-1, -2), (-2, 1), (-1, 2), (1, -2), (2, -1), (1, 2), (2, 1)]
        for d in knight_dirs:
            row, col = r + d[0], c + d[1]
            if 0 <= row < 8 and 0 <= col < 8:
                if self.board[row][col] == enemyColor + 'n':
                    return True

        # rooks, bishops, queens (sliding)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for i, d in enumerate(directions):
            for dist in range(1, 8):
                row, col = r + d[0] * dist, c + d[1] * dist
                if not (0 <= row < 8 and 0 <= col < 8):
                    break
                piece = self.board[row][col]
                if piece == "--":
                    continue
                if piece[0] == allyColor:
                    break
                pieceType = piece[1]
                # straight directions -> rook or queen
                if i < 4 and (pieceType == 'r' or pieceType == 'q'):
                    return True
                # diagonal directions -> bishop or queen, note pawn/king handled elsewhere
                if i >= 4 and (pieceType == 'b' or pieceType == 'q'):
                    return True
                break

        # king (adjacent)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                row, col = r + dr, c + dc
                if 0 <= row < 8 and 0 <= col < 8:
                    if self.board[row][col] == enemyColor + 'k':
                        return True

        return False

    def checkPinsChecks(self):
        pins = []
        checks = []
        inCheck = False
        if self.whiteMove:
            enemyColor = "b"
            allyColor = "w"
            startRow = self.whiteKingPos[0]
            startCol = self.whiteKingPos[1]
        else:
            enemyColor = "w"
            allyColor = "b"
            startRow = self.blackKingPos[0]
            startCol = self.blackKingPos[1]

        directions = [(-1, 0), (0, -1), (1, 0), (0, 1),
                      (-1, -1), (-1, 1), (1, -1), (1, 1)]
        # UP, LEFT, DOWN, RIGHT, UL, UR, DL, DR

        for j in range(len(directions)):
            d = directions[j]
            possiblePin = ()
            for i in range(1, 8):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != 'k':
                        if possiblePin == ():
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else:
                            break
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]
                        if (0 <= j <= 3 and type == 'r') or \
                                (4 <= j <= 7 and type == 'b') or \
                                (i == 1 and type == 'p' and (
                                        (enemyColor == 'w' and 6 <= j <= 7) or
                                        (enemyColor == 'b' and 4 <= j <= 5)
                                )) or \
                                (type == 'q') or \
                                (i == 1 and type == 'k'):
                            if possiblePin == ():
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else:
                                pins.append(possiblePin)
                                break
                        else:
                            break
                else:
                    break

        knightMoves = [(-1, -2), (-2, -1), (-1, 2), (-2, 1),
                       (1, 2), (2, 1), (1, -2), (2, -1)]
        for m in knightMoves:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == "n":
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))

        return inCheck, pins, checks

    def getFEN(self):
        fen = ""
        for row in self.board:
            empty = 0
            for square in row:
                if square == "--":
                    empty += 1
                else:
                    if empty != 0:
                        fen += str(empty)
                        empty = 0
                    piece = square[1]
                    if square[0] == "w":
                        piece = piece.upper()
                    fen += piece
            if empty != 0:
                fen += str(empty)
            fen += "/"
        fen = fen[:-1]  # remove last '/'
        fen += " "
        fen += "w" if self.whiteMove else "b"
        fen += " KQkq - 0 1"  # basic placeholders (you can expand later)
        return fen


class CastleRights:
    def __init__(self, wks, wqs, bks, bqs):
        self.wks = wks
        self.wqs = wqs
        self.bks = bks
        self.bqs = bqs
class Moves:
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    #How the board actually makes moves
    #startSq and endSq are two-dimensional arrays representing the starting and ending square of the piece
    def __init__(self, startSq, endSq, board, enPassant=False, pawnPromotion=False, Castling=False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.enPassant = enPassant
        self.pawnPromotion = pawnPromotion
        self.Castling = Castling
        if enPassant:
            # If enPassant, captured pawn is behind the end square
            self.pieceCaptured = 'bp' if self.pieceMoved == 'wp' else 'wp'

        #Encoding moves to check equality
        self.moveID=self.startRow*1000+self.startCol*100+self.endRow*10+self.endCol

    #Important to check true equality of moves, without it, move objects would literally have to be the same even if they're
    #the same move
    def __eq__(self, other):
        if isinstance(other, Moves):
            return self.moveID==other.moveID
        return False

    def getNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]




def get_best_move_from_stockfish(gs):

    fen = gs.getFEN()
    stockfish.set_fen_position(fen)
    best_move = stockfish.get_best_move()
    return best_move


from stockfish import Stockfish


stockfish = Stockfish(
    path="/Users/michaeltunglut/PycharmProjects/chess/stockfish/stockfish",
    parameters={
        "Threads": 2,
        "Skill Level": 10,
    }
)







