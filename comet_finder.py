# -*- coding: utf-8 -*-
"""
Created on Sat May 28 22:32:35 2016

@author: Evan
"""
 
from PIL import Image, ImageFilter, ImageOps
from urllib import request
from matplotlib import pyplot as plt
from ConnectedComponents import find_connected_components
import time
from multiprocessing import Pool
from io import BytesIO

imsize = 512

class CometImageConverter:
    def __init__(self, background, mask, im_size):
        self.bkgd = background
        self.msk = mask
        self.size = im_size
    def output(self, original, debug=False):
        f = Image.composite(original.convert('L'), self.bkgd, self.msk)
        f = ImageOps.autocontrast(f)
        f = f.filter(ImageFilter.FIND_EDGES)
        f = f.point(lambda x: 0 if x<40 else 255)
        f = dilate(dilate(dilate(f)))
        f = erode(erode(erode(f)))
        if debug: f.show()
        return find_connected_components(f, self.size)

class CometTrajectory:
    vel_change_allowed = 0.1
    minpxdist = 5.0
    maxpxdist = 27.0 #comet ISON was ~11 pixels in 12 minutes or 22px in 24min
    def __init__(self, origin, originlevel):
        self.positions = [origin]
        self.level = self.origin_level = originlevel
        self.scaler_used = 0
        self.minscalar = 1.0 - self.vel_change_allowed
        self.maxscalar = 1.0 + self.vel_change_allowed
    def __repr__(self):
        out = "from "+str(self.origin_level)+": "
        for p in self.positions:
            out = out+str(p)+" "
        return out
    def minvel(self, lastvel):
        return self.minscalar * lastvel
    def maxvel(self, lastvel):
        return self.maxscalar * lastvel
    def copy(self):
        out = CometTrajectory((0,0), 0)
        out.positions = self.positions.copy()
        out.level = self.level
        out.origin_level = self.origin_level
        out.scaler_used = self.scaler_used
        return out
    def matching_trajectory(self, newpt):
        dx0, dy0 = self.velocity()
        self.positions.append(newpt)
        dx1, dy1 = self.velocity()
        self.positions.pop(-1)
        if self.minpxdist**2 < (dx1**2 + dy1**2) < self.maxpxdist**2:
            if dx0 == 0 and dy0 == 0:
                return True
            minx = self.minvel(abs(dx0))
            miny = self.minvel(abs(dy0))
            maxx = self.maxvel(abs(dx0))
            maxy = self.maxvel(abs(dy0))
            #print(minx,'<',abs(dx1),'<',maxx,'and',miny,'<',abs(dy1),'<',maxy)
            if minx < abs(dx1) < maxx and miny < abs(dy1) < maxy:
                return True
            if self.scaler_used != 2.0 and minx < dx1/2. < maxx and \
                        miny < dy1/2. < maxy:
                if self.scaler_used == 0:
                    self.scaler_used = 0.5
                return True
            if self.scaler_used != 0.5 and minx < dx1*2 < maxx and \
                        miny < dy1*2 < maxy:
                if self.scaler_used == 0:
                    self.scaler_used = 2.0
                return True
        return False
    def add(self, newpt):
        self.positions.append(newpt)
    def velocity(self):
        if self.length() < 2:
            return (0,0)
        return tuplediff(self.positions[-1], self.positions[-2])
    def positionmatch(self, newpos):
        return self.positions[-1] == newpos
    def length(self):
        return len(self.positions)


def tuplediff(a, b):
    return tuple(map(lambda x,y: x-y, a, b))
def matplot(image):
    plt.imshow(image)
    plt.show()    

    
def dilate(image, darktarget=False):
    imcopy = image.copy()
    pxarr = imcopy.load()
    target = 0 if darktarget else 255
    for x in range(imsize):
        for y in range(imsize):
            if(pxarr[x,y] == target):
                if x > 0 and pxarr[x-1,y] != target:     pxarr[x-1,y] = 1
                if y > 0 and pxarr[x,y-1] != target:     pxarr[x,y-1] = 1
                if x+1<imsize and pxarr[x+1,y]!=target:  pxarr[x+1,y] = 1
                if y+1<imsize and pxarr[x,y+1]!=target:  pxarr[x,y+1] = 1
    for x in range(imsize):
        for y in range(imsize):
            if pxarr[x,y]==1: pxarr[x,y] = target
    return imcopy

def erode(image):
    return dilate(image, darktarget=True)
    
def draw_trajectory(trajectory, background):
    background = background.copy().convert('RGB')
    pxarr = background.load()
    for x,y in trajectory.positions:
        print(x,y)
        pxarr[x,y] = (0,255,0)
    matplot(background)
    

if __name__ == '__main__':
    timestart = time.clock()    
    
#    url = 'http://sohowww.nascom.nasa.gov/data/LATEST/current_c2.gif'
#    print("waiting for response")
#    response = request.urlopen(url)
#    print("response received, processing")
#    file = BytesIO(response.read())
    file = 'C:/Users/Evan/Desktop/current_c2.gif'
    gif = Image.open(file)
    
    frames = []
    try:
        while True:
            newim = Image.new('RGBA', (imsize,imsize))
            newim.paste(gif)
            frames.append(newim)
            gif.seek(gif.tell()+1)
    except EOFError:
        print("read", len(frames), "frames")
    
    mask = Image.open('C:/Users/Evan/Desktop/mask.gif').convert('L')
    background = Image.open('C:/Users/Evan/Desktop/background.png').convert('L')
    
    print("converting frames to black/white and finding connected components")
    converter = CometImageConverter(background, mask, imsize)
    pool = Pool(processes=4)
    allblobs = pool.map(converter.output, frames[1:31])
    #allblobs = map(converter.output, frames[:10])
    pool.close()
    pool.join()
    pool.terminate()
    
    print("extracting all potential object trajectories...")
    allpoints = [[b.avg_position() for b in imgblobs] for imgblobs in allblobs]
    #allhistorylinks = []
    consecutive_frames_req = 13 #ISON was ~20
    trajectories = []
    #traj_dbg = []
    completed = set()
    for imgnum, imgpointslist in enumerate(allpoints):
        print("analyzing image", imgnum)
        if imgnum == 0:
            for pt in imgpointslist:
                trajectories.append( CometTrajectory(pt, 0) )
        else:
            trajectories_old = trajectories[:]
            trajectories = []
            for pt in imgpointslist:
                any_matches = False
                for traj in trajectories_old:
                    if traj.level==imgnum-1 and traj.matching_trajectory(pt):
                        any_matches = True
                        newtraj = traj.copy()
                        newtraj.add(pt)
                        newtraj.level += 1
                        trajectories.append(newtraj)
                    elif traj.length() >= consecutive_frames_req:
                        completed.add(str(traj))
                        #print("found", traj.length(), traj.origin_level, \
                        #        traj.level)
                if not any_matches:
                    trajectories.append( CometTrajectory(pt, imgnum) )
        #traj_tmp = [str(t) for t in trajectories]
        #traj_dbg.append(traj_tmp)
        print("found", len(completed))
    completed_dbg = sorted(completed)
    
    for c in completed_dbg:
        print(c)
    
    timediff = time.clock() - timestart
    print("done in", timediff, "seconds")
    
    
