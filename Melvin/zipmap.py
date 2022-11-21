import utility

#Compression script used by a crontab every ten minutes to compress the global image map
try:
    utility.compress_file('/home/user/melvin/map/outs.png')
except:
    print("File not found")