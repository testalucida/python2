import datetime
import matplotlib.pyplot as plt
from matplotlib.dates import drange
import numpy as np

d1 = datetime.datetime( 2021, 7, 2 )
d2 = datetime.datetime( 2021, 7, 12 )
delta = datetime.timedelta( hours=24 ) # delta: 1 day, 0:00:00
dates = drange( d1, d2, delta ) # contains a list containing 10 (?) num values representing a date each

titlefont = {'family':'serif', 'color':'blue', 'size':20}
labelfont = {'color':'blue', 'size':14}

plt.title( "Kurse der DKB-Anleihen", fontdict=titlefont, loc='left' )
#plt.xlabel( "Datum", fontdict=labelfont )
plt.ylabel( "Kurs", fontdict=labelfont )

#y = np.arange( len( dates ) )
#yy = y ** 3
kurse = [99.8, 100.0, 100.2, 99.4, 99.5, 100.8, 100.6, 101.0, 102.5, 99.1]
plt.plot_date( dates, kurse, fmt='o:r', label='Post' )
plt.gcf().autofmt_xdate()

plt.tick_params( axis='x', which='major', labelsize=8 )
plt.legend()
plt.tight_layout()
plt.grid()
plt.show()