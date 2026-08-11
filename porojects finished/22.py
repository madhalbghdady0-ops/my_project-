library_book=[]
the_name_book=input("enter the name of a book you own : \n")
library_book.append(the_name_book)
the_book_2=input('Enter The Name of another book you own (or press "enter tO skip : ") ')
if the_book_2 :
   library_book.append(the_book_2)
   print(f"you library : {library_book}")
else :
   mo="mk"
book_wish=[]
book_you_wish=input("enter the name of a book you wish to have in the future :")
book_wish.append(book_you_wish)
book_you_wish_2=input("enter the name of a book you wish to have (or press 'enter tO skip : '')")
if book_you_wish_2 :
   book_wish.append(book_you_wish_2)
   print(f"your wish list : {book_wish}")
else :
   no="sj"
book_library_10=input("Enter the name of book from your wishlist that you have acquired (press or 'enter' to skip ) : ")
book_wish.append(book_library_10)
print(f""" Updated library : {library_book}
 Ubdated wish : {book_wish}""")
donate_book=input("enter the name of book from your library you wish to donate  (press or 'enter' to skip ) : ")
if donate_book in book_wish :
   book_wish.remove(donate_book)
   print(f"final library after  donations : {book_wish}")
else:
   mk="dc"