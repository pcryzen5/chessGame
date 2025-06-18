import pygame
import sys
import os
from enum import Enum
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 800
HEIGHT = 600
BOARD_SIZE = 480
SQUARE_SIZE = BOARD_SIZE // 8
BOARD_X = (WIDTH - BOARD_SIZE) // 2
BOARD_Y = (HEIGHT - BOARD_SIZE) // 2

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BROWN = (240, 217, 181)
DARK_BROWN = (181, 136, 99)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)

class PieceType(Enum):
    KING = "king"
    QUEEN = "queen"
    ROOK = "rook"
    BISHOP = "bishop"
    KNIGHT = "knight"
    PAWN = "pawn"

class Color(Enum):
    WHITE = "white"
    BLACK = "black"

class GameMode(Enum):
    TWO_PLAYER = "two_player"
    VS_COMPUTER = "vs_computer"

class Piece:
    def __init__(self, piece_type, color, row, col):
        self.type = piece_type
        self.color = color
        self.row = row
        self.col = col
        self.has_moved = False
        self.image = None
        self.load_image()
    
    def load_image(self):
        """Load piece image from assets folder"""
        try:
            filename = f"{self.color.value}_{self.type.value}.png"
            image_path = os.path.join("assets", filename)
            if os.path.exists(image_path):
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (SQUARE_SIZE - 10, SQUARE_SIZE - 10))
            else:
                # Create a simple colored circle if image not found
                self.image = pygame.Surface((SQUARE_SIZE - 10, SQUARE_SIZE - 10))
                color = (255, 255, 255) if self.color == Color.WHITE else (0, 0, 0)
                pygame.draw.circle(self.image, color, (SQUARE_SIZE//2 - 5, SQUARE_SIZE//2 - 5), 20)
                # Add text for piece type
                font = pygame.font.Font(None, 24)
                text = font.render(self.type.value[0].upper(), True, (255, 0, 0))
                self.image.blit(text, (SQUARE_SIZE//2 - 10, SQUARE_SIZE//2 - 10))
        except:
            # Fallback to simple representation
            self.image = pygame.Surface((SQUARE_SIZE - 10, SQUARE_SIZE - 10))
            color = (255, 255, 255) if self.color == Color.WHITE else (0, 0, 0)
            pygame.draw.circle(self.image, color, (SQUARE_SIZE//2 - 5, SQUARE_SIZE//2 - 5), 20)
            font = pygame.font.Font(None, 24)
            text = font.render(self.type.value[0].upper(), True, (255, 0, 0))
            self.image.blit(text, (SQUARE_SIZE//2 - 10, SQUARE_SIZE//2 - 10))

class ChessBoard:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.current_player = Color.WHITE
        self.selected_piece = None
        self.selected_pos = None
        self.valid_moves = []
        self.game_over = False
        self.winner = None
        self.in_check = False
        self.checkmate = False
        self.stalemate = False
        self.last_move = None  # For en passant
        self.move_history = []  # For castling and game history
        self.move_count = 0  # For fifty-move rule
        self.position_history = []  # For threefold repetition
        self.move_states = []  # For move navigation
        self.current_move_index = -1  # For move navigation
        self.setup_board()
    
    def setup_board(self):
        """Initialize the chess board with pieces"""
        # Place pawns
        for col in range(8):
            self.board[1][col] = Piece(PieceType.PAWN, Color.BLACK, 1, col)
            self.board[6][col] = Piece(PieceType.PAWN, Color.WHITE, 6, col)
        
        # Place other pieces
        piece_order = [PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN,
                      PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK]
        
        for col in range(8):
            self.board[0][col] = Piece(piece_order[col], Color.BLACK, 0, col)
            self.board[7][col] = Piece(piece_order[col], Color.WHITE, 7, col)
    
    def get_piece(self, row, col):
        """Get piece at given position"""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    
    def move_piece(self, from_row, from_col, to_row, to_col):
        """Move piece from one position to another"""
        piece = self.board[from_row][from_col]
        if piece:
            piece.row = to_row
            piece.col = to_col
            piece.has_moved = True
            self.board[to_row][to_col] = piece
            self.board[from_row][from_col] = None
            return True
        return False
    
    def is_valid_move(self, piece, to_row, to_col):
        """Check if a move is valid for the given piece"""
        if not (0 <= to_row < 8 and 0 <= to_col < 8):
            return False
        
        target_piece = self.board[to_row][to_col]
        if target_piece and target_piece.color == piece.color:
            return False
        
        from_row, from_col = piece.row, piece.col
        
        if piece.type == PieceType.PAWN:
            return self.is_valid_pawn_move(piece, to_row, to_col)
        elif piece.type == PieceType.ROOK:
            return self.is_valid_rook_move(from_row, from_col, to_row, to_col)
        elif piece.type == PieceType.BISHOP:
            return self.is_valid_bishop_move(from_row, from_col, to_row, to_col)
        elif piece.type == PieceType.QUEEN:
            return (self.is_valid_rook_move(from_row, from_col, to_row, to_col) or
                   self.is_valid_bishop_move(from_row, from_col, to_row, to_col))
        elif piece.type == PieceType.KING:
            return self.is_valid_king_move(from_row, from_col, to_row, to_col)
        elif piece.type == PieceType.KNIGHT:
            return self.is_valid_knight_move(from_row, from_col, to_row, to_col)
        
        return False
    
    def is_valid_pawn_move(self, piece, to_row, to_col):
        """Check if pawn move is valid"""
        from_row, from_col = piece.row, piece.col
        direction = -1 if piece.color == Color.WHITE else 1
        
        # Forward move
        if from_col == to_col:
            if to_row == from_row + direction and not self.board[to_row][to_col]:
                return True
            # Two squares forward from starting position
            if (not piece.has_moved and to_row == from_row + 2 * direction and 
                not self.board[to_row][to_col] and not self.board[from_row + direction][from_col]):
                return True
        
        # Diagonal capture
        elif abs(from_col - to_col) == 1 and to_row == from_row + direction:
            target_piece = self.board[to_row][to_col]
            if target_piece and target_piece.color != piece.color:
                return True
        
        return False
    
    def is_valid_rook_move(self, from_row, from_col, to_row, to_col):
        """Check if rook move is valid"""
        if from_row != to_row and from_col != to_col:
            return False
        
        # Check path is clear
        if from_row == to_row:
            start, end = min(from_col, to_col), max(from_col, to_col)
            for col in range(start + 1, end):
                if self.board[from_row][col]:
                    return False
        else:
            start, end = min(from_row, to_row), max(from_row, to_row)
            for row in range(start + 1, end):
                if self.board[row][from_col]:
                    return False
        
        return True
    
    def is_valid_bishop_move(self, from_row, from_col, to_row, to_col):
        """Check if bishop move is valid"""
        if abs(from_row - to_row) != abs(from_col - to_col):
            return False
        
        # Check path is clear
        row_step = 1 if to_row > from_row else -1
        col_step = 1 if to_col > from_col else -1
        
        row, col = from_row + row_step, from_col + col_step
        while row != to_row and col != to_col:
            if self.board[row][col]:
                return False
            row += row_step
            col += col_step
        
        return True
    
    def is_valid_king_move(self, from_row, from_col, to_row, to_col):
        """Check if king move is valid"""
        return abs(from_row - to_row) <= 1 and abs(from_col - to_col) <= 1
    
    def is_valid_knight_move(self, from_row, from_col, to_row, to_col):
        """Check if knight move is valid"""
        row_diff = abs(from_row - to_row)
        col_diff = abs(from_col - to_col)
        return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)
    
    def get_valid_moves(self, piece):
        """Get all valid moves for a piece that don't put own king in check"""
        valid_moves = []
        for row in range(8):
            for col in range(8):
                if self.is_valid_move(piece, row, col):
                    # Check if this move would put own king in check
                    if not self.would_be_in_check_after_move(piece, row, col):
                        valid_moves.append((row, col))
        
        # Add castling moves for king
        if piece.type == PieceType.KING and not piece.has_moved:
            castling_moves = self.get_castling_moves(piece)
            valid_moves.extend(castling_moves)
        
        # Add en passant moves for pawns
        if piece.type == PieceType.PAWN:
            en_passant_moves = self.get_en_passant_moves(piece)
            valid_moves.extend(en_passant_moves)
        
        return valid_moves
    
    def would_be_in_check_after_move(self, piece, to_row, to_col):
        """Check if moving a piece would put own king in check"""
        # Save original state
        from_row, from_col = piece.row, piece.col
        captured_piece = self.board[to_row][to_col]
        
        # Make temporary move
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        piece.row, piece.col = to_row, to_col
        
        # Check if king is in check
        in_check = self.is_in_check(piece.color)
        
        # Restore original state
        self.board[from_row][from_col] = piece
        self.board[to_row][to_col] = captured_piece
        piece.row, piece.col = from_row, from_col
        
        return in_check
    
    def get_castling_moves(self, king):
        """Get valid castling moves for the king"""
        moves = []
        if king.has_moved or self.is_in_check(king.color):
            return moves
            
        # Check kingside castling
        if not self.board[king.row][5] and not self.board[king.row][6]:
            rook = self.board[king.row][7]
            if rook and rook.type == PieceType.ROOK and not rook.has_moved:
                if not any(self.would_square_be_attacked(king.row, col, king.color) 
                          for col in range(4, 7)):
                    moves.append((king.row, 6))
                    
        # Check queenside castling
        if not self.board[king.row][1] and not self.board[king.row][2] and not self.board[king.row][3]:
            rook = self.board[king.row][0]
            if rook and rook.type == PieceType.ROOK and not rook.has_moved:
                if not any(self.would_square_be_attacked(king.row, col, king.color) 
                          for col in range(2, 5)):
                    moves.append((king.row, 2))
                    
        return moves
    
    def would_square_be_attacked(self, row, col, defending_color):
        """Check if a square would be attacked by the opponent"""
        opponent_color = Color.BLACK if defending_color == Color.WHITE else Color.WHITE
        
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == opponent_color:
                    if self.is_valid_move(piece, row, col):
                        return True
        return False
    
    def get_en_passant_moves(self, pawn):
        """Get valid en passant moves for a pawn"""
        moves = []
        if not self.last_move:
            return moves
            
        last_piece, last_from, last_to = self.last_move
        if last_piece.type != PieceType.PAWN:
            return moves
            
        # Check if last move was a two-square pawn move
        if abs(last_to[0] - last_from[0]) == 2:
            # Check if this pawn is adjacent to the last moved pawn
            if abs(pawn.col - last_to[1]) == 1 and pawn.row == last_to[0]:
                direction = -1 if pawn.color == Color.WHITE else 1
                moves.append((last_to[0] + direction, last_to[1]))
        
        return moves
    
    def execute_move(self, from_row, from_col, to_row, to_col):
        """Execute a move with all special rules"""
        # Save state before move
        self.move_states = self.move_states[:self.current_move_index + 1]
        self.move_states.append(self.save_board_state())
        self.current_move_index = len(self.move_states) - 1

        piece = self.board[from_row][from_col]
        if not piece:
            return False

        # Save move for en passant
        self.last_move = (piece, (from_row, from_col), (to_row, to_col))
        
        # Handle castling
        if piece.type == PieceType.KING and abs(from_col - to_col) == 2:
            # Determine rook's position and new position
            rook_col = 0 if to_col < from_col else 7
            new_rook_col = 3 if to_col < from_col else 5
            rook = self.board[from_row][rook_col]
            
            # Move rook
            self.board[from_row][new_rook_col] = rook
            self.board[from_row][rook_col] = None
            if rook:
                rook.col = new_rook_col
                rook.has_moved = True

        # Handle en passant capture
        if piece.type == PieceType.PAWN and abs(from_col - to_col) == 1 and not self.board[to_row][to_col]:
            captured_pawn_row = from_row
            self.board[captured_pawn_row][to_col] = None

        # Handle pawn promotion
        if piece.type == PieceType.PAWN and (to_row == 0 or to_row == 7):
            self.board[from_row][from_col] = None
            self.board[to_row][to_col] = Piece(PieceType.QUEEN, piece.color, to_row, to_col)
            piece = self.board[to_row][to_col]
        else:
            # Regular move
            self.board[to_row][to_col] = piece
            self.board[from_row][from_col] = None
            piece.row = to_row
            piece.col = to_col

        piece.has_moved = True
        
        # Update move count for fifty-move rule
        if piece.type == PieceType.PAWN or self.board[to_row][to_col]:
            self.move_count = 0
        else:
            self.move_count += 1
            
        # Update position history for threefold repetition
        self.position_history.append(self.get_board_state())
        
        # Switch player
        self.current_player = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
        
        # Check for check, checkmate, and stalemate
        self.in_check = self.is_in_check(self.current_player)
        if self.in_check:
            if self.is_checkmate(self.current_player):
                self.checkmate = True
                self.game_over = True
                self.winner = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
        elif self.is_stalemate(self.current_player):
            self.stalemate = True
            self.game_over = True
            
        # Check for draw conditions
        if self.check_threefold_repetition() or self.check_fifty_move_rule() or self.check_insufficient_material():
            self.game_over = True
            self.stalemate = True
            
        return True
    
    def is_checkmate(self, color):
        """Check if the given color is in checkmate"""
        if not self.is_in_check(color):
            return False
        
        # Check if any move can get out of check
        pieces = self.get_all_pieces(color)
        for piece in pieces:
            valid_moves = self.get_valid_moves(piece)
            if valid_moves:
                return False
        
        return True
    
    def is_stalemate(self, color):
        """Check if the given color is in stalemate"""
        if self.is_in_check(color):
            return False
        
        # Check if any legal moves available
        pieces = self.get_all_pieces(color)
        for piece in pieces:
            valid_moves = self.get_valid_moves(piece)
            if valid_moves:
                return False
        
        return True
    
    def is_in_check(self, color):
        """Check if the king of given color is in check"""
        # Find the king
        king_pos = None
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.type == PieceType.KING and piece.color == color:
                    king_pos = (row, col)
                    break
        
        if not king_pos:
            return False
        
        # Check if any opponent piece can attack the king
        opponent_color = Color.BLACK if color == Color.WHITE else Color.WHITE
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == opponent_color:
                    if self.is_valid_move(piece, king_pos[0], king_pos[1]):
                        return True
        
        return False
    
    def get_all_pieces(self, color):
        """Get all pieces of a given color"""
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == color:
                    pieces.append(piece)
        return pieces

    def get_board_state(self):
        """Get current board state for threefold repetition"""
        state = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    state.append(f"{piece.color.value}_{piece.type.value}_{row}_{col}")
        return tuple(sorted(state))

    def check_threefold_repetition(self):
        """Check for threefold repetition"""
        current_state = self.get_board_state()
        count = 1
        for state in reversed(self.position_history):
            if state == current_state:
                count += 1
            if count >= 3:
                return True
        return False

    def check_fifty_move_rule(self):
        """Check for fifty-move rule"""
        return self.move_count >= 50

    def check_insufficient_material(self):
        """Check for insufficient material to checkmate"""
        white_pieces = self.get_all_pieces(Color.WHITE)
        black_pieces = self.get_all_pieces(Color.BLACK)
        
        # King vs King
        if len(white_pieces) == 1 and len(black_pieces) == 1:
            return True
            
        # King and Knight vs King
        if len(white_pieces) == 2 and len(black_pieces) == 1:
            if any(p.type == PieceType.KNIGHT for p in white_pieces):
                return True
        if len(black_pieces) == 2 and len(white_pieces) == 1:
            if any(p.type == PieceType.KNIGHT for p in black_pieces):
                return True
                
        # King and Bishop vs King
        if len(white_pieces) == 2 and len(black_pieces) == 1:
            if any(p.type == PieceType.BISHOP for p in white_pieces):
                return True
        if len(black_pieces) == 2 and len(white_pieces) == 1:
            if any(p.type == PieceType.BISHOP for p in black_pieces):
                return True
                
        return False

    def save_board_state(self):
        """Save current board state for move navigation"""
        state = {
            'board': [[None if piece is None else {
                'type': piece.type,
                'color': piece.color,
                'has_moved': piece.has_moved
            } for piece in row] for row in self.board],
            'current_player': self.current_player,
            'last_move': self.last_move,
            'move_count': self.move_count,
            'in_check': self.in_check
        }
        return state

    def load_board_state(self, state):
        """Load a saved board state"""
        for row in range(8):
            for col in range(8):
                piece_data = state['board'][row][col]
                if piece_data is None:
                    self.board[row][col] = None
                else:
                    piece = Piece(piece_data['type'], piece_data['color'], row, col)
                    piece.has_moved = piece_data['has_moved']
                    self.board[row][col] = piece
        
        self.current_player = state['current_player']
        self.last_move = state['last_move']
        self.move_count = state['move_count']
        self.in_check = state['in_check']

class ChessAI:
    def __init__(self, difficulty="medium"):
        self.difficulty = difficulty
    
    def get_move(self, board):
        """Get AI move based on difficulty"""
        pieces = board.get_all_pieces(Color.BLACK)
        valid_moves = []
        
        for piece in pieces:
            moves = board.get_valid_moves(piece)
            for move in moves:
                valid_moves.append((piece, move))
        
        if not valid_moves:
            return None
        
        if self.difficulty == "easy":
            return random.choice(valid_moves)
        elif self.difficulty == "medium":
            return self.get_medium_move(board, valid_moves)
        else:
            return self.get_hard_move(board, valid_moves)
    
    def get_medium_move(self, board, valid_moves):
        """Medium difficulty AI - prefer captures"""
        capture_moves = []
        for piece, (to_row, to_col) in valid_moves:
            if board.board[to_row][to_col]:  # There's a piece to capture
                capture_moves.append((piece, (to_row, to_col)))
        
        if capture_moves:
            return random.choice(capture_moves)
        return random.choice(valid_moves)
    
    def get_hard_move(self, board, valid_moves):
        """Hard difficulty AI - basic strategy"""
        # Prioritize: checkmate > check > capture > development
        best_moves = []
        capture_moves = []
        check_moves = []
        
        for piece, (to_row, to_col) in valid_moves:
            # Simulate move
            original_piece = board.board[to_row][to_col]
            board.board[to_row][to_col] = piece
            board.board[piece.row][piece.col] = None
            piece.row, piece.col = to_row, to_col
            
            # Check if this puts opponent in check
            if board.is_in_check(Color.WHITE):
                check_moves.append((piece, (to_row, to_col)))
            
            # Check if this is a capture
            if original_piece:
                capture_moves.append((piece, (to_row, to_col)))
            
            # Restore board
            board.board[piece.row][piece.col] = None
            board.board[to_row][to_col] = original_piece
            piece.row, piece.col = to_row, to_col
        
        if check_moves:
            return random.choice(check_moves)
        elif capture_moves:
            return random.choice(capture_moves)
        else:
            return random.choice(valid_moves)

class ChessGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess Game")
        self.clock = pygame.time.Clock()
        self.board = ChessBoard()
        self.game_mode = None
        self.ai = None
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.show_move_history = False
        
    def draw_menu(self):
        """Draw the main menu"""
        self.screen.fill(WHITE)
        
        title = self.font.render("Chess Game", True, BLACK)
        title_rect = title.get_rect(center=(WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        # Game mode buttons
        two_player_text = self.font.render("1. Two Player", True, BLACK)
        vs_computer_text = self.font.render("2. vs Computer", True, BLACK)
        
        two_player_rect = two_player_text.get_rect(center=(WIDTH//2, 200))
        vs_computer_rect = vs_computer_text.get_rect(center=(WIDTH//2, 250))
        
        self.screen.blit(two_player_text, two_player_rect)
        self.screen.blit(vs_computer_text, vs_computer_rect)
        
        instructions = self.small_font.render("Press SPACE to start game", True, GRAY)
        inst_rect = instructions.get_rect(center=(WIDTH//2, HEIGHT - 50))
        self.screen.blit(instructions, inst_rect)
    
    def draw_board(self):
        """Draw the chess board"""
        for row in range(8):
            for col in range(8):
                color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
                rect = pygame.Rect(BOARD_X + col * SQUARE_SIZE, BOARD_Y + row * SQUARE_SIZE, 
                                 SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(self.screen, color, rect)
                
                # Highlight selected square
                if self.board.selected_pos == (row, col):
                    pygame.draw.rect(self.screen, GREEN, rect, 3)
                
                # Highlight valid moves
                if (row, col) in self.board.valid_moves:
                    pygame.draw.circle(self.screen, GREEN, 
                                     (BOARD_X + col * SQUARE_SIZE + SQUARE_SIZE//2,
                                      BOARD_Y + row * SQUARE_SIZE + SQUARE_SIZE//2), 10)
    
    def draw_pieces(self):
        """Draw all pieces on the board"""
        for row in range(8):
            for col in range(8):
                piece = self.board.board[row][col]
                if piece and piece.image:
                    x = BOARD_X + col * SQUARE_SIZE + 5
                    y = BOARD_Y + row * SQUARE_SIZE + 5
                    self.screen.blit(piece.image, (x, y))
    
    def draw_game_info(self):
        """Draw game information including current player, check status, and game over conditions"""
        # Draw current player
        player_text = f"Current Player: {self.board.current_player.value.capitalize()}"
        text_surface = self.font.render(player_text, True, BLACK)
        self.screen.blit(text_surface, (20, 20))
        
        # Draw check status
        if self.board.in_check:
            check_text = f"{self.board.current_player.value.capitalize()} is in check!"
            text_surface = self.font.render(check_text, True, RED)
            self.screen.blit(text_surface, (20, 60))
        
        # Draw game over conditions
        if self.board.game_over:
            if self.board.checkmate:
                game_over_text = f"Checkmate! {self.board.winner.value.capitalize()} wins!"
            elif self.board.stalemate:
                if self.board.check_threefold_repetition():
                    game_over_text = "Draw by threefold repetition!"
                elif self.board.check_fifty_move_rule():
                    game_over_text = "Draw by fifty-move rule!"
                elif self.board.check_insufficient_material():
                    game_over_text = "Draw by insufficient material!"
                else:
                    game_over_text = "Stalemate! Game is a draw!"
            else:
                game_over_text = "Game Over!"
            
            text_surface = self.font.render(game_over_text, True, BLUE)
            self.screen.blit(text_surface, (WIDTH // 2 - text_surface.get_width() // 2, 20))
            
            # Draw restart button
            restart_text = "Press R to restart"
            text_surface = self.small_font.render(restart_text, True, BLACK)
            self.screen.blit(text_surface, (WIDTH // 2 - text_surface.get_width() // 2, 60))
        
        # Draw move count for fifty-move rule
        move_text = f"Moves without capture/pawn move: {self.board.move_count}/50"
        text_surface = self.small_font.render(move_text, True, BLACK)
        self.screen.blit(text_surface, (20, HEIGHT - 40))

        # Draw navigation buttons
        back_text = "Back to Menu (B)"
        text_surface = self.small_font.render(back_text, True, BLACK)
        self.screen.blit(text_surface, (WIDTH - 150, 20))

        # Draw move navigation buttons
        if len(self.board.move_states) > 1:
            prev_text = "← Previous Move"
            next_text = "Next Move →"
            text_surface = self.small_font.render(prev_text, True, BLACK)
            self.screen.blit(text_surface, (WIDTH - 150, 50))
            text_surface = self.small_font.render(next_text, True, BLACK)
            self.screen.blit(text_surface, (WIDTH - 150, 80))
    
    def get_square_from_mouse(self, pos):
        """Convert mouse position to board coordinates"""
        x, y = pos
        if BOARD_X <= x < BOARD_X + BOARD_SIZE and BOARD_Y <= y < BOARD_Y + BOARD_SIZE:
            col = (x - BOARD_X) // SQUARE_SIZE
            row = (y - BOARD_Y) // SQUARE_SIZE
            return row, col
        return None
    
    def handle_click(self, pos):
        """Handle mouse click events"""
        # Check if back button is clicked
        if WIDTH - 150 <= pos[0] <= WIDTH - 20 and 20 <= pos[1] <= 40:
            self.game_mode = None
            self.board = ChessBoard()
            return

        # Check if move navigation buttons are clicked
        if len(self.board.move_states) > 1:
            # Previous move button
            if WIDTH - 150 <= pos[0] <= WIDTH - 20 and 50 <= pos[1] <= 70:
                if self.board.current_move_index > 0:
                    self.board.current_move_index -= 1
                    self.board.load_board_state(self.board.move_states[self.board.current_move_index])
                return

            # Next move button
            if WIDTH - 150 <= pos[0] <= WIDTH - 20 and 80 <= pos[1] <= 100:
                if self.board.current_move_index < len(self.board.move_states) - 1:
                    self.board.current_move_index += 1
                    self.board.load_board_state(self.board.move_states[self.board.current_move_index])
                return

        if self.board.game_over:
            return
            
        square = self.get_square_from_mouse(pos)
        if not square:
            return
            
        row, col = square
        clicked_piece = self.board.get_piece(row, col)
        
        # If a piece is already selected
        if self.board.selected_piece:
            # If clicking on a valid move square, make the move
            if (row, col) in self.board.valid_moves:
                self.board.execute_move(self.board.selected_piece.row, 
                                     self.board.selected_piece.col, 
                                     row, col)
                self.board.selected_piece = None
                self.board.valid_moves = []
                
                # If playing against AI and it's AI's turn
                if self.game_mode == GameMode.VS_COMPUTER and self.board.current_player == Color.BLACK:
                    self.ai_move()
            # If clicking on another piece of the same color, select that piece instead
            elif clicked_piece and clicked_piece.color == self.board.current_player:
                self.board.selected_piece = clicked_piece
                self.board.valid_moves = self.board.get_valid_moves(clicked_piece)
            # If clicking on an empty square or enemy piece, deselect current piece
            else:
                self.board.selected_piece = None
                self.board.valid_moves = []
        # If no piece is selected, select a piece if it belongs to current player
        elif clicked_piece and clicked_piece.color == self.board.current_player:
            self.board.selected_piece = clicked_piece
            self.board.valid_moves = self.board.get_valid_moves(clicked_piece)
    
    def ai_move(self):
        """Make AI move"""
        if (self.game_mode == GameMode.VS_COMPUTER and 
            self.board.current_player == Color.BLACK and not self.board.game_over):
            
            move = self.ai.get_move(self.board)
            if move:
                piece, (to_row, to_col) = move
                self.board.execute_move(piece.row, piece.col, to_row, to_col)
                self.board.current_player = Color.WHITE
    
    def run(self):
        """Main game loop"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.board.game_over:
                        self.board = ChessBoard()
                        if self.game_mode == GameMode.VS_COMPUTER:
                            self.ai = ChessAI()
                    elif event.key == pygame.K_1:
                        self.game_mode = GameMode.TWO_PLAYER
                        self.board = ChessBoard()
                    elif event.key == pygame.K_2:
                        self.game_mode = GameMode.VS_COMPUTER
                        self.board = ChessBoard()
                        self.ai = ChessAI()
                    elif event.key == pygame.K_b and self.game_mode:
                        self.game_mode = None
                        self.board = ChessBoard()
                    elif event.key == pygame.K_LEFT and len(self.board.move_states) > 1:
                        if self.board.current_move_index > 0:
                            self.board.current_move_index -= 1
                            self.board.load_board_state(self.board.move_states[self.board.current_move_index])
                    elif event.key == pygame.K_RIGHT and len(self.board.move_states) > 1:
                        if self.board.current_move_index < len(self.board.move_states) - 1:
                            self.board.current_move_index += 1
                            self.board.load_board_state(self.board.move_states[self.board.current_move_index])
            
            self.screen.fill(WHITE)
            
            if not self.game_mode:
                self.draw_menu()
            else:
                self.draw_board()
                self.draw_pieces()
                self.draw_game_info()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = ChessGame()
    game.run()

