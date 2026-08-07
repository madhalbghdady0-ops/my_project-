import random
print ("Welcome to the coin guessing game !")
mo= (random.random())
Mi=(random.randint(1,11))
moiu=int (input("""1. using random.random()
2. using random.randint()
enter your choice (1 or 2) : \n"""))
if moiu == 1 :
   mo= (random.random())
   if mo <= 0.5 :
      lp="heads"
   elif mo >= 0.5 :
      prin="tails"
elif moiu == 2 :
   Mi=(random.randint(1,11))
if Mi == (1,5) :
         pri="heads"
elif Mi == (6,11) :
        pr="tails"
else :
     mu=input("Please try again and choose (1 or 2) :")
mlk=input("The computer is expected to choose (heads or tails) :").lower()   
if Mi == (1,5) or mo == 0.5 and mlk== "heads" :
     print ('Yes, you are the winner.')
elif Mi ==  (6,11) or mo > 0.5 or mlk == "tails" :
     print ('Yes, you are the winner.')
else :
     print ("sorry you are lose ")
