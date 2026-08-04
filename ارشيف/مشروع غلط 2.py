import random
the_random=random.randint(0,500)+ random.randint(0,500)+ random.randint(0,500)+ random.randint(0,500)
numper=int(input("enter a 4 numpers password pin : \n"))
if numper==the_random :
    print("congrcolation you win ")
else :
    print(f"you lose the numper is : {the_random}")