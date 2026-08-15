name=[['apple','banana'], ['milk','water']]
print(name)
enter=input('press enter to change the content.... ')
if name :
    print('here updated the basket.')
    name[0].insert(0,'oranges')
    name[0].insert(3,'kiwis')
    name[1].insert(0,'coffe')
    name[1].remove('water')
    name[1].insert(2,'tea')
    ml=['1', '2', '3']
    name.append(ml)
    print(name)
    njk=(input('Would you like to add anything to the list? ("yes" or "no")')).lower()
    if njk == 'yes' :
        mo=input('Okay, enter what you want to add Where do you want to add it? \n (1a)= (" The one list and Beginning  ") \n (1b)=("The one list and end ") \n (2a)= (" the two list and Beginning ") \n (2b)= ("the two list and end") \n (3a) = ("the three list and Beginning")  \n (3b)= ("the three list and end")\n (4a) =( "the nw list " )').lower()
        ask=input('Enter the items you want to add')
        print("Enter (', ') between everything you want to add so that the program works correctly ")
        mk=ask.split(', ')
        if mo == ('1a') :
            name[0].insert(0,mk)
            print(name)
        elif mo == ('1b') :
            name[0].append(mk)
            print(name)
        elif mo == ('2a') :
            name[1].insert(0,mk)
            print(name)
        elif mo == ('2b') :
            name[1].append(mk)
            print(name)
        elif mo == ('3a') :
            name[2].insert(0,mk)
            print(name)
        elif mo == ('3b') :
            name[2].append(mk)
            print(name)
        elif mo == ('4a') :
            name.append(mk)
            print(name)
        else :
            print ("Unfortunately, your selection is incorrect. Please try again. Thank you for using the Moaz program ")    
    elif njk == 'no' :
        print('Thank you for using the Moaz program')
else:
    ('Thank you for using the Moaz program')