import sys
from PIL import Image
fs=sys.argv[2:]; out=sys.argv[1]
ims=[Image.open(f).resize((960,540)) for f in fs]
rows=(len(ims)+1)//2
sheet=Image.new('RGB',(1920,540*rows),'white')
for i,im in enumerate(ims): sheet.paste(im,((i%2)*960,(i//2)*540))
sheet.save(out)
