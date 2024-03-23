import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from PIL import Image
import seaborn as sb

#read in data
ddd = pd.read_csv('./nnBrBr_long_2min_200.csv')

#read image used as background
img = np.asarray(Image.open('./AVG_CamMod_1_right_20220930_115508.png'))

#restructure data
dd = pd.wide_to_long(ddd, stubnames=['x_', 'y_'], i=['animal_id', 'time'], j='obs')

dd = dd.reset_index()

#split data according to animal id
dd_B1 = dd[dd['animal_id'] == 1].dropna()
dd_B2 = dd[dd['animal_id'] == 2].dropna()

# plot on top of image
plt.imshow(img)
plt.scatter(dd_B1[['x_']], dd_B1['y_'], s=1, alpha=0.05, c='b')
plt.savefig('B1_heatmap' + '.png')

plt.clf()

# plot on top of image
plt.imshow(img)
plt.scatter(dd_B2[['x_']], dd_B2['y_'], s=1, alpha=0.05, c='r')
plt.savefig('B2_heatmap' + '.png')

plt.clf()

## plot for dates
d1 = datetime(2022, 8, 31)
d2 = datetime(2022, 9, 30)

dd['time'] = dd.apply(lambda x: datetime.strptime(x['time'], '%Y-%m-%d %H:%M:%S'), axis=1)
dd['date_range'] = np.where(dd['time'] <= d1, 0,
                   np.where((dd['time'] > d1) & (dd['time'] <= d2), 1,
                   np.where(dd['time'] > d2, 2, np.nan)))


for d in [0, 1, 2]:
    for aid in [1, 2]:
        print("Animal: ", aid, "Date_range: ", d)
        df_rnr1 = dd[dd['animal_id'] == aid]
        df_rnr = df_rnr1[df_rnr1['date_range'] == d]

        plt.imshow(img)
        plt.scatter(df_rnr[['x_']], df_rnr['y_'], s=1, alpha=0.05, c=['b', 'r'][aid-1])
        plt.savefig('dates_heatmap_B' + str(aid) + '_' + str(d) + '.png')
        plt.clf()