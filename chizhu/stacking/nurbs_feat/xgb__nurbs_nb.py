
# coding: utf-8

# In[1]:


import pandas as pd
import seaborn as sns
import numpy as np
from tqdm import tqdm
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import lightgbm as lgb
from datetime import datetime,timedelta  
import matplotlib.pyplot as plt
import time
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
# get_ipython().run_line_magic('matplotlib', 'inline')

#add
import gc
from sklearn import preprocessing
from sklearn.feature_extraction.text import TfidfVectorizer

from scipy.sparse import hstack, vstack
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import cross_val_score
# from skopt.space import Integer, Categorical, Real, Log10
# from skopt.utils import use_named_args
# from skopt import gp_minimize
from gensim.models import Word2Vec, FastText
import gensim 
import re
import os
path="./feature/"##nurbs概率文件路径
o_path="/dev/shm/chizhu_data/data/"###原始文件路径
os.listdir(path)


# In[2]:


sex_feat=pd.read_csv(path+"feature_sex_all.csv")
age_feat=pd.read_csv(path+"feature_age_all.csv")
# all_feat=pd.read_csv(path+"feature_22_all.csv")
train_id=pd.read_csv(o_path+"deviceid_train.tsv",sep="\t",names=['device_id','sex','age'])
test_id=pd.read_csv(o_path+"deviceid_test.tsv",sep="\t",names=['device_id'])
all_id=pd.concat([train_id[['device_id']],test_id[['device_id']]])
all_id.index=range(len(all_id))
sex_feat['device_id']=all_id
age_feat['device_id']=all_id
# deepnn_feat=pd.read_csv(path+"deepnn_fix.csv")
# deepnn_feat['device_id']=deepnn_feat['DeviceID']
# del deepnn_feat['DeviceID']


# In[3]:


train=pd.merge(train_id,sex_feat,on="device_id",how="left")
# train=pd.merge(train,deepnn_feat,on="device_id",how="left")
test=pd.merge(test_id,sex_feat,on="device_id",how="left")
# test=pd.merge(test,deepnn_feat,on="device_id",how="left")


# In[4]:


features = [x for x in train.columns if x not in ['device_id', 'sex',"age",]]
Y = train['sex'] - 1


# In[5]:



import xgboost as xgb
from sklearn.metrics import auc, log_loss, roc_auc_score,f1_score,recall_score,precision_score
from sklearn.cross_validation import StratifiedKFold

kf = StratifiedKFold(Y, n_folds=10, shuffle=True, random_state=1024)
params={
	'booster':'gbtree',
    "tree_method":"gpu_hist",
    "gpu_id":"2",
	'objective': 'binary:logistic',
#      'is_unbalance':'True',
# 	'scale_pos_weight': 1500.0/13458.0,
        'eval_metric': "logloss",
    
	'gamma':0.2,#0.2 is ok
	'max_depth':6,
# 	'lambda':20,
    # "alpha":5,
        'subsample':0.7,
        'colsample_bytree':0.4 ,
#         'min_child_weight':2.5, 
        'eta': 0.01,
    # 'learning_rate':0.01,
    "silent":1,
	'seed':1024,
	'nthread':12,
   
    }
num_round = 3500
early_stopping_rounds = 100


# In[6]:


aus = []
sub1 = np.zeros((len(test), ))
pred_oob1=np.zeros((len(train),))
for i,(train_index,test_index) in enumerate(kf):
  
    tr_x = train[features].reindex(index=train_index, copy=False)
    tr_y = Y[train_index]
    te_x = train[features].reindex(index=test_index, copy=False)
    te_y = Y[test_index]

    # tr_y=tr_y.apply(lambda x:1 if x>0 else 0)
    # te_y=te_y.apply(lambda x:1 if x>0 else 0)
    d_tr = xgb.DMatrix(tr_x, label=tr_y)
    d_te = xgb.DMatrix(te_x, label=te_y)
    watchlist  = [(d_tr,'train'),
    (d_te,'val')
             ]
    model = xgb.train(params, d_tr, num_boost_round=5500, 
                      evals=watchlist,verbose_eval=200,
                              early_stopping_rounds=100)
    pred = model.predict(d_te,ntree_limit=model.best_iteration)
    pred_oob1[test_index] =pred
    # te_y=te_y.apply(lambda x:1 if x>0 else 0)
    a = log_loss(te_y, pred)

    sub1 += model.predict(xgb.DMatrix(test[features]),ntree_limit=model.best_iteration)/10
    

    print ("idx: ", i) 
    print (" loss: %.5f" % a)
#     print " gini: %.5f" % g
    aus.append(a)

print ("mean")
print ("auc:       %s" % (sum(aus) / 10.0))


# In[7]:


pred_oob1 = pd.DataFrame(pred_oob1, columns=['sex2'])
sub1 = pd.DataFrame(sub1, columns=['sex2'])
res1=pd.concat([pred_oob1,sub1])
res1['sex1'] = 1-res1['sex2']


# In[8]:


import gc
gc.collect()


# In[9]:


train=pd.merge(train_id,age_feat,on="device_id",how="left")
# train=pd.merge(train,deepnn_feat,on="device_id",how="left")
test=pd.merge(test_id,age_feat,on="device_id",how="left")
# test=pd.merge(test,deepnn_feat,on="device_id",how="left")


# In[10]:


####sex1
test['sex']=1


# In[11]:


features = [x for x in train.columns if x not in ['device_id',"age"]]
Y = train['age'] 


# In[12]:


import lightgbm as lgb
import xgboost as xgb
from sklearn.metrics import auc, log_loss, roc_auc_score,f1_score,recall_score,precision_score
from sklearn.model_selection import StratifiedKFold

kf = StratifiedKFold(Y, n_splits=10, shuffle=True, random_state=1024)
params={
	'booster':'gbtree',
     "tree_method":"gpu_hist",
    "gpu_id":"2",
	'objective': 'multi:softprob',
#      'is_unbalance':'True',
# 	'scale_pos_weight': 1500.0/13458.0,
        'eval_metric': "mlogloss",
    'num_class':11,
	'gamma':0.1,#0.2 is ok
	'max_depth':6,
# 	'lambda':20,
    # "alpha":5,
        'subsample':0.7,
        'colsample_bytree':0.4 ,
        # 'min_child_weight':2.5, 
        'eta': 0.01,
    # 'learning_rate':0.01,
    "silent":1,
	'seed':1024,
	'nthread':12,
   
    }
num_round = 3500
early_stopping_rounds = 100


# In[13]:


aus = []
sub2 = np.zeros((len(test),11 ))
pred_oob2=np.zeros((len(train),11))
models=[]
iters=[]
for i,(train_index,test_index) in enumerate(kf):
  
    tr_x = train[features].reindex(index=train_index, copy=False)
    tr_y = Y[train_index]
    te_x = train[features].reindex(index=test_index, copy=False)
    te_y = Y[test_index]

    # tr_y=tr_y.apply(lambda x:1 if x>0 else 0)
    # te_y=te_y.apply(lambda x:1 if x>0 else 0)
    d_tr = xgb.DMatrix(tr_x, label=tr_y)
    d_te = xgb.DMatrix(te_x, label=te_y)
    watchlist  = [(d_tr,'train'),
    (d_te,'val')
             ]
    model = xgb.train(params, d_tr, num_boost_round=5500, 
                      evals=watchlist,verbose_eval=200,
                              early_stopping_rounds=100)
    models.append(model)
    iters.append(model.best_iteration)
    pred = model.predict(d_te,ntree_limit=model.best_iteration)
    pred_oob2[test_index] =pred
    # te_y=te_y.apply(lambda x:1 if x>0 else 0)
    a = log_loss(te_y, pred)

    sub2 += model.predict(xgb.DMatrix(test[features]),ntree_limit=model.best_iteration)/10
    

    print ("idx: ", i) 
    print (" loss: %.5f" % a)
#     print " gini: %.5f" % g
    aus.append(a)

print ("mean")
print ("auc:       %s" % (sum(aus) / 10.0))


# In[14]:


res2_1=np.vstack((pred_oob2,sub2))
res2_1 = pd.DataFrame(res2_1)


# In[15]:


###sex2
test['sex']=2
features = [x for x in train.columns if x not in ['device_id',"age"]]
Y = train['age'] 


# In[16]:


aus = []
sub2 = np.zeros((len(test),11 ))
for model,it in zip(models,iters):
    sub2 += model.predict(xgb.DMatrix(test[features]),ntree_limit=it)/10
res2_2=np.vstack((pred_oob2,sub2))
res2_2 = pd.DataFrame(res2_2) 


# In[17]:


res1.index=range(len(res1))
res2_1.index=range(len(res2_1))
res2_2.index=range(len(res2_2))
final_1=res2_1.copy()
final_2=res2_2.copy()
for i in range(11):
    final_1[i]=res1['sex1']*res2_1[i]
    final_2[i]=res1['sex2']*res2_2[i]
id_list=pd.concat([train[['device_id']],test[['device_id']]])
final=id_list
final.index=range(len(final))
final.columns= ['DeviceID']
final_pred = pd.concat([final_1,final_2],1)
final=pd.concat([final,final_pred],1)
final.columns = ['DeviceID', '1-0', '1-1', '1-2', '1-3', '1-4', '1-5', '1-6', 
         '1-7','1-8', '1-9', '1-10', '2-0', '2-1', '2-2', '2-3', '2-4', 
         '2-5', '2-6', '2-7', '2-8', '2-9', '2-10']

final.to_csv('xgb_feat_nurbs_nb_10fold.csv', index=False)


# In[18]:


test['DeviceID']=test['device_id']
sub=pd.merge(test[['DeviceID']],final,on="DeviceID",how="left")
sub.to_csv("xgb_nurbs_nb_10fold.csv",index=False)

