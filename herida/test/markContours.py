import cv2
import numpy as np
import sys
from glob import glob
import math
from time import clock
import pickle
from _utils import *
from _findStaples import *
from _getContours import *
from _squareHistogram import *
from _fleshBackProyection import *
from _findSpot import *

def dummy(x):
	global changeParam
	changeParam = True
	changeSeed = True
	print x

def dummy2(x):
	global changeSeed
	changeSeed = True
	print x

def doAndPack(img,dirList,thresh,cannyList,blatList,relevanceThresh,probThresh):
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

	
	#get the squareHistogram for all the contours, see _squareHistogram.getSigSquare
	print 'get significant squares '+str(clock())
	img5,sqHist5 = getSigSquares(aux,img.shape,(10,10),relevanceThresh)
	print '====>takes '+str(clock()-myTime)
	myTime = clock()


	#do backproyection for every non trivial entry in sqHist
	print 'backproyection '+str(clock())
	bpGeneral, bpComponent = bpSignificantSquares(img.copy(),sqHist5,probThresh)
	print '====>takes '+str(clock()-myTime)
	myTime = clock()

	print 'dilate '+str(clock())
	kernel = np.ones((3,3),np.uint8)*255
	bpComponentDilated = cv2.dilate(bpComponent.copy(),kernel,iterations=3,borderType=cv2.BORDER_CONSTANT,borderValue=0)
	#bpComponentDilated = cv2.erode(bpComponent.copy(),kernel,iterations=1,borderType=cv2.BORDER_CONSTANT,borderValue=0)
	print '====>takes '+str(clock()-myTime)

	blueShape = getBlueMask(img.copy(),cv2.split(bpComponentDilated)[0])

	
	print '====>takes '+str(clock()-myTime)
	myTime = clock()

	return blueShape


def markContoursMethod(imgIndex,imageNames,parameterDict):
	global changeParam
	global changeSeed
	global seedPoint
	img = cv2.imread(imageNames[imgIndex])
	imgParameters = parameterDict[imageNames[imgIndex]]
	
	dirList = imgParameters['direction']
	blatList = imgParameters['blat'] 
	cannyList =imgParameters['canny']
	thresh = imgParameters['thresh']
	relevanceThresh = imgParameters['relevanceThresh']
	probThresh = imgParameters['probThresh']

	cv2.namedWindow('floodfillImg',cv2.cv.CV_WINDOW_NORMAL)
	cv2.namedWindow('floodfillParams',cv2.cv.CV_WINDOW_NORMAL)
	cv2.createTrackbar('R','floodfillParams',0,255,dummy2)
	cv2.createTrackbar('G','floodfillParams',0,255,dummy2)
	cv2.createTrackbar('B','floodfillParams',255,255,dummy2)
	cv2.createTrackbar('loDiff','floodfillParams',1,100,dummy2)
	cv2.createTrackbar('upDiff','floodfillParams',1,100,dummy2)

	floodfillImg = doAndPack(img,dirList,thresh,cannyList,blatList,relevanceThresh,probThresh)
	
	changeParam = False
	changeImg = False
	edit = False

	floodfillImgCopy = floodfillImg.copy()
	floodfillImgDim = (900,750)
	seedPoint = (0,0)
	changeSeed = False

	def onmouse(event, x, y, flags, param):
		global seedPoint
		global changeSeed

		aux = (transform(x,y,floodfillImg.shape,floodfillImgDim))
		print 'aux point is '+str(aux)
		patch = cv2.pyrUp(cv2.getRectSubPix(floodfillImgCopy, (100,100), aux))
		cv2.circle(patch,(100,100),2,(0,0,255),1)
		cv2.imshow('zoom',patch)

		if flags and (event == cv2.EVENT_FLAG_LBUTTON):
			print 'click!!!'
			seedPoint = aux
			print 'seedPoint is '+str(seedPoint)
			changeSeed = True
			

	cv2.setMouseCallback('floodfillImg', onmouse)


	while True:
		if changeImg:	
			imgParameters = parameterDict[imageNames[imgIndex]]

			dirList = imgParameters['direction']
			blatList = imgParameters['blat'] 
			cannyList =imgParameters['canny']
			thresh = imgParameters['thresh']
			relevanceThresh = imgParameters['relevanceThresh']
			probThresh = cv2.getTrackbarPos('probabilityThresh','backproyection')
			floodfillImg = doAndPack(img,dirList,thresh,cannyList,blatList,relevanceThresh,probThresh)

			changeImg=False

		if changeParam and edit:
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
			probThresh = cv2.getTrackbarPos('probabilityThresh','backproyection')

			floodfillImg = doAndPack(img,dirList,thresh,cannyList,blatList,relevanceThresh,probThresh)
			floodfillImgCopy = floodfillImg.copy()
			changeParam = False
		
		if changeSeed:
			print 'in changeseed!!!'
			print 'seedPoint is '+str(seedPoint)
			floodfillImgCopy = floodfillImg.copy()
			mask = np.zeros((floodfillImgCopy.shape[0]+2,floodfillImgCopy.shape[1]+2),np.uint8)
			newVal = (cv2.getTrackbarPos('B','floodfillParams'),cv2.getTrackbarPos('G','floodfillParams'),cv2.getTrackbarPos('R','floodfillParams'))
			loDiff = [cv2.getTrackbarPos('loDiff','floodfillParams'),]*3
			upDiff = [cv2.getTrackbarPos('upDiff','floodfillParams'),]*3
			cv2.floodFill(floodfillImgCopy, mask, seedPoint, newVal, loDiff, upDiff)
			changeSeed = False

		
		cv2.imshow('floodfillImg',cv2.resize(floodfillImgCopy,floodfillImgDim))
		
		key = cv2.waitKey(5)
		if (key==120):#x to move to the right
	 		imgIndex = (imgIndex+1,imgIndex)[imgIndex==(len(imageNames)-1)]
	 		img = cv2.imread(imageNames[imgIndex])
	 		changeImg = True
	 		changeSeed = True
	 		seedPoint = (0,0)
	 	elif (key==122):#z to move to the left
	 		imgIndex = (imgIndex-1,imgIndex)[imgIndex==0]
	 		img = cv2.imread(imageNames[imgIndex])
	 		changeImg = True
	 		changeSeed = True
	 		seedPoint = (0,0)
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
	 		 'canny':cannyList , 'thresh':thresh,
	 		 'relevanceThresh':relevanceThresh,
	 		 'probThresh':probThresh}
	 		parameterDict[imageNames[imgIndex]]=parameter
			f = open('parameters','w')
	 		pickle.dump(parameterDict,f)
	 		f.close()

	 	elif (key == 114):#r to remove the previous floodfills
	 		floodfillImgCopy = floodfillImg.copy()

	 	elif (key == 102):#f to fix the previous floodfills
	 		floodfillImg = floodfillImgCopy.copy()

		elif (key==113):#q to exit
	 		cv2.destroyWindow('panel findStaples')
			cv2.destroyWindow('panel canny')
			cv2.destroyWindow('panel blat')
			cv2.destroyWindow('panel direction')
	 		cv2.destroyWindow('floodfillImg')
	 		cv2.destroyWindow('floodfillParams')
	 		break



if __name__ == "__main__":
	print 'this script finds all the contours of a'
	print 'specified area and orientation and cuts'
	print 'the tiles containing them out of the original image'
	print 'not connected tiles are blended'
	print ''
	print 'use z and x to move through the images'

	path = '../images/*.jpg'
	imageNames = glob(path)
	imgIndex = 0
	img = cv2.imread(imageNames[imgIndex])	
	

	f = open('parameters','r')
	parametersDict = pickle.load(f)
	f.close()

	imgParams = parametersDict[imageNames[imgIndex]]


	cv2.namedWindow('panel',cv2.cv.CV_WINDOW_NORMAL)
	cv2.namedWindow('ffP',cv2.cv.CV_WINDOW_NORMAL)
	cv2.createTrackbar('probThresh','panel',1,256,dummy)
	cv2.createTrackbar('R','ffP',0,255,dummy2)
	cv2.createTrackbar('G','ffP',0,255,dummy2)
	cv2.createTrackbar('B','ffP',255,255,dummy2)
	cv2.createTrackbar('loDiff','ffP',1,100,dummy2)
	cv2.createTrackbar('upDiff','ffP',1,100,dummy2)



	changeParam = False

	blueShapeOriginal = doAndPack(img,imgParams['direction'],
		imgParams['thresh'],
		imgParams['canny'],
		imgParams['blat'],
		imgParams['relevanceThresh'],
		cv2.getTrackbarPos('probThresh','panel')
	)






	blueShapeCopy = blueShapeOriginal.copy()
	thresholdImage = blueShapeOriginal.copy()
	cv2.namedWindow('blueShape',cv2.cv.CV_WINDOW_NORMAL)
	blueShapeDim = (900,750)
	seedPoint = (0,0)
	changeSeed = False

	def onmouse(event, x, y, flags, param):
		global blueShapeOriginal
		global blueShapeCopy
		global seedPoint
		global changeSeed

		#blueShapeOriginal=blueShapeCopy.copy()
		aux = (transform(x,y,img.shape,blueShapeDim))
		patch = cv2.pyrUp(cv2.getRectSubPix(blueShapeCopy, (100,100), aux))
		cv2.circle(patch,(100,100),2,(0,0,255),1)
		cv2.imshow('zoom',patch)

		if flags & cv2.EVENT_FLAG_LBUTTON:
			seedPoint = aux
			changeSeed = True
			

	cv2.setMouseCallback('blueShape', onmouse)


	while True:
		

		if changeParam:
			imgParams = parametersDict[imageNames[imgIndex]]
			
			blueShapeOriginal = doAndPack(img,imgParams['direction'],
				imgParams['thresh'],
				imgParams['canny'],
				imgParams['blat'],
				imgParams['relevanceThresh'],
				cv2.getTrackbarPos('probThresh','panel')
			)

			blueShapeCopy = blueShapeOriginal.copy()
			changeParam = False

		if changeSeed:
			blueShapeCopy = blueShapeOriginal.copy()
			mask = np.zeros((blueShapeCopy.shape[0]+2,blueShapeCopy.shape[1]+2),np.uint8)
			newVal = (cv2.getTrackbarPos('B','ffP'),cv2.getTrackbarPos('G','ffP'),cv2.getTrackbarPos('R','ffP'))
			loDiff = [cv2.getTrackbarPos('loDiff','ffP'),]*3
			upDiff = [cv2.getTrackbarPos('upDiff','ffP'),]*3
			cv2.floodFill(blueShapeCopy, mask, seedPoint, newVal, loDiff, upDiff)
			changeSeed = False
			print 'out of changeseed'
			thresholdImage = blueShapeOriginal.copy()
			print 'VALOR: '+str(thresholdImage[seedPoint[1],seedPoint[0]][0])
			interval = (thresholdImage[seedPoint[1],seedPoint[0]][0]-loDiff[0],thresholdImage[seedPoint[1],seedPoint[0]][0]+upDiff[0])
			thresholdImage = intervalThresholdBinary(thresholdImage,interval)

		#cv2.imshow('original',bigImg)
		cv2.imshow('blueShape',cv2.resize(blueShapeCopy,blueShapeDim))
		cv2.imshow('threshold',cv2.resize(thresholdImage,blueShapeDim))



		key = cv2.waitKey(5)
	 	if (key==120):
	 		imgIndex = (imgIndex+1,imgIndex)[imgIndex==(len(imageNames)-1)]
	 		img = cv2.imread(imageNames[imgIndex])
	 		changeParam = True
	 		changeSeed = True
	 		seedPoint = (0,0)
	 	elif (key==122):
	 		imgIndex = (imgIndex-1,imgIndex)[imgIndex==0]
	 		img = cv2.imread(imageNames[imgIndex])
	 		changeParam = True
	 		changeSeed = True
	 		seedPoint = (0,0)
	 	elif (key == 114):
	 		blueShapeCopy = blueShapeOriginal.copy()
	 	elif (key == 115):
	 		blueShapeOriginal = blueShapeCopy.copy()
	 	elif (key != -1):
	 		break









	
