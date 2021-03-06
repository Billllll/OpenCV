from astropy.io import fits
import cv2
import numpy as np

fitsFile="../examples/Filters/frame-i-002830-6-0398.fits"
hdulist = fits.open(fitsFile)
img = hdulist[0].data


Min=abs(np.amin(img))
Max=np.amax(img)
img = 255*(img+Min)/Max
imgFiltered=cv2.filter2D(img,-1,np.array([[0,1,0],[1,0,1],[0,1,0]]))

_,binary=cv2.threshold(imgFiltered, cv2.THRESH_OTSU, 1.0, cv2.THRESH_BINARY_INV)
cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
cv2.imshow("Image",binary)
cv2.waitKey()
