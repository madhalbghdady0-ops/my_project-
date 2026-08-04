import random
print ("Welcome to the coin guessing game !")
rand_rando=int (input("""1. using random.random()
2. using random.randint()
enter your choice (1 or 2) : \n"""))
if rand_rando == 1 :
    re=random.random()
    if re <=.5 :
        mo='heads'
    elif re >= .5 :
          mk= 'tails' 
    else :
          plf='sdf'
elif rand_rando == 2 :
    mj=(random.randint(1,11))
    if 1 <=  mj   <= 5  :
       ml='heads' 
    elif 6 <= mj <= 11 :
        mu= 'tails'
    else :
        print("Please try again and choose (1 or 2) : ")
Guess=input("Enter Your Guess (heads or tails) : \n ").lower()
if Guess == mo or ml   :
   print ('''Yes, congratulations! You won.
The computer choice : heads .
''')
elif Guess == mu or mk :
    print('''Yes, congratulations! You won.
The computer choice : tails .
''')
else :
    print (' you lost ')