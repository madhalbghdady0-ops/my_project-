age=int(input('enter your age? \n'))
d=input("معاك رخصه ؟ (yes or NO) \n" )
if age>=18 and d.lower() =="yes" :
    print ("yes")
elif age <18 or d.lower() =="no":
    print("sorry") 
else :
    print("Try again")