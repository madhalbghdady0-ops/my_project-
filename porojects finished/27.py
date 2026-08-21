the_choice = int(input('Choose what you want to do: \n1 = Currency exchange \n2 = Gold price calculation \n'))

if the_choice == 1:
    name_omla = input('Enter the name of the currency you want to exchange: \n')
    sarf_omla = input('Enter the name of the other currency: \n')
    price_omla = float(input(f'What is the price of {name_omla} compared to {sarf_omla}? \n'))
    aadd = float(input(f'Sweet! Enter the amount of currency you want to calculate: \n'))
    mko = aadd * price_omla
    print(f'Now you have {mko} {name_omla}')
    print("Thank you for using Moaz's program")

elif the_choice == 2:
    name_dahp = float(input('What is the gold karat? \n'))
    nespa = float(input('What is the gold percentage? \n'))
    price_dahp = float(input('What is the price per gram of gold? \n'))
    km_gram_dahp = float(input('How many grams of gold are you buying? \n'))
    
    mki = price_dahp * km_gram_dahp
    mkl = mki * nespa
    mjk = mkl - mki
    
    print(f'The total amount to be paid for {km_gram_dahp} grams is {mjk}')
    print("Thank you for using Moaz's program")

else:
    print("There is an error, please try again")
    print("Thank you for using Moaz's program")