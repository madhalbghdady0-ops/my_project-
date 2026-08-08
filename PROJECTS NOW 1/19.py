import random
print("--- Welcome to the Lucky Number Game! ---")
choice_customer=int(input("""Choose your difficulty level:
1. Easy (Numbers from 1 to 5)
2. Medium (Numbers from 1 to 10)
Enter your choice (1 or 2): \n """))
choice_number=int (input("Guess the password the computer set \n"))
choice_computer=""
if choice_customer ==1 :
    choice_computer = random.randint(1,5)
    if 1 > choice_number or choice_number > 5 :
        print(f"The number {choice_number} is outside the range of 1 and 5 try again. ")
        exit()
elif choice_customer == 2 :
    choice_computer = int (random.random() * 10) 
    if 1 > choice_number or choice_number > 10 :
        print(f"The number {choice_number} is outside the range of 1 and 10 try again.") 
        exit()
else :
    print(f"the numper {choice_customer} Error: Please try again. ")
if choice_computer==choice_number :
    print(f"Congratulations! You won the computer. Choose it : ({choice_number})")
elif choice_computer != choice_number :
    print(f"Unfortunately, I lost the computer I chose : ({choice_computer})")