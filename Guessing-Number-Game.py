"""
Guessing Number Game
 Inspired by wordle/termo
"""
import tkinter as tk
from tkinter import messagebox
import tkinter.simpledialog as simpledialog
from PIL import Image, ImageTk
import sqlite3
import numpy as np
from numpy import random as rd


def generate_number():
    """Generates a array with 5 random numbers from 0 to 9"""
    random_number = np.array(rd.randint(1, 10, 1))
    random_number = np.append(random_number, rd.randint(0, 10, 4))
    # print(random_number)  # Used for testing ONLY
    return random_number


def create_leaderboard(connection):
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS leaderboard (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   player VARCHAR NOT NULL UNIQUE,
                   score INTEGER NOT NULL
                   )""")
    cursor.close()


class GuessingNumberGame(tk.Tk):
    """Window of the game"""
    def __init__(self):
        tk.Tk.__init__(self)

        self.title("Numdle (Guest)")
        self.geometry("400x400")
        self.resizable(False, False)
        self.eval("tk::PlaceWindow . center")
        self.iconbitmap("assets/Icon.ico")

        leaderboard = sqlite3.connect("assets/Leaderboard.db")
        create_leaderboard(leaderboard)

        frames_holder = tk.Frame(self)
        frames_holder.pack(anchor = "center")

        game_frame = Game(leaderboard, frames_holder, self)
        game_frame.grid(row = 0,
                        column = 0,
                        sticky = "nsew")


class Game(tk.Frame):
    """Frame where you can play and guess"""
    def __init__(self, connection, master, window):
        tk.Frame.__init__(self, master)
        self.window = window
        self.connection = connection

        header_holder = tk.Frame(self)
        header_holder.pack(anchor = "center",
                           fill = "x",
                           pady = 5)
        
        leaderboard_profile = tk.Frame(header_holder)
        leaderboard_profile.grid(row = 0,
                                 column = 0,
                                 sticky = "w")

        profile_image = Image.open("assets/Profile.png")
        profile_image.thumbnail((30, 30))
        profile_image = ImageTk.PhotoImage(profile_image)

        self.player = [None, "Guest", 0]
        profile = tk.Label(leaderboard_profile,
                           image = profile_image)
        profile.image = profile_image
        profile.grid(row = 0,
                     column = 0,
                     sticky = "e")
        profile.bind("<Button-1>", lambda event: self._select_player(simpledialog.askstring("Who are you?", f"Currently playing as: {self.player[1]}\nType a different nickname to change player:")))

        leaderboard_image = Image.open("assets/Leaderboard.png")
        leaderboard_image.thumbnail((30, 30))
        leaderboard_image = ImageTk.PhotoImage(leaderboard_image)

        open_leaderboard = tk.Label(leaderboard_profile,
                                    image = leaderboard_image)
        open_leaderboard.image = leaderboard_image
        open_leaderboard.grid(row = 0,
                              column = 1,
                              sticky = "w")

        header = tk.Label(header_holder,
                          text = "Numdle",
                          font = ("Arial", 16, "bold"))
        header.grid(row = 0,
                    column = 1,
                    padx = 65,
                    sticky = "nsew")
        
        self.personal_best = tk.Label(header_holder,
                                      text = f"PB: {self.player[2]}",
                                      font = ("Arial", 12, "bold"))
        self.personal_best.grid(row = 0,
                                column = 2,
                                sticky = "e")

        self.info = tk.Label(self,
                             text = "",
                             font = ("Arial", 12))
        self.info.pack(anchor = "center")

        random_number = generate_number()
        rows = self._create_boxes(master)

        self.consecutive_wins = 0
        self.guess_row = 0
        self.guess_button = tk.Button(self,
                                 text = "Guess",
                                 command = lambda: self._check_guess(rows, random_number))
        self.guess_button.pack(anchor = "n")

    def _check_guess(self, rows, random_number):
        """Checks the users guess"""
        for box in rows[self.guess_row]:
            if box.get() == "":
                messagebox.showwarning(title = "Fill the Boxes",
                                     message = "You have to fill all the\nboxes to make a guess!")
                return
        _found = -1

        target = np.copy(random_number)
        for i, box in enumerate(rows[self.guess_row]):
            if int(box.get()) == target[i]:
                target[i] = _found
                box.configure(bg = "Green")
            else:
                box.configure(bg = "Gray")
        
        if np.all(target == _found):
            self._update_boxes(rows, False)
            self.guess_button.config(text = "Play Again",
                                     command = lambda: self._clear_boxes(rows))
            self.info.configure(text = "Nice, you got it!")
            self.consecutive_wins += 1
            if self.consecutive_wins > self.player[2]:
                self.player[2] = self.consecutive_wins
                self.personal_best.configure(text = f"PB: {self.player[2]}")
            return

        for box in rows[self.guess_row]:
            for i, number in enumerate(target):
                if int(box.get()) == number and box["bg"] != "Green":
                    target[i] = _found
                    box.configure(bg = "Yellow")
                    break
        
        if self.guess_row > 4:
            self.guess_button.config(text = "Try Again",
                                     command = lambda: self._clear_boxes(rows))
            self.info.configure(text = f"The number was {''.join(map(str, random_number))}")
            self.consecutive_wins = 0
            if self.player[1] != "Guest":
                self._update_PB()
            self._update_boxes(rows, False)
        else:
            self._update_boxes(rows)

    def _update_boxes(self, rows, next_row = True):
        """Disables the boxes in the guess row and unlocks the boxes in the next if the number wasn't guessed"""
        for box in rows[self.guess_row]:
            box.configure(disabledbackground = box["bg"],
                          state = "disable")
            
        self.guess_row += 1
        if next_row == True:
            for box in rows[self.guess_row]:
                box.configure(state = "normal",
                              bg = "White")
    
    def _clear_boxes(self, rows):
        """Clears the guess boxes and resets their colours"""
        for boxes in rows:
            for box in boxes:
                box.configure(state = "normal",
                              bg = "#f0f0f0")
                box.delete(0, tk.END)
                box.configure(disabledbackground = box["bg"],
                              state = "disable")

        for box in rows[0]:
            box.configure(state = "normal",
                          bg = "White")

        self.guess_row = 0
        self.info.configure(text = f"Wins in a Row: {self.consecutive_wins}")
        random_number = generate_number()
        self.guess_button.configure(text = "Guess",
                                    command = lambda: self._check_guess(rows, random_number))

    def _create_boxes(self, app_window):
        """Creates the boxes for the user to guess the number
        
        Parameters:
        app_window (tk.Tk): Window holding the frame

        Returns:
        Boxes (Array): Array containing the boxes created
        """
        boxes_holder = tk.Label(self)
        boxes_holder.pack(anchor = "n")

        validation_command = app_window.register(self._validate_entry)

        rows = [[] for _ in range(6)]
        for i in range(6):
            for j in range(5):
                box = tk.Entry(boxes_holder,
                               font = ("Arial", 12),
                               justify = "center",
                               fg = "Black",
                               bg = "#f0f0f0",
                               width = 5,
                               state = "disabled",
                               validate = "key",
                               validatecommand=(validation_command, '%P'))
                box.configure(disabledforeground = box["fg"],
                              disabledbackground = box["bg"])
                box.grid(padx = 5,
                         pady = 10,
                         row = i+1,
                         column = j,
                         sticky = "ns")
                rows[i].append(box)

        for boxes in rows:
            for box in boxes:
                box.bind("<KeyPress>", self._focus_next_box)

        for box in rows[0]:
            box.configure(state = "normal",
                          bg = "White")

        return rows
    
    def _focus_next_box(self, event):
        if event.char.isdigit():
            event.widget.tk_focusNext().focus()

    def _validate_entry(self, entry_text):
        """Validates that each box can only have 1 digit
        
        Parameters:
        entry_text (string): Full text inside the entry after the button press

        Retuns:
        True: If the box is empty and the pressed button is a digit
        False: If the box already has something in it or the button pressed isn't a digit
        """
        if entry_text == "":
            return True
        
        elif entry_text.isdigit() and len(entry_text) == 1:
            return True
        
        return False

    def _select_player(self, player):
        if player == None or player == "":
            return
        
        self._update_PB()
        cursor = self.connection.cursor()
        cursor.execute("""SELECT * FROM leaderboard WHERE player = ?""", (player,))
        result = cursor.fetchone()

        if result == None:
            self._create_player(player)
            cursor.execute("""SELECT * FROM leaderboard WHERE player = ?""", (player,))
            result = cursor.fetchone()
        
        cursor.close()
        self.player = list(result)
        self.personal_best.configure(text = f"PB: {self.player[2]}")
        self.info.configure(text = "")
        self.window.title(f"Numdle ({self.player[1]})")

    def _create_player(self, player):
        cursor = self.connection.cursor()

        cursor.execute("INSERT INTO leaderboard (player, score) VALUES (?, ?)", (player, 0))
        self.connection.commit()

        cursor.close()

    def _update_PB(self):
        cursor = self.connection.cursor()
        cursor.execute("""UPDATE leaderboard SET score = ? WHERE id = ?""", (self.player[2], self.player[0]))
        self.connection.commit()
        cursor.close()

class Leaderboard (tk.Frame):
    """Frame for displaying the top 10 best plays and a player best score"""
    def __init__(self, master):
        tk.Frame.__init__(self, master)


if __name__ == "__main__":
    app = GuessingNumberGame()
    app.mainloop()