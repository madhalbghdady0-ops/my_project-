the_choise=int(input('''اختار ماذا تريد ان تفعل :
1= صرف عمله 
2=حساب سعر الذهب \n'''))
if the_choise == 1 :
    name_omla=input("ادخل اسم العمله التي تريد حساب صرفها ؟ \n")
    sarf_omla=input("ادخل اسم العمله الاخري ؟ \n")
    price_omla=float(input(f"كم سعر {name_omla} مقارنه ب {sarf_omla} \n"))
    aadd=float(input("حلو اوووي ادخل عدد العملات اللي عايز تحسب صرفها \n"))
    mko=aadd*price_omla
    nhh=print(f"اذن ال{aadd}{name_omla}={mko}{sarf_omla}")
    print("شكرا لاستخدامك برنامج معاذ البغدادي")
elif the_choise== 2 :
    name_dahp=float(input('الدهب عيار كام ؟ \n'))
    nespa=float(input('كم نسبه التاجر ؟ \n'))
    price_dahp=float(input('كم سعر جرام الدهب ؟ \n'))
    km_gram_dahp=float(input('هتشتري كم جرام دهب ؟ \n'))
    omla_aee=(input("اي العمله اللي هتشتري بيها الدهب ؟ \n"))
    mki=price_dahp*km_gram_dahp
    mkl=mki*(nespa/100)
    mjk=mkl+mki
    print(f"اذن ال{km_gram_dahp}جرام دهب= {mjk}{omla_aee}")
    print("شكرا لاستخدامك برنامج معاذ البغدادي")
else :
    print("هناك خطا ما اعد االمحاوله")
    print("شكرا لاستخدامك برنامج معاذ البغدادي")
