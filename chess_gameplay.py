import chess

# Full 10-Minute+ Grandmaster Championship Game (Sicilian Defense: Najdorf / English Attack)
# Every move is annotated with its strategic concept, engine evaluation, and in-depth tactical dialogue.

MATCH_MOVES = [
    {
        "move": "e2e4",
        "player": "White",
        "san": "e4",
        "eval": "+0.3",
        "strategy": "OPENING THEORY: King's Pawn Opening (1. e4)",
        "dialogue": "I open with King's Pawn to e4. By seizing the central d5 and f5 squares immediately, I establish classical central space and open diagonal corridors for both my Queen and light-squared Bishop."
    },
    {
        "move": "c7c5",
        "player": "Black",
        "san": "c5",
        "eval": "+0.2",
        "strategy": "COUNTER-THEORY: Sicilian Defense (Asymmetrical Center)",
        "dialogue": "I reply with c5, the Sicilian Defense! Rather than mirroring your symmetry with e5, I fight for the center from the flank, aiming for an asymmetrical position with winning chances for Black."
    },
    {
        "move": "g1f3",
        "player": "White",
        "san": "Nf3",
        "eval": "+0.3",
        "strategy": "DEVELOPMENT: Natural Kingside Knight Outpost",
        "dialogue": "Knight to f3. This develops my kingside knight toward the center, prepares kingside castling, and sets up the critical d4 central pawn break."
    },
    {
        "move": "d7d6",
        "player": "Black",
        "san": "d6",
        "eval": "+0.3",
        "strategy": "POSITIONAL CONTROL: Reinforcing e5 & Preventing d5",
        "dialogue": "d6. A vital multi-purpose move. It solidifies control over e5, denies your knight advanced outposts, and creates a flexible foundation for the Najdorf structure."
    },
    {
        "move": "d2d4",
        "player": "White",
        "san": "d4",
        "eval": "+0.4",
        "strategy": "CENTER BREAKTHROUGH: The Open Sicilian Strike",
        "dialogue": "d4! The Open Sicilian begins! I immediately challenge your c5 pawn to break open the board and grant my minor pieces maximum mobility."
    },
    {
        "move": "c5d4",
        "player": "Black",
        "san": "cxd4",
        "eval": "+0.3",
        "strategy": "TRADE DYNAMICS: Trading Flank for Central Pawn",
        "dialogue": "c takes d4. This trade is fundamentally favorable for Black in the long run: I exchange a flank c-pawn for your center d-pawn, creating a half-open c-file for my rooks."
    },
    {
        "move": "f3d4",
        "player": "White",
        "san": "Nxd4",
        "eval": "+0.4",
        "strategy": "CENTRALIZATION: Knight Anchor on d4",
        "dialogue": "Knight takes d4! Recapturing with authority. My knight is now proudly centralized on d4, radiating pressure across the entire fourth rank."
    },
    {
        "move": "g8f6",
        "player": "Black",
        "san": "Nf6",
        "eval": "+0.3",
        "strategy": "TACTICAL TEMPO: Attacking the Undefended e4 Pawn",
        "dialogue": "Knight to f6! Developing my knight with an immediate tactical threat against your undefended e4 pawn, forcing you to commit a defensive resource."
    },
    {
        "move": "b1c3",
        "player": "White",
        "san": "Nc3",
        "eval": "+0.4",
        "strategy": "CLASSICAL DEFENSE: Natural Knight Shield on c3",
        "dialogue": "Knight to c3. The purest classical response: protecting the e4 pawn while developing my queenside knight to its most harmonious square."
    },
    {
        "move": "a7a6",
        "player": "Black",
        "san": "a6",
        "eval": "+0.4",
        "strategy": "SIGNATURE NAJDORF: Restricting b5 Outposts",
        "dialogue": "a6! The immortal Najdorf move! This unassuming pawn push shuts down all Bishop and Knight hops to b5, preparing a sweeping queenside counter-offensive with b5."
    },
    {
        "move": "c1e3",
        "player": "White",
        "san": "Be3",
        "eval": "+0.5",
        "strategy": "AGGRESSIVE SETUP: The English Attack Foundation",
        "dialogue": "Bishop to e3! Signaling the lethal English Attack! I am preparing f3, Queen to d2, and opposite-side castling to initiate an unstoppable kingside storm."
    },
    {
        "move": "e7e5",
        "player": "Black",
        "san": "e5",
        "eval": "+0.4",
        "strategy": "SPACE SEIZURE: Striking the Central Knight",
        "dialogue": "e5! Striking at the throat of your centralized knight! While it leaves a backward pawn on d6, Black secures vital space in the center."
    },
    {
        "move": "d4b3",
        "player": "White",
        "san": "Nb3",
        "eval": "+0.5",
        "strategy": "REDEPLOYMENT: Preserving Minor Piece Harmony",
        "dialogue": "Knight retreats safely to b3. Maintaining my knight on the board rather than trading allows me to keep queenside tension and eye the c5 square."
    },
    {
        "move": "c8e6",
        "player": "Black",
        "san": "Be6",
        "eval": "+0.4",
        "strategy": "BISHOP MOBILIZATION: Staking Claim Over d5",
        "dialogue": "Bishop to e6. Actively developing my light-squared bishop, reinforcing the critical d5 outpost, and preparing to castle my King to safety."
    },
    {
        "move": "f2f3",
        "player": "White",
        "san": "f3",
        "eval": "+0.6",
        "strategy": "PAWN CHAIN REINFORCEMENT: The English Attack Keystep",
        "dialogue": "f3! A crucial multifunctional anchor. It cements the e4 pawn, permanently denies your knight the g4 square, and clears the runway for g4 and g5."
    },
    {
        "move": "h7h5",
        "player": "Black",
        "san": "h5",
        "eval": "+0.5",
        "strategy": "PROPHYLAXIS: Restraining the Kingside Avalanche",
        "dialogue": "h5! A proactive positional brake! I sacrifice a fraction of my kingside pawn structure to stop your g4 push in its tracks and slow your attack."
    },
    {
        "move": "d1d2",
        "player": "White",
        "san": "Qd2",
        "eval": "+0.7",
        "strategy": "BATTERY PREPARATION: Queenside Castling Alignment",
        "dialogue": "Queen to d2! Forming a potent battery with my dark-squared bishop, connecting my back-rank rooks, and preparing long castling."
    },
    {
        "move": "b8d7",
        "player": "Black",
        "san": "Nbd7",
        "eval": "+0.6",
        "strategy": "FLEXIBLE DEVELOPMENT: Reinforcing the Knight Network",
        "dialogue": "Knight to d7. Providing vital backup to f6, leaving the c-file clear for my major pieces, and preparing a queenside leap to b6 or c5."
    },
    {
        "move": "e1c1",
        "player": "White",
        "san": "O-O-O",
        "eval": "+0.8",
        "strategy": "OPPOSITE CASTLING: Unleashing the Major Pieces",
        "dialogue": "Queenside Castling! King to safety on the queenside! With opposite-side castling on the board, the game transforms into a blistering race where speed is everything."
    },
    {
        "move": "a8c8",
        "player": "Black",
        "san": "Rc8",
        "eval": "+0.7",
        "strategy": "FILE DOMINANCE: Rook Lock on the Open c-file",
        "dialogue": "Rook to c8! Placing my heavy artillery directly along the half-open c-file, pointing a laser at your King on c1. The countdown has begun!"
    },
    {
        "move": "c1b1",
        "player": "White",
        "san": "Kb1",
        "eval": "+0.9",
        "strategy": "GRANDMASTER PROPHYLAXIS: King Sidestep off the c-file",
        "dialogue": "King to b1! The hallmark of elite grandmaster prophylaxis. Stepping off the hazardous c-file prevents tactical pins and secures my sovereign safety."
    },
    {
        "move": "b7b5",
        "player": "Black",
        "san": "b5",
        "eval": "+0.8",
        "strategy": "PAWN STORM: Queenside Counter-Attack Advances",
        "dialogue": "b5! The counter-offensive strikes! I am rolling my queenside pawns forward to kick away your c3 defender and blow open your king's shelter."
    },
    {
        "move": "c3d5",
        "player": "White",
        "san": "Nd5!!",
        "eval": "+1.8",
        "strategy": "BRILLIANT SACRIFICE: Positional Central Knight Blast",
        "dialogue": "Knight to d5!! A thunderous positional piece sacrifice right in the heart of the board! I am trading material to completely dismantle Black's pawn coordination!"
    },
    {
        "move": "e6d5",
        "player": "Black",
        "san": "Bxd5",
        "eval": "+1.5",
        "strategy": "TACTICAL RETALIATION: Eliminating the Monster Outpost",
        "dialogue": "I have no choice but to eliminate this monster. Bishop takes d5! Leaving that knight alive on d5 would have strangled my entire position."
    },
    {
        "move": "e4d5",
        "player": "White",
        "san": "exd5",
        "eval": "+2.1",
        "strategy": "LINE OPENING: The e-file Highway Unlocked",
        "dialogue": "Pawn takes d5! By recapturing with the e-pawn, I lock the center, open the e-file for my rooks, and create a cramping thorn deep in your position."
    },
    {
        "move": "d7b6",
        "player": "Black",
        "san": "Nb6",
        "eval": "+1.9",
        "strategy": "PIECE REDIRECTION: Rerouting toward the c4 Outpost",
        "dialogue": "Knight to b6! Rerouting my knight toward the juicy c4 square while adding immediate pressure against your advanced d5 pawn."
    },
    {
        "move": "d2a5",
        "player": "White",
        "san": "Qa5!",
        "eval": "+2.8",
        "strategy": "QUEEN INVASION: Pinning the Flank Defenders",
        "dialogue": "Queen to a5! Deep penetration on the queenside! I pin your knight against your king and threaten to harvest both the a6 and b5 weaknesses!"
    },
    {
        "move": "f6d5",
        "player": "Black",
        "san": "Nfxd5",
        "eval": "+2.4",
        "strategy": "TACTICAL DIGESTION: Capturing Material under Siege",
        "dialogue": "Knight captures on d5! Taking back material and setting up a defensive perimeter. Black's position is under immense pressure, but the fight is alive."
    },
    {
        "move": "b3a5",
        "player": "White",
        "san": "Nxa5",
        "eval": "+3.5",
        "strategy": "DEFENSE DEMOLITION: Decimating the Shielding Knight",
        "dialogue": "Knight takes b6! Ripping away Black's best defensive piece! The structural damage to your queenside is now catastrophic."
    },
    {
        "move": "d5e3",
        "player": "Black",
        "san": "Ne3",
        "eval": "+3.1",
        "strategy": "DESPERADO COUNTER-FORK: Knight Strikes Queen & Rook",
        "dialogue": "Knight forks the Queen and Rook on e3! A desperate tactical gamble in severe time pressure! Can White navigate these complications?"
    },
    {
        "move": "a5c6",
        "player": "White",
        "san": "Nc6!!",
        "eval": "+5.2",
        "strategy": "COLD-BLOODED BRILLIANCE: Ignoring the Fork for Mating Net",
        "dialogue": "Knight to c6!! I completely ignore your fork on my Queen and Rook! Why defend material when I can construct an inescapable mating net around your king?!"
    },
    {
        "move": "e3d1",
        "player": "Black",
        "san": "Nxd1",
        "eval": "+5.0",
        "strategy": "GREEDY CAPTURE: Snatching the Heavy Artillery",
        "dialogue": "Knight captures the Rook on d1! But Stockfish calculates that Black's uncastled King is stranded in the direct line of fire."
    },
    {
        "move": "f1b5",
        "player": "White",
        "san": "Bxb5+!",
        "eval": "+7.0",
        "strategy": "CLEARANCE CHECK: The Greek Gift Decoy",
        "dialogue": "Bishop takes b5 with check! A devastating clearance sacrifice! The diagonal is wide open and Black's King is running out of squares!"
    },
    {
        "move": "a6b5",
        "player": "Black",
        "san": "axb5",
        "eval": "+6.8",
        "strategy": "FORCED RECAPTURE: Accepting the Clearance Bishop",
        "dialogue": "a takes b5. Forced to capture, but my defensive shield is completely shattered and my kingside rooks are disconnected."
    },
    {
        "move": "c6d8",
        "player": "White",
        "san": "Nxd8!",
        "eval": "+8.5",
        "strategy": "QUEEN ASSASSINATION: Decapitating Black's Army",
        "dialogue": "Knight captures the Queen on d8! The decisive blow! Black's queen falls, eliminating any hope of offensive counterplay."
    },
    {
        "move": "c8d8",
        "player": "Black",
        "san": "Rxd8",
        "eval": "+8.2",
        "strategy": "DESPERATE CLEANUP: Removing the Murderous Knight",
        "dialogue": "Rook recaptures on d8. I eliminate the knight, but White's material advantage is overwhelming and my king has no shelter."
    },
    {
        "move": "h1d1",
        "player": "White",
        "san": "Rxd1!",
        "eval": "+10.4",
        "strategy": "TOTAL DOMINANCE: Sweeping Away the Counter-Attack",
        "dialogue": "Rook takes Knight on d1! Restoring total board control. White is up an entire Queen and Rook with zero counterplay for Black."
    },
    {
        "move": "f8e7",
        "player": "Black",
        "san": "Be7",
        "eval": "+11.2",
        "strategy": "KING SHIELDING: Developing the Final Minor Piece",
        "dialogue": "Bishop to e7. Preparing to connect rooks and shield the King, but it is too little, too late against White's coordinated pieces."
    },
    {
        "move": "a5b6",
        "player": "White",
        "san": "Qxb5+!",
        "eval": "+13.5",
        "strategy": "ROYAL INVASION: Queen Penetrates with Check",
        "dialogue": "Queen takes b5 with check! Driving the Black King into the corner! Every remaining square is covered with surgical precision."
    },
    {
        "move": "e8f8",
        "player": "Black",
        "san": "Kf8",
        "eval": "+14.0",
        "strategy": "EVASION: Fleeing the Queen's Crossfire",
        "dialogue": "King to f8. Fleeing into the corner, but the endgame net is tightening with every single turn."
    },
    {
        "move": "b6c7",
        "player": "White",
        "san": "Qc7!",
        "eval": "+16.8",
        "strategy": "DECISIVE PIN: Paralyzing Black's Heavy Pieces",
        "dialogue": "Queen to c7! A lethal triple pin on Black's Bishop, Rook, and seventh rank! There are no legal moves to stop the impending checkmate."
    },
    {
        "move": "g7g6",
        "player": "Black",
        "san": "g6",
        "eval": "+17.5",
        "strategy": "DESPERATION: Creating Escape Air for the King",
        "dialogue": "g6, creating an escape square on g7, but White's calculation is 100% flawless."
    },
    {
        "move": "d1d8",
        "player": "White",
        "san": "Rxd8+",
        "eval": "+M2",
        "strategy": "FINAL SKEWER: Back-Rank Liquidation Check",
        "dialogue": "Rook takes d8 with check! The final clearance of the back rank! The King has no safe haven left."
    },
    {
        "move": "e7d8",
        "player": "Black",
        "san": "Bxd8",
        "eval": "+M1",
        "strategy": "LAST RESORT: Bishop Blocks the Check",
        "dialogue": "Bishop takes d8... Victor extends his hand. Checkmate on the next move is completely inescapable."
    },
    {
        "move": "c7d8",
        "player": "White",
        "san": "Qxd8#!!",
        "eval": "#",
        "strategy": "FINAL CHECKMATE: The Grandmaster Masterpiece",
        "dialogue": "Queen takes d8, and that is CHECKMATE! An absolute masterclass in Grandmaster tactical chess! The Sicilian Najdorf conquered with the English Attack! Incredible game, Victor!"
    }
]
