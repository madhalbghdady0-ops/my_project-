color=[]
color.append(input("add the first color you like : "))
add_color=input("do you want to add more more colors ? yes or no ?").lower ()
if add_color == "yes" :
    add_color_2=input("add another color to the list :")
    color.append(add_color_2)
    print(f"""the colors you like are :
{color}""")
elif add_color == "no" :
     print(f"the colors you like are : {color}")
else :
     print("sorry try again.")     