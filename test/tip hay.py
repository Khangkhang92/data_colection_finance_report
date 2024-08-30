# temp = [-1, -1, -1, 1, 1, 1, 1, 1, -1, 1, -1, -1, -1, 1, 1, -1, 1, 1, -1, 1, -1, 0, -1, 1, 1, -1, -1, -1, -1, -1, 1, -1, -1, 1, -1, 1, -1, 1, 1, -1, 1, 1, 0, 0]
data = [-1, -1, -1, 1, 1, 1, 1, 1, -1, 1, -1, -1, -1, 1, 1, -1, 1, 1, -1, 1, -1]


result = []


# truong hop sai
# for i in data:
#    result.append(i)
#    data.pop(i)


# truong hop dung
index = 0
while index < len(data):
    result.append(data[index])
    data.pop(index)


print(data)
print(result)
              