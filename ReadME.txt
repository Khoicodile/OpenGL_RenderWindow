This is a program to view obj files in OpenGL written in python3. 

Needed libraries:
numpy - pip install numpy
glfw - pip install glfw
PyOpenGL - pip install PyOpenGL PyOpenGL_accelerate

How to run:
python3 RenderWindow.py filename.obj



Controls of the render window:
Keep left mouse button pressed and move: rotation of the object around its selected axis
Keep middle mouse button pressed and move: zoom in or out on the object
Keep right mouse button pressed and move: move the object

Press the h button: enable or disable calculated shadow
Press the ctr button: switch between the colour selection of the background or that of the object

Selectable colours and their buttons:
w: white
u: blue
b: black
r: red
y: yellow (on some keyboards the button is z instead of y)

Switching between orthogonal and central projection camera mode:
o: orthogonal projection
p: central projection
