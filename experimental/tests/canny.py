from __init__ import *

#Solo funciona con GrayScaleProcessor
visualizer = CamSource(
	Window(processors=[
		CannyProcessor()
	]),
	DebugWindow()
)
visualizer.show()
