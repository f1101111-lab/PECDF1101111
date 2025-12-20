import tkinter as tk
from tkinter import messagebox
import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageTk

class Suit(Enum):
    """牌花色"""
    HEARTS = ("♥", "red")      # 紅心
    DIAMONDS = ("♦", "red")    # 方塊
    CLUBS = ("♣", "black")     # 黑桃
    SPADES = ("♠", "black")    # 梅花

class Rank(Enum):
    """牌等級"""
    ACE = ("A", 1)
    TWO = ("2", 2)
    THREE = ("3", 3)
    FOUR = ("4", 4)
    FIVE = ("5", 5)
    SIX = ("6", 6)
    SEVEN = ("7", 7)
    EIGHT = ("8", 8)
    NINE = ("9", 9)
    TEN = ("10", 10)
    JACK = ("J", 11)
    QUEEN = ("Q", 12)
    KING = ("K", 13)

@dataclass
class Card:
    """單張牌"""
    suit: Suit
    rank: Rank
    
    def __str__(self):
        return f"{self.rank.value[0]}{self.suit.value[0]}"
    
    def get_color(self):
        """取得牌的顏色"""
        return self.suit.value[1]
    
    def get_rank_value(self):
        """取得牌的數值"""
        return self.rank.value[1]

class Deck:
    """牌組"""
    def __init__(self):
        self.cards: List[Card] = []
        self.create_deck()
    
    def create_deck(self):
        """創建標準52張牌"""
        for suit in Suit:
            for rank in Rank:
                self.cards.append(Card(suit, rank))
        random.shuffle(self.cards)
    
    def draw(self) -> Optional[Card]:
        """抽取一張牌"""
        return self.cards.pop() if self.cards else None
    
    def reset_deck(self):
        """重置牌組"""
        self.cards.clear()
        self.create_deck()

class CardPile:
    """牌堆"""
    def __init__(self, pile_id: int, is_foundation: bool = False):
        self.pile_id = pile_id
        self.cards: List[Card] = []
        self.is_foundation = is_foundation
    
    def add_card(self, card: Card):
        """添加牌"""
        self.cards.append(card)
    
    def remove_card(self) -> Optional[Card]:
        """移除頂部的牌"""
        return self.cards.pop() if self.cards else None
    
    def get_top_card(self) -> Optional[Card]:
        """取得頂部的牌"""
        return self.cards[-1] if self.cards else None
    
    def is_empty(self) -> bool:
        """檢查是否為空"""
        return len(self.cards) == 0
    
    def can_accept_card(self, card: Card) -> bool:
        """檢查是否可以放置牌"""
        if self.is_foundation:
            # 基礎堆：只能放同花色的牌，且必須順序遞增
            if self.is_empty():
                return card.rank == Rank.ACE
            top_card = self.get_top_card()
            return (card.suit == top_card.suit and 
                    card.get_rank_value() == top_card.get_rank_value() + 1)
        else:
            # 工作堆：只能放顏色不同且數值小1的牌
            if self.is_empty():
                return card.rank == Rank.KING
            top_card = self.get_top_card()
            return (card.get_color() != top_card.get_color() and 
                    card.get_rank_value() == top_card.get_rank_value() - 1)

class SolitaireGame:
    """撲克牌接龍遊戲"""
    def __init__(self, root):
        self.root = root
        self.root.title("撲克牌接龍")
        self.root.geometry("1200x800")
        self.root.configure(bg="#2d5016")
        
        # 遊戲變數
        self.deck = Deck()
        self.waste_pile: List[Card] = []
        self.foundation_piles: List[CardPile] = []
        self.tableau_piles: List[CardPile] = []
        
        self.selected_card: Optional[Card] = None
        self.selected_pile: Optional[CardPile] = None
        self.selected_index: int = -1
        
        self.card_width = 80
        self.card_height = 120
        self.card_images = {}
        
        self.moves = 0
        self.start_time = None
        
        self.setup_ui()
        self.initialize_game()
    
    def setup_ui(self):
        """設置使用者界面"""
        # 頂部框架
        top_frame = tk.Frame(self.root, bg="#2d5016")
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = tk.Label(top_frame, text="撲克牌接龍", 
                              font=("Arial", 24, "bold"), 
                              fg="white", bg="#2d5016")
        title_label.pack(side=tk.LEFT)
        
        self.moves_label = tk.Label(top_frame, text="步數: 0", 
                                   font=("Arial", 12), 
                                   fg="white", bg="#2d5016")
        self.moves_label.pack(side=tk.RIGHT, padx=20)
        
        # 按鈕框架
        button_frame = tk.Frame(self.root, bg="#2d5016")
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        restart_btn = tk.Button(button_frame, text="重新開始", 
                               command=self.restart_game,
                               font=("Arial", 10), width=15)
        restart_btn.pack(side=tk.LEFT, padx=5)
        
        hint_btn = tk.Button(button_frame, text="提示", 
                            command=self.show_hint,
                            font=("Arial", 10), width=15)
        hint_btn.pack(side=tk.LEFT, padx=5)
        
        undo_btn = tk.Button(button_frame, text="撤銷", 
                            command=self.undo_move,
                            font=("Arial", 10), width=15)
        undo_btn.pack(side=tk.LEFT, padx=5)
        
        # 遊戲畫布
        self.canvas = tk.Canvas(self.root, bg="#2d5016", 
                               highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        self.move_history = []
    
    def initialize_game(self):
        """初始化遊戲"""
        # 建立基礎堆
        for i in range(4):
            pile = CardPile(i, is_foundation=True)
            self.foundation_piles.append(pile)
        
        # 建立工作堆
        for i in range(7):
            pile = CardPile(i)
            self.tableau_piles.append(pile)
        
        # 分配牌
        for i, pile in enumerate(self.tableau_piles):
            for j in range(i + 1):
                card = self.deck.draw()
                if card:
                    pile.add_card(card)
        
        self.moves = 0
        self.move_history = []
        self.draw_game()
    
    def draw_card_image(self, card: Card) -> tk.PhotoImage:
        """繪製牌卡圖像"""
        img = Image.new('RGB', (self.card_width, self.card_height), 'white')
        draw = ImageDraw.Draw(img)
        
        # 邊框
        draw.rectangle([0, 0, self.card_width-1, self.card_height-1], 
                      outline='black', width=2)
        
        # 牌面內容
        color = 'red' if card.get_color() == 'red' else 'black'
        
        # 上方
        draw.text((5, 5), card.rank.value[0], fill=color, 
                 font=None)
        draw.text((10, 20), card.suit.value[0], fill=color, 
                 font=None)
        
        # 中央
        draw.text((25, 50), card.suit.value[0], fill=color, 
                 font=None)
        
        # 下方
        draw.text((60, 100), card.rank.value[0], fill=color, 
                 font=None)
        
        return ImageTk.PhotoImage(img)
    
    def draw_game(self):
        """繪製遊戲畫面"""
        self.canvas.delete("all")
        
        # 更新步數標籤
        self.moves_label.config(text=f"步數: {self.moves}")
        
        # 定位
        start_x = 30
        start_y = 30
        pile_width = self.card_width + 20
        
        # 繪製牌組
        deck_x = start_x
        deck_y = start_y
        if self.deck.cards:
            self.canvas.create_rectangle(deck_x, deck_y, 
                                        deck_x + self.card_width,
                                        deck_y + self.card_height,
                                        fill='white', outline='black', width=2)
            self.canvas.create_text(deck_x + self.card_width//2,
                                   deck_y + self.card_height//2,
                                   text=f"{len(self.deck.cards)}",
                                   font=("Arial", 16, "bold"))
            self.canvas.tag_bind(self.canvas.create_text(
                deck_x + self.card_width//2,
                deck_y + self.card_height//2),
                                "<Button-1>", lambda e: self.draw_from_deck())
        else:
            self.canvas.create_rectangle(deck_x, deck_y,
                                        deck_x + self.card_width,
                                        deck_y + self.card_height,
                                        fill='lightgray', outline='black', width=2)
        
        # 繪製廢牌堆
        waste_x = start_x + pile_width
        waste_y = start_y
        if self.waste_pile:
            card = self.waste_pile[-1]
            self.draw_card_on_canvas(card, waste_x, waste_y, "waste")
        else:
            self.canvas.create_rectangle(waste_x, waste_y,
                                        waste_x + self.card_width,
                                        waste_y + self.card_height,
                                        fill='lightgray', outline='black', width=2)
        
        # 繪製基礎堆
        for i, pile in enumerate(self.foundation_piles):
            foundation_x = start_x + 500 + i * pile_width
            foundation_y = start_y
            if pile.is_empty():
                suit = list(Suit)[i]
                self.canvas.create_rectangle(foundation_x, foundation_y,
                                            foundation_x + self.card_width,
                                            foundation_y + self.card_height,
                                            fill='lightgray', outline='black', width=2)
                self.canvas.create_text(foundation_x + self.card_width//2,
                                       foundation_y + self.card_height//2,
                                       text=suit.value[0],
                                       font=("Arial", 24, "bold"),
                                       fill=suit.value[1])
                self.canvas.tag_bind(self.canvas.create_rectangle(
                    foundation_x, foundation_y,
                    foundation_x + self.card_width,
                    foundation_y + self.card_height),
                    "<Button-1>", 
                    lambda e, p=pile: self.select_pile(p))
            else:
                card = pile.get_top_card()
                self.draw_card_on_canvas(card, foundation_x, foundation_y, f"foundation_{i}")
        
        # 繪製工作堆
        for i, pile in enumerate(self.tableau_piles):
            tableau_x = start_x + i * pile_width
            tableau_y = start_y + 180
            
            if pile.is_empty():
                self.canvas.create_rectangle(tableau_x, tableau_y,
                                            tableau_x + self.card_width,
                                            tableau_y + self.card_height,
                                            fill='darkgreen', outline='gray', width=2)
                self.canvas.tag_bind(self.canvas.create_rectangle(
                    tableau_x, tableau_y,
                    tableau_x + self.card_width,
                    tableau_y + self.card_height),
                    "<Button-1>",
                    lambda e, p=pile: self.select_pile(p))
            else:
                offset = 0
                for j, card in enumerate(pile.cards):
                    card_y = tableau_y + min(j * 25, 150)
                    self.draw_card_on_canvas(card, tableau_x, card_y, 
                                            f"tableau_{i}_{j}")
    
    def draw_card_on_canvas(self, card: Card, x: int, y: int, tag: str):
        """在畫布上繪製牌"""
        color = 'red' if card.get_color() == 'red' else 'black'
        
        self.canvas.create_rectangle(x, y, x + self.card_width,
                                    y + self.card_height,
                                    fill='white', outline='black', width=2,
                                    tags=tag)
        
        self.canvas.create_text(x + 10, y + 15,
                               text=f"{card.rank.value[0]}{card.suit.value[0]}",
                               font=("Arial", 12, "bold"),
                               fill=color, anchor="nw", tags=tag)
        
        self.canvas.create_text(x + self.card_width - 15, y + self.card_height - 20,
                               text=f"{card.rank.value[0]}{card.suit.value[0]}",
                               font=("Arial", 10, "bold"),
                               fill=color, anchor="se", tags=tag)
        
        self.canvas.tag_bind(tag, "<Button-1>", 
                            lambda e, c=card: self.on_card_click(c, tag))
    
    def on_card_click(self, card: Card, tag: str):
        """牌被點擊"""
        # 確定牌所在的堆
        if "waste" in tag:
            self.selected_card = card
            self.selected_pile = None
        elif "foundation" in tag:
            idx = int(tag.split("_")[1])
            self.selected_card = card
            self.selected_pile = self.foundation_piles[idx]
        elif "tableau" in tag:
            parts = tag.split("_")
            pile_idx = int(parts[1])
            self.selected_card = card
            self.selected_pile = self.tableau_piles[pile_idx]
    
    def on_canvas_click(self, event):
        """畫布被點擊"""
        pass
    
    def on_canvas_drag(self, event):
        """畫布被拖拽"""
        pass
    
    def on_canvas_release(self, event):
        """畫布被放開"""
        if not self.selected_card or not self.selected_pile:
            return
        
        # 檢查目標
        x, y = event.x, event.y
        
        # 檢查基礎堆
        for i, pile in enumerate(self.foundation_piles):
            foundation_x = 30 + 500 + i * 100
            foundation_y = 30
            if (foundation_x < x < foundation_x + self.card_width and
                foundation_y < y < foundation_y + self.card_height):
                self.move_card(self.selected_pile, pile)
                return
        
        # 檢查工作堆
        for i, pile in enumerate(self.tableau_piles):
            tableau_x = 30 + i * 100
            tableau_y = 210
            if (tableau_x < x < tableau_x + self.card_width and
                tableau_y < y < tableau_y + self.card_height + 150):
                self.move_card(self.selected_pile, pile)
                return
        
        self.selected_card = None
        self.selected_pile = None
    
    def draw_from_deck(self):
        """從牌組抽牌"""
        card = self.deck.draw()
        if card:
            self.waste_pile.append(card)
            self.moves += 1
            self.move_history.append(("deck", None, None))
        else:
            # 重新洗牌
            for card in self.waste_pile:
                self.deck.cards.append(card)
            self.waste_pile.clear()
            random.shuffle(self.deck.cards)
            self.moves += 1
            self.move_history.append(("reshuffle", None, None))
        
        self.draw_game()
    
    def select_pile(self, pile: CardPile):
        """選擇堆"""
        if pile.is_empty() and not pile.is_foundation:
            return
        
        if not pile.is_empty():
            card = pile.get_top_card()
            self.selected_card = card
            self.selected_pile = pile
    
    def move_card(self, from_pile: CardPile, to_pile: CardPile):
        """移動牌"""
        if not self.selected_card or from_pile.is_empty():
            return
        
        card = from_pile.get_top_card()
        if to_pile.can_accept_card(card):
            from_pile.remove_card()
            to_pile.add_card(card)
            self.moves += 1
            self.move_history.append((from_pile, to_pile, card))
            self.check_win()
        
        self.selected_card = None
        self.selected_pile = None
        self.draw_game()
    
    def show_hint(self):
        """顯示提示"""
        # 尋找可能的移動
        hint_found = False
        
        # 檢查廢牌堆
        if self.waste_pile:
            card = self.waste_pile[-1]
            for foundation in self.foundation_piles:
                if foundation.can_accept_card(card):
                    messagebox.showinfo("提示", 
                                       f"可以將 {card} 放入基礎堆")
                    hint_found = True
                    break
            
            if not hint_found:
                for tableau in self.tableau_piles:
                    if tableau.can_accept_card(card):
                        messagebox.showinfo("提示",
                                           f"可以將 {card} 放入工作堆")
                        hint_found = True
                        break
        
        # 檢查工作堆
        if not hint_found:
            for i, tableau in enumerate(self.tableau_piles):
                if not tableau.is_empty():
                    card = tableau.get_top_card()
                    for foundation in self.foundation_piles:
                        if foundation.can_accept_card(card):
                            messagebox.showinfo("提示",
                                               f"可以將工作堆{i}的 {card} 放入基礎堆")
                            hint_found = True
                            break
                    if hint_found:
                        break
        
        if not hint_found:
            messagebox.showinfo("提示", "目前沒有明顯的移動建議")
    
    def undo_move(self):
        """撤銷上一步"""
        if not self.move_history:
            messagebox.showinfo("撤銷", "沒有可撤銷的移動")
            return
        
        messagebox.showinfo("撤銷", "撤銷功能在此版本中尚未完全實現")
    
    def check_win(self):
        """檢查是否勝利"""
        if all(len(pile.cards) == 13 for pile in self.foundation_piles):
            messagebox.showinfo("恭喜", f"你贏了！\n用了 {self.moves} 步")
            self.restart_game()
    
    def restart_game(self):
        """重新開始遊戲"""
        self.deck = Deck()
        self.waste_pile.clear()
        for pile in self.tableau_piles + self.foundation_piles:
            pile.cards.clear()
        self.initialize_game()

def main():
    root = tk.Tk()
    game = SolitaireGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
