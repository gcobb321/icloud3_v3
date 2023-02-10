a=[0,1,2,3,4,5]
curr_idx = 4
up_down='up'


if up_down == 'up':
  if curr_idx > 0:
    new_idx = curr_idx - 1
if up_down == 'down':
  if curr_idx< len(a):
    new_idx = curr_idx + 1
print(new_idx, curr_idx)
print(a)
a_save = a.pop(curr_idx)
a.insert(new_idx, a_save)
print(a)