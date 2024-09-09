from copy import deepcopy

# data = [-1, -1, -1, 1, 1, 1, 1, 1, -1, 1, -1, -1, -1, 1, 1, -1, 1, 1, -1, 1, -1, 0, -1, 1, 1, -1, -1, -1, -1, -1, 1, -1, -1, 1, -1, 1, -1, 1, 1, -1, 1, 1, 0, 0]
data = [-1, -1, -1, 1, 1, 1, 1, 1, -1, 1, -1, -1, -1, 1, 1, -1, 1, 1, -1, 1, -1]


result = []
tmp = []
entry = None


def is_continous(entry, item):
    return (entry > 0) == (item > 0)


for idx, item in enumerate(data):
    item = data[idx]
    if item == 0:
        result.append(item)
        entry = None
        #   tmp = []
        continue
    if entry is None:
        entry = item
    if is_continous(entry, item):
        tmp.append(item)
    else:
        tranfer = deepcopy(tmp)

        tmp = []  # reset tmp
        tmp.append(item)  # new again
        entry = item  # update new entry

        index = 0
        while index < len(tranfer):
            result.append(sum(tranfer))
            tranfer.pop(index)


print(data)
print(result)
