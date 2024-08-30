data = [-1, -1, -1, 1, 1, 1, 1, 1, -1, 1, -1, -1, -1, 1, 1, -1, 1, 1, -1, 1, -1, 0, -1, 1, 1, -1, -1, -1, -1, -1, 1, -1, -1, 1, -1, 1, -1, 1, 1, -1, 1, 1, 0, 0]

def is_continous(entry, item):
    return (entry > 0 and item > 0) or (entry < 0 and item < 0)

def group_data(data):
     result = []
     tmp = []
     entry = None

     for idx,item in enumerate(data):
          if idx < len(data) - 1:
                next_item = data[idx + 1]
          else:
               next_item = None   
          if entry is None:
                entry = item
          if is_continous(entry, item):
               tmp.append(item) 
          if next_item is not None:     
               if is_continous(entry, next_item) == False:
                    result.append(tmp)
                    tmp = [] # reset tmp
                    entry = None   # update new entry   
          else:
               result.append(tmp)
     return result          
                              
raw_result = group_data(data)
       

result = []           

for i in raw_result:
     index = 0
     if len(i) == 0:
       result.append(0)
     while index < len(i):
          result.append(sum(i))
          i.pop(index)  
            
        
print(data)
print(result)
                          
      
     
             


    
       
          
           


          



