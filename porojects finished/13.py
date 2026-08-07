print("""
      ______
    .d$$$$$$$$b.
   d$P""""""$b
  d$  _    _  $b
 :$  (_)  (_)  $:
 :$    _!_    $:
  $b         d$
   $b._____u.$b
    `$$.____.$$'
""")
door=input("""
Welcome to island!
there are two doors in front of you . 🚪 a red door and 🚪 a blue door
which door do you went yo open ? \n
""").lower()
if door == 'blue' :
    print("""
Oops! you choose the crocodile door.
Game over! 🐊 🐊 🐊 
""")
elif door == 'red' :
    print ('''
Great ! now you entered a room. 
''')
else :
    print('invalid choice ! 💔💔💔')
boxes=input('''
you found three boxes : 🎁 white , 🎁 black , 🎁 green
which box do you open ? \n
''').lower()
if boxes == 'black' :
    print('''
Oops! you opened filled with spiders 🕸 🕸 🕸 
''')
elif boxes == 'green' :
    print('congratulation! you found the treasure 💰💰💰')
elif boxes == 'white' :
    print ('Oops! you opened filled with bomb 💣💣💣')
else :
    print ("invalid choice ! 💔💔💔")