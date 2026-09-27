import chess

# A curated Grandmaster championship game (Sicilian Defense - Sharp Tactical Showdown)
# Each move has SAN, character dialogue, and positional evaluation.
MATCH_MOVES = [
    {
        "move": "e2e4",
        "player": "White",
        "san": "e4",
        "eval": "+0.3",
        "dialogue": "I open with King's Pawn to e4. Establishing early control of the center and opening diagonals for my Queen and Bishop."
    },
    {
        "move": "c7c5",
        "player": "Black",
        "san": "c5",
        "eval": "+0.2",
        "dialogue": "I reply with c5, the Sicilian Defense! An aggressive counter-strike fighting for d4 from the flank."
    },
    {
        "move": "g1f3",
        "player": "White",
        "san": "Nf3",
        "eval": "+0.3",
        "dialogue": "Knight to f3, developing toward the center and preparing an immediate d4 thrust."
    },
    {
        "move": "d7d6",
        "player": "Black",
        "san": "d6",
        "eval": "+0.3",
        "dialogue": "d6, solidifying the e5 square and keeping your Knight away from advanced outposts."
    },
    {
        "move": "d2d4",
        "player": "White",
        "san": "d4",
        "eval": "+0.4",
        "dialogue": "d4! Striking the center open to unleash my pieces for an aggressive tactical middlegame."
    },
    {
        "move": "c5d4",
        "player": "Black",
        "san": "cxd4",
        "eval": "+0.3",
        "dialogue": "c takes d4. I trade my flank pawn for your central pawn and open the half-open c-file."
    },
    {
        "move": "f3d4",
        "player": "White",
        "san": "Nxd4",
        "eval": "+0.4",
        "dialogue": "Knight takes d4! Recapturing with a dominant central knight outpost."
    },
    {
        "move": "g8f6",
        "player": "Black",
        "san": "Nf6",
        "eval": "+0.3",
        "dialogue": "Knight to f6, developing with tempo and targeting your undefended e4 pawn."
    },
    {
        "move": "b1c3",
        "player": "White",
        "san": "Nc3",
        "eval": "+0.4",
        "dialogue": "Knight to c3, naturally defending e4 while developing my second minor piece."
    },
    {
        "move": "a7a6",
        "player": "Black",
        "san": "a6",
        "eval": "+0.4",
        "dialogue": "a6! The signature Najdorf move. Preventing all Bishop and Knight jumps to b5."
    },
    {
        "move": "c1e3",
        "player": "White",
        "san": "Be3",
        "eval": "+0.5",
        "dialogue": "Bishop to e3! The English Attack setup. I am preparing f3, g4, and a full kingside pawn storm!"
    },
    {
        "move": "e7e5",
        "player": "Black",
        "san": "e5",
        "eval": "+0.4",
        "dialogue": "e5! Striking your centralized knight immediately and seizing central space."
    },
    {
        "move": "d4b3",
        "player": "White",
        "san": "Nb3",
        "eval": "+0.5",
        "dialogue": "Knight retreats safely to b3, maintaining harmony and keeping an eye on the queenside."
    },
    {
        "move": "c8e6",
        "player": "Black",
        "san": "Be6",
        "eval": "+0.4",
        "dialogue": "Bishop to e6, developing actively and staking my own claim over the critical d5 square."
    },
    {
        "move": "f2f3",
        "player": "White",
        "san": "f3",
        "eval": "+0.6",
        "dialogue": "f3! Cementing the e4 pawn, shutting down Knight to g4, and clearing the runway for g4 and g5."
    },
    {
        "move": "h7h5",
        "player": "Black",
        "san": "h5",
        "eval": "+0.5",
        "dialogue": "h5! A proactive positional brake to slow down your kingside expansion."
    },
    {
        "move": "d1d2",
        "player": "White",
        "san": "Qd2",
        "eval": "+0.7",
        "dialogue": "Queen to d2! Connecting my rooks and preparing long queenside castling."
    },
    {
        "move": "b8d7",
        "player": "Black",
        "san": "Nbd7",
        "eval": "+0.6",
        "dialogue": "Knight to d7, reinforcing f6 and preparing counterplay along the c-file."
    },
    {
        "move": "e1c1",
        "player": "White",
        "san": "O-O-O",
        "eval": "+0.8",
        "dialogue": "Queenside Castling! King to safety, and my d1 rook is now locked onto the central file."
    },
    {
        "move": "a8c8",
        "player": "Black",
        "san": "Rc8",
        "eval": "+0.7",
        "dialogue": "Rook to c8! Taking control of the open c-file directly opposite your King. The battle lines are drawn!"
    },
    {
        "move": "c1b1",
        "player": "White",
        "san": "Kb1",
        "eval": "+0.9",
        "dialogue": "King to b1. The essential prophylactic step, stepping off the half-open c-file."
    },
    {
        "move": "b7b5",
        "player": "Black",
        "san": "b5",
        "eval": "+0.8",
        "dialogue": "b5! Rolling my queenside pawns forward to harass your c3 knight."
    },
    {
        "move": "c3d5",
        "player": "White",
        "san": "Nd5!!",
        "eval": "+1.8",
        "dialogue": "Knight takes d5!! A thunderous positional sacrifice right in the center! Breaking open Black's defense!"
    },
    {
        "move": "e6d5",
        "player": "Black",
        "san": "Bxd5",
        "eval": "+1.5",
        "dialogue": "I must accept the challenge. Bishop takes d5, eliminating the intrusive monster knight."
    },
    {
        "move": "e4d5",
        "player": "White",
        "san": "exd5",
        "eval": "+2.1",
        "dialogue": "Pawn takes d5! Opening the e-file and clamping down on Black's central freedom."
    },
    {
        "move": "d7b6",
        "player": "Black",
        "san": "Nb6",
        "eval": "+1.9",
        "dialogue": "Knight to b6, rerouting toward the c4 outpost and pressuring the advanced d5 pawn."
    },
    {
        "move": "d2a5",
        "player": "White",
        "san": "Qa5!",
        "eval": "+2.8",
        "dialogue": "Queen to a5! Infiltrating the queenside, pinning the knight and targeting a6 and b5!"
    },
    {
        "move": "f6d5",
        "player": "Black",
        "san": "Nfxd5",
        "eval": "+2.4",
        "dialogue": "Knight captures on d5! Snatching material and defending the queenside perimeter."
    },
    {
        "move": "b3a5",
        "player": "White",
        "san": "Nxa5",
        "eval": "+3.5",
        "dialogue": "Knight takes b6! Liquidating Black's key defender and ripping open the queenside defenses!"
    },
    {
        "move": "d5e3",
        "player": "Black",
        "san": "Ne3",
        "eval": "+3.1",
        "dialogue": "Knight forks the Queen and Rook on e3! Desperate counter-tactics in severe time pressure!"
    },
    {
        "move": "a5c6",
        "player": "White",
        "san": "Nc6!!",
        "eval": "+5.2",
        "dialogue": "Knight to c6!! Ignoring the fork completely! Setting up an inescapable mating net against the uncastled King!"
    },
    {
        "move": "e3d1",
        "player": "Black",
        "san": "Nxd1",
        "eval": "+5.0",
        "dialogue": "Knight takes Rook on d1, but White's tactical attack is moving faster than light!"
    },
    {
        "move": "f1b5",
        "player": "White",
        "san": "Bxb5+!",
        "eval": "+M3",
        "dialogue": "Bishop takes b5 with check! The final devastating Greek Gift clearance! The King has nowhere to run!"
    },
    {
        "move": "a6b5",
        "player": "Black",
        "san": "axb5",
        "eval": "+M2",
        "dialogue": "Pawn takes Bishop... but checkmate is now completely forced."
    },
    {
        "move": "c6d8",
        "player": "White",
        "san": "Nxd8!",
        "eval": "+7.5",
        "dialogue": "Knight captures the Queen on d8! Eliminating Black's most powerful piece and cracking the game wide open!"
    },
    {
        "move": "c8d8",
        "player": "Black",
        "san": "Rxd8",
        "eval": "+7.2",
        "dialogue": "Rook takes Knight on d8, but my King remains completely exposed under severe time pressure."
    },
    {
        "move": "h1d1",
        "player": "White",
        "san": "Rxd1!",
        "eval": "+8.9",
        "dialogue": "Rook takes Knight on d1! Restoring total material dominance. Black has no counter-play left."
    }
]
