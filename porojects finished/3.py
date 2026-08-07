long=int(input("How long is the room? \n"))
Width=int(input ("How wide is the room? \n "))
price=int( input("How much is the price per meter? \n"))
Area=int( ( long * Width ))
price= int(( price * Area ))
شاشه =input( print("1 =Area  or  price = 2"))
if شاشه == "1":
        print ( Area )
elif شاشه == "2":
        print( price  )
else :
        print ("I'm sorry, I didn't understand you. Please try again.")
#مشروع حساب مساحه غرفه وتكلفتها 