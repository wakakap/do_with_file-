import qrcode
import os
from PIL import Image
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.moduledrawers import SquareModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask
# import qrcode
# img = qrcode.make('祝生日快乐，每次L(_ ･o･)  ( ･ｰ･)_／彡○，至少⊂=(－＿－)=⊃ safe，经常ヾ(;ﾟ◇ﾟ)ゞhome  ~ °')
# type(img)  # qrcode.image.pil.PilImage
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)

qr.add_data('祝生日快乐\n每次L(_ ･o･)  ( ･ｰ･)_／彡○\n至少⊂=(－＿－)=⊃ safe\n经常ヾ(;ﾟ◇ﾟ)ゞhome  ~ °')
qr.make(fit=True)

#img = qr.make_image(fill_color="black", back_color="white")
# img= qr.make_image(image_factory=StyledPilImage, module_drawer=SquareModuleDrawer())
img= qr.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())
#img = qr.make_image(image_factory=StyledPilImage, embeded_image_path='testasdf.png')



#添加logo
logo = 'lww.jpg'
if logo and os.path.exists(logo):
    icon=Image.open(logo)
    #获取二维码图片的大小
    img_w,img_h=img.size
    factor=6
    size_w=int(img_w/factor)
    size_h=int(img_h/factor)
    #logo图片的大小不能超过二维码图片的1/4
    icon_w,icon_h=icon.size
    if icon_w>size_w:
        icon_w=size_w
    if icon_h>size_h:
        icon_h=size_h
    icon=icon.resize((icon_w,icon_h),Image.ANTIALIAS)
    #详见：http://pillow.readthedocs.org/handbook/tutorial.html
    #计算logo在二维码图中的位置
    w=int((img_w-icon_w)/2)
    h=int((img_h-icon_h)/2)
    icon=icon.convert("RGBA")
    img.paste(icon,(w,h),icon)


img.save("some_file.png")