مصري=input('Are you Egyptian? (Yes or No)\n').lower()
if مصري == 'yes':
    print("The first step is done.")
    عمره=int(input(" How old are you? \n"))
    if عمره >= 15 :
       print ("Yes, you can get a card.")
    else:
       print('Wait until you turn 15 Year.')
else  :
   print ('You cannot remove the card')    