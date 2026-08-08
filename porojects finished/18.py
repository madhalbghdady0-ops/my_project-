import random
print ("Welcome to the coin guessing game !")
rand_rando=(print("""1. using random.random()
2. using random.randint() \n"""))
moza=int(input("enter your choice (1 or 2) : \n"))
Guess=input("Enter Your Guess (heads or tails) : \n ").lower()
if moza == 1 :
   random.random()
   if 0 <= random.random() <= 0.5 :
      ms='heads'
   else :
      mh='tails'
if moza == 2 :
   random.randint(1,11)
   if  1<= random.randint(1,11) >= 5 :
      bu="heads"
   else :
      fg="tails"
if Guess == 0 <= random.random() <= 0.5 or  1<= random.randint(1,11) >= 5 == 'heads'  :
   print("""Yes, congratulations! You won.
The computer choice : (heads) """)
elif Guess ==0.51 <= random.random() <= 0.999 or 6 <= random.randint(1,11) >= 11 :
    print('''Yes, congratulations! You won.
The computer choice : tails .
''')
else :
    print (' try again you lost ')
