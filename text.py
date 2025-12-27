#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
撲克牌接龍遊戲 (Klondike Solitaire) - Tkinter 版本
"""

import tkinter as tk
from tkinter import messagebox
import random
from enum import Enum

class Suit(Enum):
    SPADE = '♠'
    HEART = '♥'
    DIAMOND = '♦'
    CLUB = '♣'

RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
RANK_VALUES = {rank: i+1 for i, rank in enumerate(RANKS)}

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.face_up = False
    
    def __str__(self):
        return f"{self.rank}{self.suit.value}"
    
    def color(self):
        return 'red' if self.suit in [Suit.HEART, Suit.DIAMOND] else 'black'

class SolitaireGame:
    def __init__(self):
        self.stock = []
        self.waste = []
        self.foundations = [[], [], [], []]
        self.tableau = [[], [], [], [], [], [], []]
        self.selected = None
        self.moves = 0
        self.initialize_deck()
    
    def initialize_deck(self):
        deck = []
        for suit in Suit:
            for rank in RANKS:
                deck.append(Card(suit, rank))
        random.shuffle(deck)
        
        # Deal tableau
        for i in range(7):
            for j in range(i+1):
                card = deck.pop()
                if j == i:
                    card.face_up = True
                self.tableau[i].append(card)
        
        # Remaining cards to stock
        self.stock = deck
    
    def new_game(self):
        self.__init__()
    
    def draw_from_stock(self):
        if not self.stock:
            # Recycle waste
            while self.waste:
                card = self.waste.pop()
                card.face_up = False
                self.stock.append(card)
            return
        
        card = self.stock.pop()
        card.face_up = True
        self.waste.append(card)
        self.moves += 1
    
    def can_place_on_tableau(self, card, pile):
        if not pile:
            return card.rank == 'K'
        top = pile[-1]
        return (RANK_VALUES[card.rank] == RANK_VALUES[top.rank] - 1 and 
                card.color() != top.color())
    
    def can_move_to_foundation(self, card, foundation_idx):
        foundation = self.foundations[foundation_idx]
        if not foundation:
            return card.rank == 'A'
        top = foundation[-1]
        return (card.suit == top.suit and 
                RANK_VALUES[card.rank] == RANK_VALUES[top.rank] + 1)
    
    def move_to_tableau(self, from_pile, to_pile_idx, card_idx):
        if from_pile == 'waste':
            if not self.waste:
                return False
            card = self.waste[-1]
            if self.can_place_on_tableau(card, self.tableau[to_pile_idx]):
                self.tableau[to_pile_idx].append(self.waste.pop())
                self.moves += 1
                # Flip top card of waste if available
                if self.waste and not self.waste[-1].face_up:
                    self.waste[-1].face_up = True
                return True
        elif from_pile in range(7):
            pile = self.tableau[from_pile]
            if card_idx < len(pile) and pile[card_idx].face_up:
                cards_to_move = pile[card_idx:]
                if self.can_place_on_tableau(cards_to_move[0], self.tableau[to_pile_idx]):
                    self.tableau[to_pile_idx].extend(cards_to_move)
                    del pile[card_idx:]
                    self.moves += 1
                    # Flip top card
                    if pile and not pile[-1].face_up:
                        pile[-1].face_up = True
                    return True
        return False
    
    def move_to_foundation(self, from_pile, foundation_idx):
        card = None
        if from_pile == 'waste':
            if self.waste and self.can_move_to_foundation(self.waste[-1], foundation_idx):
                card = self.waste.pop()
        elif from_pile in range(7):
            pile = self.tableau[from_pile]
            if pile and pile[-1].face_up and self.can_move_to_foundation(pile[-1], foundation_idx):
                card = pile.pop()
        
        if card:
            self.foundations[foundation_idx].append(card)
            self.moves += 1
            # Flip top card if in tableau
            if from_pile in range(7) and self.tableau[from_pile] and not self.tableau[from_pile][-1].face_up:
                self.tableau[from_pile][-1].face_up = True
            return True
        return False
    
    def is_won(self):
        return all(len(f) == 13 for f in self.foundations)

class SolitaireGUI:
    CARD_WIDTH = 80
    CARD_HEIGHT = 120
    CARD_GAP = 30
    
    def __init__(self, root):
        self.root = root
        self.root.title("撲克牌接龍 - Tkinter 版")
        self.root.geometry("1000x700")
        self.root.configure(bg='#0b6623')
        
        self.game = SolitaireGame()
        self.selected_card = None
        self.selected_source = None
        
        self.setup_ui()
        self.draw_game()
    
    def setup_ui(self):
        # Header frame
        header = tk.Frame(self.root, bg='#0b6623')
        header.pack(pady=10)
        
        tk.Label(header, text="撲克牌接龍", font=("Arial", 24, "bold"), 
                fg="white", bg='#0b6623').pack()
        
        button_frame = tk.Frame(header, bg='#0b6623')
        button_frame.pack(pady=5)
        
        tk.Button(button_frame, text="重新開始", command=self.new_game,
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                 padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="抽牌", command=self.draw_card,
                 bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                 padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(header, text="", font=("Arial", 10),
                                     fg="white", bg='#0b6623')
        self.status_label.pack()
        
        # Game canvas
        self.canvas = tk.Canvas(self.root, bg='#0b6623', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Pile information (for coordinate mapping)
        self.pile_coords = {}
    
    def draw_game(self):
        self.canvas.delete("all")
        self.pile_coords.clear()
        
        # Top row: Stock, Waste, Foundations
        y = 20
        x = 20
        
        # Stock pile
        self.draw_pile(x, y, self.game.stock, "stock", len(self.game.stock) > 0)
        self.pile_coords["stock"] = (x, y, x + self.CARD_WIDTH, y + self.CARD_HEIGHT)
        
        # Waste pile
        x += self.CARD_WIDTH + 20
        if self.game.waste:
            card = self.game.waste[-1]
            self.draw_card_graphic(x, y, card, True, "waste")
        else:
            self.draw_empty_pile(x, y)
        self.pile_coords["waste"] = (x, y, x + self.CARD_WIDTH, y + self.CARD_HEIGHT)
        
        # Foundations
        x = 400
        for i in range(4):
            if self.game.foundations[i]:
                card = self.game.foundations[i][-1]
                self.draw_card_graphic(x, y, card, True, f"foundation_{i}")
            else:
                self.draw_empty_pile(x, y)
            self.pile_coords[f"foundation_{i}"] = (x, y, x + self.CARD_WIDTH, y + self.CARD_HEIGHT)
            x += self.CARD_WIDTH + 10
        
        # Tableau
        y = 160
        x = 20
        for pile_idx in range(7):
            pile = self.game.tableau[pile_idx]
            if not pile:
                self.draw_empty_pile(x, y)
                self.pile_coords[f"tableau_{pile_idx}"] = (x, y, x + self.CARD_WIDTH, y + self.CARD_HEIGHT)
            else:
                for card_idx, card in enumerate(pile):
                    card_y = y + card_idx * self.CARD_GAP
                    if card.face_up:
                        self.draw_card_graphic(x, card_y, card, True, f"tableau_{pile_idx}_{card_idx}")
                    else:
                        self.draw_card_back(x, card_y)
                self.pile_coords[f"tableau_{pile_idx}"] = (x, y, x + self.CARD_WIDTH, y + len(pile) * self.CARD_GAP + self.CARD_HEIGHT)
            x += self.CARD_WIDTH + 10
        
        self.update_status()
    
    def draw_empty_pile(self, x, y):
        self.canvas.create_rectangle(x, y, x + self.CARD_WIDTH, y + self.CARD_HEIGHT,
                                     fill='#1a7a2a', outline='white', width=2, dash=(4, 4))
    
    def draw_pile(self, x, y, pile, pile_type, has_cards):
        if has_cards:
            self.canvas.create_rectangle(x, y, x + self.CARD_WIDTH, y + self.CARD_HEIGHT,
                                        fill='#0d5c1f', outline='white', width=2)
            self.canvas.create_text(x + self.CARD_WIDTH // 2, y + self.CARD_HEIGHT // 2,
                                   text="🂠", font=("Arial", 40), fill='white')
        else:
            self.draw_empty_pile(x, y)
    
    def draw_card_back(self, x, y):
        self.canvas.create_rectangle(x, y, x + self.CARD_WIDTH, y + self.CARD_HEIGHT,
                                     fill='#1a1a3e', outline='#444444', width=1)
        self.canvas.create_text(x + self.CARD_WIDTH // 2, y + self.CARD_HEIGHT // 2,
                               text="🂠", font=("Arial", 20), fill='#aaaaaa')
    
    def draw_card_graphic(self, x, y, card, face_up, card_id):
        color = card.color()
        fill_color = 'white'
        text_color = 'red' if color == 'red' else 'black'
        
        self.canvas.create_rectangle(x, y, x + self.CARD_WIDTH, y + self.CARD_HEIGHT,
                                     fill=fill_color, outline='#cccccc', width=1, tags=card_id)
        
        self.canvas.create_text(x + 8, y + 8, anchor='nw',
                               text=f"{card.rank}{card.suit.value}",
                               font=("Arial", 10, "bold"), fill=text_color, tags=card_id)
    
    def on_canvas_click(self, event):
        x, y = event.x, event.y
        clicked_pile = None
        
        # Check which pile was clicked
        for pile_name, (x1, y1, x2, y2) in self.pile_coords.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                clicked_pile = pile_name
                break
        
        if not clicked_pile:
            return
        
        # Handle different pile types
        if clicked_pile == "stock":
            self.draw_card()
        elif clicked_pile == "waste":
            self.select_card("waste", 0)
        elif clicked_pile.startswith("foundation_"):
            foundation_idx = int(clicked_pile.split("_")[1])
            if self.selected_source:
                self.move_to_foundation(foundation_idx)
            self.draw_game()
        elif clicked_pile.startswith("tableau_"):
            parts = clicked_pile.split("_")
            tableau_idx = int(parts[1])
            self.select_tableau_card(tableau_idx)
        
        self.draw_game()
    
    def select_card(self, source, card_idx):
        if source == "waste" and self.game.waste:
            self.selected_card = self.game.waste[-1]
            self.selected_source = "waste"
        elif source in range(7):
            pile = self.game.tableau[source]
            if card_idx < len(pile) and pile[card_idx].face_up:
                self.selected_card = pile[card_idx]
                self.selected_source = source
    
    def select_tableau_card(self, tableau_idx):
        pile = self.game.tableau[tableau_idx]
        if not pile:
            return
        
        # Click on face-down card to flip
        if not pile[-1].face_up:
            pile[-1].face_up = True
            return
        
        # Select the top face-up card
        if self.selected_source is not None:
            # Move to this tableau
            if self.selected_source == "waste":
                if self.game.move_to_tableau("waste", tableau_idx, None):
                    self.selected_source = None
                    self.selected_card = None
            elif isinstance(self.selected_source, int):
                # Find the card index in source tableau
                src_pile = self.game.tableau[self.selected_source]
                card_idx = src_pile.index(self.selected_card) if self.selected_card in src_pile else -1
                if card_idx >= 0:
                    if self.game.move_to_tableau(self.selected_source, tableau_idx, card_idx):
                        self.selected_source = None
                        self.selected_card = None
        else:
            # Just select this card
            self.selected_card = pile[-1]
            self.selected_source = tableau_idx
    
    def move_to_foundation(self, foundation_idx):
        if not self.selected_source:
            return
        
        if self.game.move_to_foundation(self.selected_source, foundation_idx):
            self.selected_source = None
            self.selected_card = None
            
            if self.game.is_won():
                messagebox.showinfo("恭喜！", f"你贏了！\n步數: {self.game.moves}")
    
    def draw_card(self):
        self.game.draw_from_stock()
    
    def new_game(self):
        self.game.new_game()
        self.selected_card = None
        self.selected_source = None
        self.draw_game()
    
    def update_status(self):
        status = f"牌庫: {len(self.game.stock)}  棄牌: {len(self.game.waste)}  步數: {self.game.moves}"
        self.status_label.config(text=status)

def main():
    root = tk.Tk()
    gui = SolitaireGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
