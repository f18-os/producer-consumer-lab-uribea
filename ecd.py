#!/usr/bin/env python3

import threading
import cv2
import numpy as np
import base64


MAXBUFF = 10
#[1]
extractFull = threading.Semaphore(0)
extractEmpty = threading.Semaphore(MAXBUFF)
displayFull = threading.Semaphore(0)
displayEmpty = threading.Semaphore(MAXBUFF)


def extractFrames(fileName, outputBuffer):
    # Initialize frame count
    count = 0

    # open video file
    vidcap = cv2.VideoCapture(fileName)

    # read first image
    success, image = vidcap.read()

    while success:
        # get a jpg encoded frame
        success, jpgImage = cv2.imencode('.jpg', image)

        # encode the frame as base 64 to make debugging easier
        jpgAsText = base64.b64encode(jpgImage)

        extractEmpty.acquire()

        # add the frame to the buffer
        outputBuffer.put(jpgAsText)

        extractFull.release()

        success, image = vidcap.read()
        count += 1

    outputBuffer.put('e')



def convertFrames(inputBuffer, outputBuffer):
    count = 0
    while True and inputBuffer.peek() is not 'e':
    #[2]
        extractFull.acquire()

        # get the next frame
        frameAsText = inputBuffer.get()

        extractEmpty.release()

        # decode the frame
        jpgRawImage = base64.b64decode(frameAsText)

        # convert the raw frame to a numpy array
        jpgImage = np.asarray(bytearray(jpgRawImage), dtype=np.uint8)

        # convert to an image
        img = cv2.imdecode(jpgImage, cv2.IMREAD_UNCHANGED)

        # set image to grayscale
        grayscaleFrame = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # convert image to jpg
        success, jpgImage = cv2.imencode('.jpg', grayscaleFrame)

        # encode the frame
        jpgAsText = base64.b64encode(jpgImage)

        displayEmpty.acquire()
        
        # add the frame to the buffer
        outputBuffer.put(jpgAsText)
        
        displayFull.release()

        count += 1
    outputBuffer.put(inputBuffer.get())#thread knows when to end

def displayFrames(inputBuffer):
    # initialize frame count
    count = 0
    while True:
    #[2]
        displayFull.acquire()

        # get the next frame
        frameAsText = inputBuffer.get()

        displayEmpty.release()

        # decode the frame
        jpgRawImage = base64.b64decode(frameAsText)

        # convert the raw frame to a numpy array
        jpgImage = np.asarray(bytearray(jpgRawImage), dtype=np.uint8)

        # get a jpg encoded frame
        img = cv2.imdecode(jpgImage, cv2.IMREAD_UNCHANGED)

        # display the image in a window called "video" and wait 42ms
        # before displaying the next frame
        cv2.imshow("Video", img)
        if cv2.waitKey(42) and 0xFF == ord("q") or inputBuffer.peek() is 'e':
            break
        count += 1

    # cleanup the windows
    cv2.destroyAllWindows()


class Q:#[1]
    def __init__(self, initArray=[]):
        self.a = []
        self.a = [x for x in initArray]

    def put(self, item):
        self.a.append(item)

    def get(self):
        a = self.a
        item = a[0]
        del a[0]
        return item
    #required to check for end conditional
    def peek(self):
        item = None
        if len(self.a)>0:
            a = self.a
            item = a[0]
        return item


    def __repr__(self):
        return "Q(%s)" % self.a


# filename of clip to load
filename = 'clip.mp4'

# shared queue
extractionQueue = Q()
displayQueue = Q()

# extract the frames
extracting = threading.Thread(target=extractFrames, args=(filename, extractionQueue))

# convert the frames
converting = threading.Thread(target=convertFrames, args=(extractionQueue, displayQueue))

# display the frames
displaying = threading.Thread(target=displayFrames, args=(displayQueue,))

extracting.start()
converting.start()
displaying.start()