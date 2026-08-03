import random
the_random=random.randint(1000,9999)
numper=(input("enter a 4 numpers password pin : \n"))
mou=len(numper)
if len(numper)==4:
   print("A Few Moments: Comparing Your Choice with the Computer's Choice")
if numper==the_random :
    print("congrcolation you win ")
elif len(numper) != 4 :
    print(f"Try again and enter a 4-digit number, not a number consisting of {mou} " )
else :
    print(f"you lose the numper is : {the_random}")