import matplotlib.pyplot as plt
import numpy as np

y1 = np.array( [3, 8, 1, 10] )
y2 = np.array([6, 2, 7, 11])

titlefont = {'family':'serif', 'color':'blue', 'size':20}
labelfont = {'color':'blue', 'size':14}

plt.title( "Kurse der DKB-Anleihen", fontdict=titlefont, loc='left' )
plt.xlabel( "Datum", fontdict=labelfont )
plt.ylabel( "Kurs", fontdict=labelfont )

plt.plot( y1, 'o:r' ) # means: fmt = o, :, r (marker='o', line is dotted, color is red)
plt.plot( y2, 'o:c' )

plt.grid()

plt.show()