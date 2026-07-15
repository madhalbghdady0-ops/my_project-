seconds = input ("enter the Second : \n "  )
the_seconds=int(seconds)
minutes= the_seconds % 60
hours= the_seconds // 3600
print ('the course is' + '(' + str ( hours) + ' hours and ' + str (minutes ) + ' minute' )