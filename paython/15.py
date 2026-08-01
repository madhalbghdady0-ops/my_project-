import random
number=random.randint(0,10)
my_numper=int (input(print("Choose a numper from 1 to 10 \n")))
if number==my_numper :
    print("your choice is correct.")
elif my_numper > 10 or my_numper < 0:
    m=int ( input (print ("the numper is outside the possibilities. please chooce a numper from 0 to 10. ")))
    if m == number :
     print ("your choice is correct.") 
    else :
       print(f'your choice is incorrect the correct choise is {number} \n  try agin. ' )
else :
    print(f'your choice is incorrect the correct choise is {number} ')