import chess
import chess.pgn
import io

KASPAROV_PGN = """1. e4 d6 2. d4 Nf6 3. Nc3 g6 4. Be3 Bg7 5. Qd2 c6 6. f3 b5 7. Nge2 Nbd7 8. Bh6 Bxh6 9. Qxh6 Bb7 10. a3 e5 11. O-O-O Qe7 12. Kb1 a6 13. Nc1 O-O-O 14. Nb3 exd4 15. Rxd4 c5 16. Rd1 Nb6 17. g3 Kb8 18. Na5 Ba8 19. Bh3 d5 20. Qf4+ Ka7 21. Rhe1 d4 22. Nd5 Nbxd5 23. exd5 Qd6 24. Rxd4 cxd4 25. Re7+ Kb6 26. Qxd4+ Kxa5 27. b4+ Ka4 28. Qc3 Qxd5 29. Ra7 Bb7 30. Rxb7 Qc4 31. Qxf6 Kxa3 32. Qxa6+ Kxb4 33. c3+ Kxc3 34. Qa1+ Kd2 35. Qb2+ Kd1 36. Bf1 Rd2 37. Rd7 Rxd7 38. Bxc4 bxc4 39. Qxh8 Rd3 40. Qa8 c3 41. Qa4+ Ke1 42. f4 f5 43. Kc1 Rd2 44. Qa7 1-0"""

CUSTOM_DIALOGUES = {
    1: ("OPENING THEORY: King's Pawn Opening (1. e4)", "I open with King's Pawn to e4, staking out the center and opening lines for the Queen and Bishop."),
    2: ("COUNTER-THEORY: Pirc Defense (Hypermodern)", "I respond with d6, initiating the flexible and counter-punching Pirc Defense."),
    3: ("OPENING THEORY: Classical Center Occupation", "d4. Establishing full classical dominance over the central squares."),
    4: ("DEVELOPMENT: Kingside Knight Deployment", "Knight to f6, developing and pressuring White's advanced e4 pawn."),
    5: ("DEVELOPMENT: Defending e4 with Harmony", "Knight to c3, naturally protecting e4 and maintaining central integrity."),
    6: ("FIANCHETTO PREPARATION: Pirc King's Walk", "g6, preparing to fianchetto my dark-squared bishop along the long diagonal."),
    7: ("AGGRESSIVE SETUP: English Attack Bishop Development", "Bishop to e3! Preparing Qd2 and queenside castling for a sharp attacking race."),
    8: ("FIANCHETTO BISHOP: Dominating the Long Diagonal", "Bishop to g7. My dragon bishop breathes fire across the central light squares."),
    9: ("BATTERY ALIGNMENT: Queen & Bishop Target h6", "Queen to d2! Setting up a battery targeting the dark-squared bishop on g7."),
    10: ("QUEENSIDE PREPARATION: The c6 Counter-Stroke", "c6, preparing an aggressive queenside pawn expansion with b5."),
    11: ("PAWN CHAIN DEFENSE: Solidifying the Center", "f3! Cementing the e4 pawn and taking away the g4 square from Black's knight."),
    12: ("PAWN EXPANSION: Rolling the Queenside Flank", "b5! Expanding on the queenside to challenge White's spatial control."),
    13: ("KNIGHT REDIRECTION: Rerouting via e2", "Knight to e2. Rerouting the kingside knight toward the active c1 and b3 outposts."),
    14: ("QUEENSIDE REINFORCEMENT: Flexible Knight Placement", "Knight to d7, reinforcing the center while keeping lines open for the b7 bishop."),
    15: ("DARK SQUARE ASSAULT: Trading the Defensive Bishop", "Bishop to h6! Offering to trade off Black's key defensive fianchetto bishop."),
    16: ("BISHOP EXCHANGE: Eliminating the Infiltrator", "Bishop takes h6. Accepting the trade, though my king's dark squares are slightly weakened."),
    17: ("QUEEN INFILTRATION: Dominating the h6 Outpost", "Queen takes h6! Infiltrating the dark squares and preventing Black from castling kingside."),
    18: ("BISHOP ACTIVATION: Placing the Sniper on b7", "Bishop to b7, taking up a powerful post on the long diagonal."),
    19: ("PROPHYLAXIS: Restricting Queenside Expansion", "a3. Restraining the further advance of Black's queenside pawns."),
    20: ("CENTER STRIKE: Contesting the E-file", "e5! Striking at White's central pawn chain and fighting for central space."),
    21: ("QUEENSIDE CASTLING: King Safety & Rook Activation", "Queenside Castling! King to safety, and the d-file rook is mobilized for battle."),
    22: ("TACTICAL PREPARATION: Queen Coordinates Defense", "Queen to e7, connecting the rooks and preparing queenside castling."),
    23: ("PROPHYLAXIS: King Steps Off the Open File", "King to b1! The hallmark of grandmaster prophylaxis, stepping off the open c-file."),
    24: ("PREPARING OPPOSITE CASTLING: King Solidification", "a6, preparing to shelter the king on the queenside opposite White."),
    25: ("KNIGHT MANEUVER: Rerouting toward b3", "Knight to c1! Heading for b3 to establish an impregnable central post."),
    26: ("QUEENSIDE CASTLING: King Seeks Haven", "Queenside Castling! Both kings are castled on opposite wings. The battle is raging!"),
    27: ("OUTPOST OCCUPATION: Knight to b3", "Knight to b3, applying pressure against the d4 square and monitoring c5."),
    28: ("CENTRAL TENSION: Pawns Clash on d4", "e takes d4. Liquidating central tension to open lines for counterplay."),
    29: ("ROOK CENTRALIZATION: Dominating the 4th Rank", "Rook takes d4! Centralizing the rook actively along the open central highway."),
    30: ("PAWN CHASE: Kicking the Central Rook", "c5! Hitting the active rook and expanding space on the queenside."),
    31: ("TACTICAL RETREAT: Rook to d1", "Rook retreats to d1, maintaining vertical laser pressure along the d-file."),
    32: ("KNIGHT ADVANCE: Targeting the Center", "Knight to b6, eyeing the c4 outpost and adding pressure on White's queenside."),
    33: ("KINGSIDE PAWN MOBILIZATION: Preparing g4", "g3. Preparing a kingside expansion while solidifying the f4 break."),
    34: ("KING SAFETY: King to b8", "King to b8, an essential prophylactic step to safety behind the pawn shield."),
    35: ("KNIGHT INVASION: Seizing the a5 Outpost", "Knight to a5! Planting a monster knight deep inside Black's queenside territory."),
    36: ("BISHOP RETREAT: Preserving the Long Diagonal", "Bishop to a8, preserving the bishop pair and keeping pressure on the diagonal."),
    37: ("BISHOP ACTIVATION: Placing the Bishop on h3", "Bishop to h3! Pinning Black's pieces and reinforcing the d7 square."),
    38: ("CENTRAL BREAKTHROUGH: d5 Counter-Strike", "d5! Striking the center open! Black is fighting with ferocious tenacity."),
    39: ("QUEEN CHECK: Delivering the Tactical Check", "Queen to f4 check! Penetrating Black's defenses and seizing the initiative!"),
    40: ("KING EVASION: King to a7", "King to a7, finding safe shelter behind the pawns while avoiding check."),
    41: ("ROOK MOBILIZATION: Seizing the Open e-file", "Rook from h1 to e1! Centralizing all four major pieces. White's army is fully mobilized."),
    42: ("PAWN PUSH: d4 Wedge", "d4! Pushing the pawn to cramp White's knight and restrict the central files."),
    43: ("TACTICAL OUTPOST: Knight Infiltrates d5", "Knight to d5! Embedding a dominant octopus knight right into Black's camp!"),
    44: ("KNIGHT TRADE: Eliminating the Octopus Knight", "Knight takes d5. Black cannot allow this monster to remain on the board."),
    45: ("PAWN RECAPTURE: Clamping Down the Position", "e takes d5! Opening the e-file and establishing a lethal passed pawn."),
    46: ("QUEEN CENTRALIZATION: Queen to d6", "Queen to d6, centralizing the queen and eyeing White's weaknesses."),
    47: ("!! THE IMMORTAL ROOK SACRIFICE (Rxd4!!)", "Rook takes d4!! A thunderous, immortal piece sacrifice! Giving up a full rook to shatter Black's central king shelter!"),
    48: ("ACCEPTING THE SACRIFICE: c takes d4", "c takes d4. Accepting the sacrifice, but the board is exploding into total tactical chaos!"),
    49: ("!! SECOND ROOK SACRIFICE (Re7+!!)", "Rook to e7 check!! Unbelievable! The second consecutive rook sacrifice! Driving the Black King into the open board!"),
    50: ("KING EVASION: King Flees to b6", "King to b6! The King is forced to flee into the open queenside crossfire!"),
    51: ("QUEEN CHECK: Driving the King Out", "Queen takes d4 check! The hunt is on! Every square around the King is burning!"),
    52: ("FORCED MARCH: King Walks to a5", "King takes a5! Forced to capture the knight, marching deep into White's territory!"),
    53: ("PAWN CHECK: The Golden Cage (b4+)", "b4 check! Sealing the exits! The Black King is trapped on the edge of the abyss!"),
    54: ("KING STEP: King to a4", "King to a4. The King is on a4—an extraordinary sight in Grandmaster chess!"),
    55: ("QUEEN INFILTRATION: Setting Up Mating Net", "Queen to c3! Threatening unstoppable checkmate in two moves!"),
    56: ("DESPERATE INTERVENTION: Queen Captures d5", "Queen takes d5, desperately trying to shield the king with counter-tactics."),
    57: ("ROOK REVENGE: Rook to a7!", "Rook to a7! Pinning Black's bishop and threatening instant destruction!"),
    58: ("DEFENSIVE BISHOP: Bishop Blocks on b7", "Bishop to b7, shielding the back rank with the last remaining minor piece."),
    59: ("ROOK TAKE BISHOP: Slicing the Shield", "Rook takes b7! Liquidating the defender with surgical precision!"),
    60: ("QUEEN COUNTER-ATTACK: Queen to c4", "Queen to c4! Offering a queen trade to relieve the crushing mating net."),
    61: ("DECLINING QUEEN TRADE: Infiltrating f6", "Queen takes f6! Ignoring the trade and threatening a lethal queen checkmate!"),
    62: ("KING PAWN GRAB: King Takes a3", "King takes a3! The King captures the pawn, completely alone in the storm!"),
    63: ("QUEEN CHECK: Queen to a6 Check", "Queen takes a6 check! Driving the King further into the corner!"),
    64: ("KING RETREAT: King Takes b4", "King takes b4, capturing every pawn in a desperate bid for survival!"),
    65: ("PAWN CHECK: c3 Check", "c3 check! Closing the walls around the King!"),
    66: ("KING CAPTURE: King Takes c3", "King takes c3! The King has captured three pawns and a knight!"),
    67: ("QUEEN CHECK: Queen to a1 Check", "Queen to a1 check! Driving the King down to the second rank!"),
    68: ("KING ESCAPE: King to d2", "King to d2, fleeing across the back ranks."),
    69: ("QUEEN CHECK: Queen to b2 Check", "Queen to b2 check! Hitting the King from every angle!"),
    70: ("KING EVASION: King to d1", "King to d1. Fleeing into the first rank!"),
    71: ("BISHOP INTERVENTION: Bishop to f1 Check", "Bishop to f1! Driving the final nail into Black's coffin!"),
    72: ("ROOK INTERVENTION: Rook Blocks on d2", "Rook to d2, desperately blocking the check."),
    73: ("ROOK PIN: Rook to d7!", "Rook to d7! Pinning the rook against the Queen!"),
    74: ("ROOK TAKE ROOK: Liquidating Pieces", "Rook takes d7, eliminating White's active rook."),
    75: ("BISHOP CAPTURE: Bishop Takes Queen", "Bishop takes c4! Winning the Queen and restoring total material domination!"),
    76: ("PAWN RECAPTURE: b takes c4", "b takes c4. Recapturing, but White's queen and rooks are completely dominant."),
    77: ("QUEEN HARVEST: Queen Takes h8", "Queen takes h8! Harvesting Black's corner rook!"),
    78: ("ROOK COUNTERPLAY: Rook to d3", "Rook to d3, attempting a final desperate counter-attack."),
    79: ("QUEEN REPOSITION: Queen to a8", "Queen to a8! Preventing Black's pawn from promoting!"),
    80: ("PAWN PUSH: c3 Advance", "c3, pushing the passed pawn forward."),
    81: ("QUEEN CHECK: Queen to a4 Check", "Queen to a4 check! Restricting the king to the first rank!"),
    82: ("KING STEP: King to e1", "King to e1, trapped in the corner pocket."),
    83: ("PAWN SHIELD: f4 Advance", "f4! Locking down the kingside pawns permanently."),
    84: ("PAWN ADVANCE: f5 Advance", "f5! Pushing the pawns in a final effort."),
    85: ("KING SAFETY: King to c1", "King to c1! Completely freezing Black's pawns from advancing!"),
    86: ("ROOK CHECK: Rook to d2", "Rook to d2. The last move before the curtains close."),
    87: ("IMMORTAL CONCLUSION: Queen to a7 1-0", "Queen to a7! Black resigns! Garry Kasparov wins the greatest game in chess history! What an absolute masterpiece!")
}

def get_kasparov_game_moves():
    pgn_io = io.StringIO(KASPAROV_PGN)
    game = chess.pgn.read_game(pgn_io)
    board = chess.Board()
    moves = []
    for i, m in enumerate(game.mainline_moves(), 1):
        san = board.san(m)
        uci = m.uci()
        player = "White" if board.turn == chess.WHITE else "Black"
        board.push(m)
        strat, dial = CUSTOM_DIALOGUES.get(i, ("GRANDMASTER TACTICS", f"{san}. Playing with supreme precision."))
        moves.append({
            "move": uci,
            "san": san,
            "player": player,
            "strategy": strat,
            "eval": "+0.4" if i < 46 else "+4.5" if i < 60 else "+12.0",
            "dialogue": dial
        })
    return moves
