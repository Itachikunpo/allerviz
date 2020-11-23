import pickle
import numpy as np
from scipy.sparse import csr_matrix
# from allergen_classifier_model import model

model = pickle.load(open('model.pkl','rb'))

###This function cleans the transformed description
def rcv(self,lem):
    if type(lem)==float:
        return lem
    else:
        a=lem.split()
        c=[i.replace('(',"").replace(')',"").replace(',',"") for i in a]
        b=[]
        for i in c:
            if i!=':':
                b.append(i)
        row= [int(float(b[x])) for x in range(0, len(b), 3)]
        column= [int(float(b[x])) for x in range(1, len(b), 3)]
        value= [float(b[x]) for x in range(2, len(b), 3)]
        final_list=[np.array(row),np.array(column),np.array(value)]

        return final_list

###This formula returns a single allergy score for a menu item
def predict_single(self, test):
    for i in test:
        adapted=rcv(i['transformed_desc'])
        sparseMatrix = csr_matrix((adapted[2], (adapted[0], adapted[1])),shape = (1, 25000)).tocsr()
        prediction = model.predict(sparseMatrix)
        i['allergy_score'] = np.mean(csr_matrix((prediction), shape=(1, 8)).toarray())
    return test

###This formula returns a tuple for a menu item: (allergy_score, [0,1,0,0,0,0,0,0]
def predict_tuple(self, test):
    for i in test:
        adapted=rcv(i['transformed_desc'])
        sparseMatrix = csr_matrix((adapted[2], (adapted[0], adapted[1])),shape = (1, 25000)).tocsr()
        prediction = model.predict(sparseMatrix)
        i['allergy_score'] = (np.mean(csr_matrix((prediction), shape=(1, 8)).toarray()), csr_matrix((prediction), shape=(1, 8)).toarray())
    return test

###This formula returns averaged score for each restaurant, it loops through the dict
def generall_prediction(self, test):
    total=0
    for i in test:
        total+=i['allergy_score']
    total_score=total/len(i['menu'])
    return total_score
