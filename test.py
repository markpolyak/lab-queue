list = [['os-pol9k-14:00'],['fgh'],['Хмара']]
a = input('')
fl_list = []
for i in list:
    for item in i:
        fl_list.append(item)
        for y in fl_list:
            if y == a:
                print(y)



# li = [[10,20],[30,40]]
# flat_li = []
# for i in li:
#   for item in i:
#     flat_li.append(item)
# print("list before flattening", li)
# print ("flattened list: ",flat_li)