# -*- coding: utf-8 -*-
from astropy.io import fits
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import cv2
import sys
import numpy as np


fitsFileI="frame-i-004264-4-0259.fits" #m81 http://mirror.sdss3.org/fields/name?name=m81
fitsFileU="frame-u-004264-4-0259.fits" #m81
fitsFileR="frame-r-004264-4-0259.fits" #m81 
fitsFileG="frame-g-004264-4-0259.fits" #m81
f1="f1.jpg"
fitsFileI2="frame-i-003804-6-0084.fits" #m66 http://mirror.sdss3.org/fields/name?name=m66
fitsFileU2="frame-u-003804-6-0084.fits" #m66
fitsFileR2="frame-r-003804-6-0084.fits" #m66
fitsFileG2="frame-g-003804-6-0084.fits" #m66
fitsFileI3='frame-i-004381-2-0120.fits' #m91 http://mirror.sdss3.org/fields/name?name=m91
fitsFileI4='frame-i-002830-6-0398.fits' #m109 http://mirror.sdss3.org/fields/name?name=m109
fitsFileI5='frame-i-003805-2-0023.fits' #m59 http://mirror.sdss3.org/fields/name?name=m59
fitsFileI6='frame-i-008112-2-0074.fits' #m33 http://mirror.sdss3.org/fields/name?name=m33
fitsFileI7='frame-i-007845-2-0104.fits' #m74 http://mirror.sdss3.org/fields/name?name=m74
fitsFileI8='frame-i-003836-4-0084.fits' #m95 http://mirror.sdss3.org/fields/name?name=m95
dataset={'i':fitsFileI,'u':fitsFileU,'r':fitsFileR,'g':fitsFileG,'1':f1,'i2':fitsFileI2,'u2':fitsFileU2,'r2':fitsFileR2,'g2':fitsFileG2,'i3':fitsFileI3,'i4':fitsFileI4,'i5':fitsFileI5,'i6':fitsFileI6,'i7':fitsFileI7,'i8':fitsFileI8}

if len(sys.argv)==2:
	data = fits.getdata(dataset[sys.argv[1]])
	#print header
	hdu_list = fits.open(dataset[sys.argv[1]])
	#hdu_list.info()
	img = hdu_list[0].data
	Min=np.amin(img)
	Max=np.amax(img)
	img = 255*(img+abs(Min))/Max
#else:
#	img=255*cv2.imread(dataset[sys.argv[1]],0)

print img.shape,type(img),np.amax(img),np.amin(img)

#cv2.namedWindow("img", cv2.WINDOW_NORMAL)
#cv2.imshow('img',img)

#plt.imshow(img,cmap='spectral', norm=LogNorm(), origin='lower')
#plt.show()


imgBlur = cv2.blur(img,(3,3))
print "BLUR: ",imgBlur.shape,type(imgBlur),np.amax(imgBlur),np.amin(imgBlur)
#cv2.namedWindow("imgBlur", cv2.WINDOW_NORMAL)
#cv2.imshow('imgBlur',imgBlur)


imgFiltered=cv2.filter2D(img,-1,np.array([[0,1,0],[1,0,1],[0,1,0]]))
print "CUSTOM FILTER: ",imgFiltered.shape,type(imgFiltered),np.amax(imgFiltered),np.amin(imgFiltered)
#cv2.namedWindow("imgFiltered", cv2.WINDOW_NORMAL)
#cv2.imshow('imgFiltered',imgFiltered)


imgGB=cv2.GaussianBlur(img,(3,3),1)
print "G. BLUR: ",imgGB.shape,type(imgGB),np.amax(imgGB),np.amin(imgGB)
#cv2.namedWindow("imgGB", cv2.WINDOW_NORMAL)
#cv2.imshow('imgGB',imgGB)


imgM=cv2.morphologyEx(img, cv2.MORPH_GRADIENT,(3,3))
print "MORPH:", imgM.shape,type(imgM),np.amax(imgM),np.amin(imgM)
#cv2.namedWindow("imgM", cv2.WINDOW_NORMAL)
#cv2.imshow('imgM',imgM)


imgL=cv2.Laplacian(img,-1)
print "LAPLACIAN:",imgL.shape,type(imgL),np.amax(imgL),np.amin(imgL)
#cv2.namedWindow("imgL", cv2.WINDOW_NORMAL)
#cv2.imshow('imgL',imgL)


imgS=cv2.Sobel(img,-1,3,2,ksize=5)
print "SOBEL:", imgS.shape,type(imgS),np.amax(imgS),np.amin(imgS)
#cv2.namedWindow("imgS", cv2.WINDOW_NORMAL)
#cv2.imshow('imgS',imgS)



imgH=cv2.cornerHarris(img,3,3,0.0005)
print "HARRIS: ",imgH.shape,type(imgH),np.amax(imgH),np.amin(imgH)
#cv2.namedWindow("imgH", cv2.WINDOW_NORMAL)
#cv2.imshow('imgH',imgH)

#imgSk = imgFiltered
#size = np.size(imgSk)
#skel = np.zeros(imgSk.shape,np.uint8)
 
#ret,imgSk = cv2.threshold(imgSk,127,255,0)
#element = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
#done = False
 
#while( not done):
#    eroded = cv2.erode(imgSk,element)
#    temp = cv2.dilate(eroded,element)
#    temp = cv2.subtract(imgSk,temp)
#    skel = cv2.bitwise_or(skel,temp)
#    imgSk = eroded.copy()
# 
#    zeros = size - cv2.countNonZero(imgSk)
#    if zeros==size:
#        done = True
#cv2.namedWindow("skel", cv2.WINDOW_NORMAL) 
#cv2.imshow("skel",skel)

row1 = np.concatenate((img, imgBlur, imgFiltered),axis=1)
row2 = np.concatenate((imgGB, imgM, imgL),axis=1)
row3 = np.concatenate((imgS, imgH,np.zeros(img.shape)),axis=1)
img_collage=np.concatenate((row1,row2,row3),axis=0)

cv2.putText(img_collage,'Base image',(2048*2+10,1489*2+250), cv2.FONT_HERSHEY_SIMPLEX, 3,(255,255,255),2)
cv2.putText(img_collage,'Blur',(7*2048/3+10,1489*2+250), cv2.FONT_HERSHEY_SIMPLEX, 3,(255,255,255),2)
cv2.putText(img_collage,'Custom filter',(8*2048/3+10,1489*2+250), cv2.FONT_HERSHEY_SIMPLEX, 3,(255,255,255),2)

cv2.putText(img_collage,'Gaussian blur',(2048*2+10,7*1489/3+250), cv2.FONT_HERSHEY_SIMPLEX, 3,(255,255,255),2)
cv2.putText(img_collage,'Morphological',(7*2048/3+10,7*1489/3+250), cv2.FONT_HERSHEY_SIMPLEX, 3,(255,255,255),2)
cv2.putText(img_collage,'Laplacian',(8*2048/3+10,7*1489/3+250), cv2.FONT_HERSHEY_SIMPLEX, 3,(255,255,255),2)

cv2.putText(img_collage,'Sobel',(2048*2+10,8*1489/3+250), cv2.FONT_HERSHEY_SIMPLEX, 3,(255,255,255),2)
cv2.putText(img_collage,'Harris',(7*2048/3+10,8*1489/3+250), cv2.FONT_HERSHEY_SIMPLEX, 3,(255,255,255),2)


cv2.line(img_collage,(2048,0),(2048,1489*3),(255,255,255),2)
cv2.line(img_collage,(7*2048/3,1489*2),(7*2048/3,1489*3),(255,255,255),2)

cv2.line(img_collage,(2048*2,0),(2048*2,1489*3),(255,255,255),2)
cv2.line(img_collage,(8*2048/3,1489*2),(8*2048/3,1489*3),(255,255,255),2)

cv2.line(img_collage,(0,1489),(2048*3,1489),(255,255,255),2)
cv2.line(img_collage,(2048*2,7*1489/3),(2048*3,7*1489/3),(255,255,255),2)

cv2.line(img_collage,(0,1489*2),(2048*3,1489*2),(255,255,255),2)
cv2.line(img_collage,(2048*2,8*1489/3),(2048*3,8*1489/3),(255,255,255),2)


cv2.namedWindow("Image collage", cv2.WINDOW_NORMAL)
cv2.imshow("Image collage", img_collage)
cv2.waitKey(10) & 0xFF

'''
while True:
	cv2.imshow("Image collage", img_collage)
	k = cv2.waitKey(10) & 0xFF
	if k == 27:
		cv2.destroyAllWindows()
		break
'''


def nada(x):
	print x/100.
def nada2(t):
	print "Threshold used:", Thresholds[t]
def nada3(t):
	print "Filter used as base image:", Filters[t]
cv2.namedWindow("binary", cv2.WINDOW_NORMAL)
cv2.createTrackbar('thresh', 'binary', 0, 200, nada)
thresholds=[cv2.THRESH_BINARY,cv2.THRESH_BINARY_INV,cv2.THRESH_TRUNC,cv2.THRESH_TOZERO,cv2.THRESH_TOZERO_INV]
Thresholds=['Binary', 'Binary_inv', 'Trunc', 'Tozero','Tozero_inv']
filters=[img, imgBlur, imgFiltered, imgGB, imgM, imgL, imgH]
Filters=['Raw image', 'Blur', 'Custom filter','Gaussian blur', 'Morph', 'Laplacian', 'Harris corner']
nada2(0)
nada3(0)
cv2.createTrackbar('threshold type', 'binary', 0, 4, nada2)
cv2.createTrackbar('filter', 'binary', 0, 6, nada3)

while True:
	thresh=cv2.getTrackbarPos('thresh', 'binary')
	threshold=cv2.getTrackbarPos('threshold type', 'binary')
	base_image=cv2.getTrackbarPos('filter', 'binary')
	_,binary=cv2.threshold(filters[base_image], cv2.THRESH_OTSU, thresh/100., thresholds[threshold])
	#print "BINARY:", binary.shape,type(binary),np.amax(binary),np.amin(binary)
	cv2.namedWindow("binary", cv2.WINDOW_NORMAL)
	cv2.imshow("binary",binary)
	#cv2.imwrite('a.png',255* binary)
	k = cv2.waitKey(1) & 0xFF
	if k == 27:
		break


cv2.destroyAllWindows()
#plt.close()



#hdu_list.close()