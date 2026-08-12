import random

print("Welcome to the coin guessing game !")

# 1. بنسأل المستخدم يحب نختار بأي طريقة؟
rand_rando = int(input("""1. using random.random()
2. using random.randint()
enter your choice (1 or 2) : \n"""))

# متغير واحد ثابت هنخزن فيه اختيار الكمبيوتر النهائي (يا heads يا tails)
computer_choice = ""

# 2. لو اختار الطريقة الأولى (عشري)
if rand_rando == 1:
    re = random.random()
    if re <= 0.5:
        computer_choice = "heads"
    else:
        computer_choice = "tails"

# 3. لو اختار الطريقة التانية (أرقام صحيحة)
elif rand_rando == 2:
    mj = random.randint(1, 11)
    if 1 <= mj <= 5:
        computer_choice = "heads"
    else:
        computer_choice = "tails"

else:
    print("Please choose 1 or 2 only!")

# 4. ناخد توقع المستخدم (ونحول الحروف لكابيتال أو سمول عشان ما يبقاش فيه غلط)
guess = input("Enter Your Guess (heads or tails) : ").strip().lower()

# 5. المقارنة النهائية وإعلان الفائز
print(f"The computer choice was: {computer_choice}")

if guess == computer_choice:
    print("Yes, congratulations! You won. 🎉")
else:
    print("Sorry, you lost. Try again! 😢")