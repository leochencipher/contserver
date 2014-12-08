import matplotlib

matplotlib.use('Agg')

from matplotlib import pyplot as PLT
import numpy as NP
import StringIO
import PIL


# next 5 lines just create a matplotlib plot
t = NP.arange(-1., 1., 100)
s = NP.sin(NP.pi*t)   
PLT.plot(t, s, 'b.')

buffer = StringIO.StringIO()
canvas = PLT.get_current_fig_manager().canvas
canvas.draw()

pil_image = PIL.Image.fromstring('RGB', canvas.get_width_height(), 
             canvas.tostring_rgb())
pil_image.save(buffer, 'SVG')
PLT.close()
# Django's HttpResponse reads the buffer and extracts the image
print buffer.getvalue()