from base import *
from folder import *
from fspot import *
from flickr import *
#from picasa import *
#from tumblr import *

token_base = (
    ['Folder', MakeDirPhoto,    PhotoTargetDir    ],
    ['F-Spot', MakeFSpotPhoto,  PhotoTargetFspot  ],
    ['Flickr', MakeFlickrPhoto, PhotoTargetFlickr ],
#    ['Picasa Web', MakePicasaPhoto, PhotoTargetPicasa ],
#    ['Tumblr', MakeTumblrPhoto, PhotoTargetTumblr ],
    )

SOURCE_LIST=[]
MAKE_PHOTO_TOKEN ={}
PHOTO_TARGET_TOKEN={}

for k in token_base:
    SOURCE_LIST.append(k[0])
    MAKE_PHOTO_TOKEN[k[0]] = k[1]
    PHOTO_TARGET_TOKEN[k[0]] = k[2]
