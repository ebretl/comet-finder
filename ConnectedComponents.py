class ConnectedComponent:
    def __init__(self):
        self.coords = set()
    def addcoord(self, x, y):
        self.coords.add((x,y))
    def contains(self, x, y):
        return (x,y) in self.coords
    def size(self):
        return len(self.coords)
    def avg_position(self):
        avgx = float(sum([c[0] for c in self.coords])) / float(self.size())
        avgy = float(sum([c[1] for c in self.coords])) / float(self.size())
        return (avgx,avgy)

def find_connected_components(img, imsize):
    pxarr = img.load()
    blobs = []
    search_dirs = ((1,0), (0,1), (-1,0), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1))
    for x in range(imsize):
        for y in range(imsize):
            if pxarr[x,y]<1 or _get_owning_component(blobs,x,y) != None:
                continue
            currentcomp = ConnectedComponent()
            currentcomp.addcoord(x,y)
            blobs.append(currentcomp)
            posstack = [(x,y)]
            while len(posstack) > 0:
                tmpx, tmpy = posstack.pop()
                for dx,dy in search_dirs:
                    newx, newy = tmpx+dx, tmpy+dy
                    if _eligible_move(pxarr,imsize,newx,newy) and not (newx,newy) in posstack \
                            and _get_owning_component(blobs,newx,newy) == None:
                        posstack.append((newx,newy))
                        currentcomp.addcoord(newx,newy)
    return blobs

def _get_owning_component(blobs, x, y):
    for blob in blobs:
        if blob.contains(x,y): return blob
    return None

def _eligible_move(pxarr, imsize, x, y):
    return x>=0 and x<imsize and y>=0 and y<imsize and pxarr[x,y]>1