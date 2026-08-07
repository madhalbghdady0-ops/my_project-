import random
import tkinter as tk
from tkinter import messagebox


def play_game(rand_choice):
  guess = guess_var.get().strip().lower()

  if guess not in ["heads", "tails"]:
    messagebox.showerror(
        "خطأ", "من فضلك اكتب تخمينك صح (heads أو tails) الأول!"
    )
    return

  computer_choice = ""

  if rand_choice == 1:
    re = random.random()
    if re <= 0.5:
      computer_choice = "heads"
    else:
      computer_choice = "tails"
  elif rand_choice == 2:
    mj = random.randint(1, 11)
    if 1 <= mj <= 5:
      computer_choice = "heads"
    else:
      computer_choice = "tails"

  # التحقق من الفوز أو الخسارة
  if guess == computer_choice:
    result_label.config(
        text=f"اختيار الكمبيوتر: {computer_choice}\n🎉 مبروك، لقد فزت!",
        fg="green",
    )
  else:
    result_label.config(
        text=f"اختيار الكمبيوتر: {computer_choice}\n❌ للأسف، لقد خسرت!",
        fg="red",
    )


# إعداد واجهة البرنامج (GUI)
root = tk.Tk()
root.title("لعبة تخمين العملة - Coin Guessing Game")
root.geometry("400x350")
root.config(bg="#f0f0f0")

# العنوان
title_label = tk.Label(
    root,
    text="Welcome to the coin guessing game!",
    font=("Arial", 14, "bold"),
    bg="#f0f0f0",
)
title_label.pack(pady=15)

# خانة إدخال التخمين
guess_label = tk.Label(
    root,
    text="اكتب تخمينك (heads أو tails):",
    font=("Arial", 11),
    bg="#f0f0f0",
)
guess_label.pack(pady=5)

guess_var = tk.StringVar()
guess_entry = tk.Entry(
    root, textvariable=guess_var, font=("Arial", 12), justify="center"
)
guess_entry.pack(pady=5)

# أزرار الاختيار (طريقة الحظ 1 أو 2)
btn_frame = tk.Frame(root, bg="#f0f0f0")
btn_frame.pack(pady=15)

btn_mode1 = tk.Button(
    btn_frame,
    text="العب باستخدام random()",
    font=("Arial", 10),
    bg="#4CAF50",
    fg="white",
    width=20,
    command=lambda: play_game(1),
)
btn_mode1.pack(pady=5)

btn_mode2 = tk.Button(
    btn_frame,
    text="العب باستخدام randint()",
    font=("Arial", 10),
    bg="#2196F3",
    fg="white",
    width=20,
    command=lambda: play_game(2),
)
btn_mode2.pack(pady=5)

# عرض النتيجة
result_label = tk.Label(
    root, text="", font=("Arial", 11, "bold"), bg="#f0f0f0", justify="center"
)
result_label.pack(pady=15)

root.mainloop()