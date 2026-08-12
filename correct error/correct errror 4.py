import random
print ("welcom to ('whose wallet') ? ")
list1=input('''you will give me a list of names, and I will pick a person to pay
If you're ready, enter the names separated by a comma \n''')
split_list=list1.split(', ')
len_list=len(split_list)
numper_index=(len_list-1)
mo=(random.randint(0,numper_index))
PD=split_list=[mo]
print(f'Please ask "{PD}" to take his wallet out. Dinner is on him')