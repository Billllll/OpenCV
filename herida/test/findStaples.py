import cv2
import numpy as np
import sys
from glob import glob
import math
import pickle
from time import clock
from _utils import *
from _findStaples import *
from _getContours import *
from _squareHistogram import *

def dummy(x):
	global changeParam
	changeParam = True
	print x

# def stapleContThresh(img,dirList,thresh):
# 	threshChan = thresholdChannels(img,thresh)
# 	return stapleCont(threshChan,dirList)

# def stapleContCanny(img,dirList,cannyList):
# 	threshChan = simpleCanny(img,cannyList)
# 	return stapleCont(threshChan,dirList)

# def stapleContBlurAT(img,dirList,blatList):
# 	threshChan = blurAndAT(img,blatList)
# 	return stapleCont(threshChan,dirList)

def doAndPack(img,dirList,thresh,cannyList,blatList,relevanceThresh):
	print 'NEW IMAGE'
	print 'current time: '+str(clock())

	h, w = 375,450
	
	#get different formats of the original image	
	aux = []
	for channel in cv2.split(img):
		aux.append(cv2.equalizeHist(channel))

	backEqImg = cv2.merge(aux)
	
	#apply the image in the format that suits best to the different algorithms 
	aux = []
	print 'BEFORE GETTING THE CONTOURS'
	myTime = clock()
	print 'first contour at: '+str(clock())
	aux.append(stapleContCanny(backEqImg,dirList,cannyList))
	print '====>takes '+str(clock()-myTime)
	myTime = clock()
	print 'second contour at: '+str(clock())
	aux.append(stapleContThresh(img,dirList,thresh))
	print '====>takes '+str(clock()-myTime)
	myTime = clock()
	print 'third contour at: '+str(clock())
	aux.append(stapleContBlurAT(backEqImg,dirList,blatList))
	print '====>takes '+str(clock()-myTime)
	myTime = clock()

	#paint the contours for showing them later
	print 'paint the contours '+str(clock())
	cpImg0,cpImg1,cpImg2 = backEqImg.copy(),img.copy(),backEqImg.copy()
	percent = 0.01
	line = int(min(img.shape[0]*percent,img.shape[1]*percent))
	cv2.drawContours(cpImg0, aux[0], -1, (0,0,255),line)
	cv2.drawContours(cpImg1, aux[1], -1, (0,0,255),line)
	cv2.drawContours(cpImg2, aux[2], -1, (0,0,255),line)
	print '====>takes '+str(clock()-myTime)
	myTime = clock()

	#get the squareHistogram for all the contours, see _squareHistogram.getSigSquare
	print 'get significant squares '+str(clock())
	img5,sqHist5 = getSigSquares(aux,img.shape,(10,10),relevanceThresh)
	print '====>takes '+str(clock()-myTime)
	myTime = clock()


	img5 = cv2.merge([cv2.min(img5,layer) for layer in cv2.split(backEqImg)])

	print 'build the canvas'
	background = np.zeros((h*2,w*3,3),np.uint8)
	background[0:h,0:w,0:3]=cv2.resize(img,(w,h))
	background[0:h,w:2*w,0:3]=cv2.resize(backEqImg,(w,h))
	background[0:h,2*w:3*w,0:3]=cv2.resize(img5,(w,h))

	background[h:2*h,0:w,0:3]=cv2.resize(cpImg0,(w,h))
	background[h:2*h,w:2*w,0:3]=cv2.resize(cpImg1,(w,h))
	background[h:2*h,2*w:3*w,0:3]=cv2.resize(cpImg2,(w,h))
	print '====>takes '+str(clock()-myTime)
	myTime = clock()

	return background



def findStaplesMethod(imgIndex,imageNames,parameterDict):
	global changeParam

	img = cv2.imread(imageNames[imgIndex])
	imgParameters = parameterDict[imageNames[imgIndex]]
	
	dirList = imgParameters['direction']
	blatList = imgParameters['blat'] 
	cannyList =imgParameters['canny']
	thresh = imgParameters['thresh']
	relevanceThresh = imgParameters['relevanceThresh']
	
	
	background = doAndPack(img,dirList,thresh,cannyList,blatList,relevanceThresh)
	
	changeParam = False
	changeImg = False
	edit = False
	while True:
		if changeImg:	
			imgParameters = parameterDict[imageNames[imgIndex]]

			dirList = imgParameters['direction']
			blatList = imgParameters['blat'] 
			cannyList =imgParameters['canny']
			thresh = imgParameters['thresh']
			relevanceThresh = imgParameters['relevanceThresh']

			background = doAndPack(img,dirList,thresh,cannyList,blatList,relevanceThresh)

			changeImg=False

		if changeParam:
			dirList = [cv2.getTrackbarPos('minArea','panel direction'),
				cv2.getTrackbarPos('maxArea','panel direction'),
				cv2.getTrackbarPos('direction','panel direction')]
		
			cannyList = [cv2.getTrackbarPos('canny thresh1','panel canny'),
				cv2.getTrackbarPos('canny thresh2','panel canny')]

			blatList = [cv2.getTrackbarPos('iterations','panel blat'),
				(cv2.getTrackbarPos('ksizeBlur X','panel blat'),cv2.getTrackbarPos('ksizeBlur Y','panel blat')),
				cv2.getTrackbarPos('ksizeAT','panel blat')]

			thresh = cv2.getTrackbarPos('thresh','panel findStaples')
			relevanceThresh = cv2.getTrackbarPos('relevanceThresh','panel findStaples')
			
			background = doAndPack(img,dirList,thresh,cannyList,blatList,relevanceThresh)
			
			changeParam = False


		cv2.imshow('findStaples',background)
		
		key = cv2.waitKey(5)
		if (key==120):#x to move to the right
	 		imgIndex = (imgIndex+1,imgIndex)[imgIndex==(len(imageNames)-1)]
	 		img = cv2.imread(imageNames[imgIndex])
	 		changeImg = True
	 	elif (key==122):#z to move to the left
	 		imgIndex = (imgIndex-1,imgIndex)[imgIndex==0]
	 		img = cv2.imread(imageNames[imgIndex])
	 		changeImg = True
		elif (key==101):#e to enter or exit edit mode
			if not edit:
				cv2.namedWindow('panel findStaples',cv2.cv.CV_WINDOW_NORMAL)
				cv2.namedWindow('panel canny',cv2.cv.CV_WINDOW_NORMAL)
				cv2.namedWindow('panel blat',cv2.cv.CV_WINDOW_NORMAL)
				cv2.namedWindow('panel direction',cv2.cv.CV_WINDOW_NORMAL)
				cv2.createTrackbar('minArea','panel direction',5,500,dummy)
				cv2.createTrackbar('maxArea','panel direction',5000,5000,dummy)
				cv2.createTrackbar('direction','panel direction',5,5,dummy)
				cv2.createTrackbar('canny thresh1','panel canny',500,700,dummy)
				cv2.createTrackbar('canny thresh2','panel canny',700,700,dummy)
				cv2.createTrackbar('iterations','panel blat',1,10,dummy)
				cv2.createTrackbar('ksizeBlur X','panel blat',3,4,dummy)
				cv2.createTrackbar('ksizeBlur Y','panel blat',3,4,dummy)
				cv2.createTrackbar('ksizeAT','panel blat',2,4,dummy)
				cv2.createTrackbar('relevanceThresh','panel findStaples',2,3,dummy)
				cv2.createTrackbar('thresh','panel findStaples',180,255,dummy)
				edit = True
			else:
				cv2.destroyWindow('panel findStaples')
				cv2.destroyWindow('panel canny')
				cv2.destroyWindow('panel blat')
				cv2.destroyWindow('panel direction')

				imgParameters = parameterDict[imageNames[imgIndex]]
				dirList = imgParameters['direction']
				blatList = imgParameters['blat'] 
				cannyList =imgParameters['canny']
				thresh = imgParameters['thresh']
				relevanceThresh = imgParameters['relevanceThresh']
				
				edit = False
				changeParam = False
				changeImg = True

		elif (key == 115):#s to save the selected parameters
			parameter = {'direction':dirList , 'blat':blatList ,
	 		 'canny':cannyList , 'thresh':cv2.getTrackbarPos('thresh','panel findStaples') ,
	 		 'relevanceThresh':cv2.getTrackbarPos('relevanceThresh','panel findStaples')}
	 		parameterDict[imageNames[imgIndex]]=parameter
			f = open('parameters','w')
	 		pickle.dump(parameterDict,f)
	 		f.close()

		elif (key==113):#q to exit
	 		cv2.destroyWindow('panel findStaples')
			cv2.destroyWindow('panel canny')
			cv2.destroyWindow('panel blat')
			cv2.destroyWindow('panel direction')
	 		cv2.destroyWindow('findStaples')
	 		break





if __name__ == "__main__":
	print 'this script finds all the contours of a'
	print 'specified area and orientation and cuts'
	print 'the tiles containing them out of the original image'
	print 'not connected tiles are blended'
	print ''
	print 'press z and x to move through the images'
	print 'press e to enter and exit edit mode'
	print 'press s to save the selected parameters during edit mode'
	print 'press q to quit'

	path = '../images/*.jpg'
	imageNames = glob(path)
	imgIndex = 0
	img = cv2.imread(imageNames[imgIndex])	
	
	f = open('parameters','r')
	parameterDict = pickle.load(f)
	f.close()

	findStaplesMethod(imgIndex,imageNames,parameterDict)
	




	
