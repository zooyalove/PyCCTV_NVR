import sys
from PIL import Image
from pushbullet import Pushbullet
from gi.repository import GLib

def main():
    im = Image.open("taehui.jpg")
    g_im = im.convert('L')
    g_im.save('taehui_gray.jpg', 'JPEG')
    pb = Pushbullet('o.cJzinoZ3SdlW7JxYeDm7tbIrueQAW5aK')
    with open('taehui_gray.jpg', 'rb') as pic:
        file_data = pb.upload_file(pic, 'taehui_gray.jpg')
    print(**file_data)
    #pb.push_file(**file_data)
    #g_im.show()

if __name__ == "__main__":
    loop = GLib.MainLoop()
    main()
    loop.run()