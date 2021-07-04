import sys

import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.arrays import vbo

# GLSHADEMODEL IS GL_FLAT BECAUSE I LIKE IT MUCH MORE

# Schatten

# Keys from keyboard
key_red = glfw.KEY_R
key_blue = glfw.KEY_U
key_black = glfw.KEY_B
key_white = glfw.KEY_W
key_yellow = glfw.KEY_Y
key_orthogonal = glfw.KEY_O  # orthogonal projection
key_central = glfw.KEY_P  # central projection
key_control = 341  # CONTROL ON KEYBOARD
key_shadow = glfw.KEY_H

# CHANGES BETWEEN BACKGROUND COLOR MODE AND OBJECT COLOR MODE
controlMode = False

# colors for background
background_red = (1.0, 0.0, 0.0, 0.0)
background_black = (0.0, 0.0, 0.0, 0.0)
background_blue = (0.0, 0.0, 1.0, 0.0)
background_white = (1.0, 1.0, 1.0, 0.0)
background_yellow = (1.0, 1.0, 0.0, 0.0)

# colors for object
object_red = [1, 0, 0]
object_blue = [0, 0, 1]
object_black = [0.1, 0.1, 0.1]
object_white = [1, 1, 1]
object_yellow = [1, 1, 0]

myColor = object_yellow

# modes for clicking
PRESSED = 1
NotPRESSED = 0

# clicked mouse keys
pressed_left = False
pressed_middle = False
pressed_right = False

button_left = 0
button_right = 1
button_middle = 2

# a lot of stuff for rotation
startPoint = 0
endPoint = 0
axis = np.array([0, 0, 0], dtype=float)
angle = 0
orientation = np.identity(4)

# for scaling and translation
scalePoint = [0.5, 0.5]

translationStart = np.array([0, 0, 0], dtype=float)
translationEnd = np.array([0, 0, 0], dtype=float)
translation = [0, 0]

orthogonalMode = True  # if false -> central projection
shadowON = False
light = np.array([10000.0, 10000.0, 10000.0])


def rotate(angle, axis):
    c = np.cos(angle)
    mc = 1 - np.cos(angle)
    s = np.sin(angle)
    l = np.sqrt(np.dot(np.array(axis), np.array(axis)))

    if l == 0.0:  # l might be 0.0, no zero division
        return np.identity(4)
    x, y, z = np.array(axis) / l

    r = np.array([[x * x * mc + c, x * y * mc - z * s, x * z * mc + y * s, 0],
                  [x * y * mc + z * s, y * y * mc + c, y * z * mc - x * s, 0],
                  [x * z * mc - y * s, y * z * mc + x * s, z * z * mc + c, 0],
                  [0, 0, 0, 1]])
    return r.transpose()


class Scene:
    """ OpenGL 2D scene class """

    # initialization
    def __init__(self, width, height):
        # time
        self.t = 0
        self.showVector = True

        self.pointsize = 3
        self.width = width
        self.height = height

        self.fList = []
        self.vList = []
        self.vtList = []
        self.vnList = []
        self.vertex = []

        glPointSize(self.pointsize)
        glLineWidth(self.pointsize)

        # Enables a lot of features: light, color, shadows and more
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)  # Mode of polygon content
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glShadeModel(GL_FLAT)

        file = open(sys.argv[1])
        for line in file:
            if line.startswith("f "):
                # list of 3 lists of v, vt and vn
                # vt might be empty 
                # faces contains 3 points with values, INDEX!
                f = line.split()[1:]
                f = [c.split("/") for c in f]
                self.fList.append(f)

            if line.startswith("v "):
                # v is list of 3 float values in line
                # v -> triangle
                v = list(map(float, line.split()[1:]))
                self.vList.append(np.array(v))

            if line.startswith("vn "):
                # vn is list of 3 float values in line
                # vn contains 3 normal vectors of a point
                n = list(map(float, line.split()[1:]))
                self.vnList.append(n)

            if line.startswith("vt "):
                # texture coordinates 
                vt = list(map(float, line.split()[1:]))
                self.vtList.append(vt)

        if len(self.vnList) == 0:
            # no normal vectors in file :(
            self.normalV = [0] * len(self.vList)
            for f in self.fList:
                v1 = self.vList[int(f[2][0]) - 1] - self.vList[int(f[0][0]) - 1]
                v2 = self.vList[int(f[2][0]) - 1] - self.vList[int(f[1][0]) - 1]
                normal = np.cross(v1, v2)
                self.normalV[int(f[0][0]) - 1] = normal
                self.normalV[int(f[1][0]) - 1] = normal
                self.normalV[int(f[2][0]) - 1] = normal

        # for boundingBox max and min value of object
        boundingMin = list(map(min, list(zip(*self.vList))))
        boundingMax = list(map(max, list(zip(*self.vList))))
        self.boundingBox = [boundingMin, boundingMax]

        # (from min to max) / 2
        self.center = np.array(self.boundingBox[0]) + np.array(self.boundingBox[1])
        self.center /= 2

        # box length is 2
        self.scaleFactor = max(list(np.array(self.boundingBox[1]) - np.array(self.boundingBox[0])))
        self.scaleFactor = 2 / self.scaleFactor

        for f in self.fList:
            for v in f:
                if len(self.vnList) != 0:
                    self.vertex.append(self.vList[int(v[0]) - 1])
                    self.vertex.append(self.vnList[int(v[2]) - 1])
                else:
                    self.vertex.append(self.vList[int(v[0]) - 1])
                    self.vertex.append(self.normalV[int(v[0]) - 1])

        self.vbo = vbo.VBO(np.array(self.vertex, "f"))

    # render 
    def render(self):
        self.vbo.bind()

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)

        glVertexPointer(3, GL_FLOAT, 24, self.vbo)
        glNormalPointer(GL_FLOAT, 24, self.vbo + 12)

        glLoadIdentity()

        # dynamic translation while clicked, always changing parameter
        glTranslate(translationEnd[0] - translationStart[0], translationEnd[1] - translationStart[1], 0)
        # after clicked keeping current position
        glTranslate(translation[0], translation[1], 0)

        if not orthogonalMode:
            glTranslate(0, 0, -5)

        # for rotation around orientation axis
        glMultMatrixf(np.dot(orientation, rotate(angle, axis)))

        # setting up scaling and it's factor, my case between 0.1 and 2
        scaling = scalePoint[0] + scalePoint[1]
        if scaling <= 0:
            glScalef(0.1, 0.1, 0.11)
        elif scaling > 2:
            glScalef(2, 2, 2)
        else:
            glScale(scaling, scaling, scaling)

        # tranlsate to center and scale by scaleFactor
        glScalef(self.scaleFactor, self.scaleFactor, self.scaleFactor)
        glTranslate(-self.center[0], -self.center[1], -self.center[2])

        if shadowON == True:  # if object should have shadows                    
            p = np.array([[1.0, 0, 0, 0],
                          [0, 1.0, 0, 0],
                          [0, 0, 1.0, 0],
                          [0, -1.0 / light[1], 0, 0]]).transpose()

            glMatrixMode(GL_MODELVIEW)

            # save state
            glPushMatrix()

            # move boundingbox down with value y = min(y)
            glTranslate(0, self.boundingBox[0][1], 0)

            # tanslate light back to normal coordinates
            glTranslatef(light[0], light[1], light[2])

            # project object
            glMultMatrixf(p)

            # move light to origin
            glTranslatef(-light[0], -light[1], -light[2])

            # move boundingbox downside up to y = 0
            glTranslate(0, -self.boundingBox[0][1], 0)

            glColor(0.0, 0.0, 0.0)

            # diasable lighting because of artifacts
            glDisable(GL_LIGHTING)
            glDisable(GL_DEPTH_TEST)

            # draw shadow, render object again
            glDrawArrays(GL_TRIANGLES, 0, len(self.vertex))

            # enable on lightning again
            glEnable(GL_LIGHTING)
            glEnable(GL_DEPTH_TEST)

            # restore state
            glPopMatrix()

            # setting up the color
        glColor(myColor)
        glDrawArrays(GL_TRIANGLES, 0, len(self.vertex))

        self.vbo.unbind()

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)


class RenderWindow:
    """GLFW Rendering window class"""

    def __init__(self):

        # save current working directory
        cwd = os.getcwd()

        # Initialize the library
        if not glfw.init():
            return

        # restore cwd
        os.chdir(cwd)

        # buffer hints
        glfw.window_hint(glfw.DEPTH_BITS, 32)

        # define desired frame rate
        self.frame_rate = 60

        # make a window
        self.width, self.height = 640, 480
        self.aspect = self.width / float(self.height)
        self.window = glfw.create_window(self.width, self.height, "RenderWindow", None, None)
        if not self.window:
            glfw.terminate()
            return

        # Make the window's context current
        glfw.make_context_current(self.window)

        # initialize GL
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glClearColor(1.0, 1.0, 1.0, 1.0)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        # for optimal ratio between height and width
        if self.width <= self.height:
            glOrtho(-1.5, 1.5, -1.5 * self.height / self.width, 1.5 * self.height / self.width, -10, 10)
        else:
            glOrtho(-1.5 * self.width / self.height, 1.5 * self.width / self.height, -1.5, 1.5, -10, 10)
        glMatrixMode(GL_MODELVIEW)

        # set window callbacks
        glfw.set_mouse_button_callback(self.window, self.onMouseButton)
        glfw.set_key_callback(self.window, self.onKeyboard)
        glfw.set_window_size_callback(self.window, self.onSize)

        # create 3D
        self.scene = Scene(self.width, self.height)

        # exit flag
        self.exitNow = False
        self.r = min(self.width, self.height) / 2.0

    def projectOnSphere(self, x, y, r):
        x = x - self.width / 2.0
        y = self.height / 2.0 - y
        a = min(r * r, x ** 2 + y ** 2)
        z = np.sqrt(r * r - a)
        l = np.sqrt(x ** 2 + y ** 2 + z ** 2)
        return x / l, y / l, z / l

    def onMouseButton(self, win, button, action, mods):
        global pressed_left, pressed_middle, pressed_right
        global startPoint, scalePoint
        global axis, angle, orientation
        global translationEnd, translationStart, translation

        # if mouse keys were or weren't clicked

        if action == PRESSED:
            if button == button_left:
                pressed_left = True
                startPoint = glfw.get_cursor_pos(win)
                startPoint = self.projectOnSphere(startPoint[0], startPoint[1], self.r)
            if button == button_middle:
                pressed_middle = True
            if button == button_right:
                pressed_right = True
                translationStart = np.array(glfw.get_cursor_pos(self.window))
                translationStart[0] = translationStart[0] / (self.width / 2)
                translationStart[1] = 1 - (translationStart[1] / (self.height / 2))

        if action == NotPRESSED:
            if button == button_left:
                pressed_left = False
                orientation = np.dot(orientation, rotate(angle, axis))
                angle = 0  # beginning state
            if button == button_middle:
                pressed_middle = False
            if button == button_right:
                pressed_right = False
                translation += translationEnd - translationStart

                # if values not [0,0] again
                # = -> translation dynamic will be added to static translation after not clicked anymore 
                # double translation values
                translationEnd = [0, 0]
                translationStart = [0, 0]

    def onKeyboard(self, win, key, scancode, action, mods):
        global myColor
        global controlMode
        global orthogonalMode
        global shadowON

        # if keyboard keys were or weren't clicked

        if action == glfw.PRESS:
            if key == key_control:  # for mode selection, background or object
                if controlMode:
                    controlMode = False
                else:
                    controlMode = True
            if key == glfw.KEY_ESCAPE:  # ESC to quit
                self.exitNow = True

            # press specific key for specific color
            if key == key_black:
                if not controlMode:
                    myColor = object_black
                else:
                    glClearColor(*background_black)
            if key == key_blue:
                if not controlMode:
                    myColor = object_blue
                else:
                    glClearColor(*background_blue)
            if key == key_red:
                if not controlMode:
                    myColor = object_red
                else:
                    glClearColor(*background_red)
            if key == key_white:
                if not controlMode:
                    myColor = object_white
                else:
                    glClearColor(*background_white)
            if key == key_yellow:
                if not controlMode:
                    myColor = object_yellow
                else:
                    glClearColor(*background_yellow)

            # for projection-mode
            if key == key_orthogonal:
                orthogonalMode = True
                glMatrixMode(GL_MODELVIEW)
            if key == key_central:
                orthogonalMode = False

            if key == key_shadow:
                if not shadowON:
                    shadowON = True
                else:
                    shadowON = False

    def onSize(self, win, width, height):
        self.width = width
        self.height = height
        if self.height == 0:
            self.height = 1  # avoid zero division error
        self.aspect = self.width / float(self.height)
        glViewport(0, 0, self.width, self.height)

        self.r = min(self.width, self.height) / 2.0
        self.chooseMode()

    def chooseMode(self):
        # switches between orthogonal and central projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        if orthogonalMode:
            if self.width <= self.height:
                glOrtho(-1.5, 1.5, -1.5 * self.height / self.width, 1.5 * self.height / self.width, -10, 10)
            else:
                glOrtho(-1.5 * self.width / self.height, 1.5 * self.width / self.height, -1.5, 1.5, -10, 10)
        else:
            if self.width <= self.height:
                glFrustum(-1.5, 1.5, -1.5 * self.height / self.width, 1.5 * self.height / self.width, 3, 10)
            else:
                glFrustum(-1.5 * self.width / self.height, 1.5 * self.width / self.height, -1.5, 1.5, 3, 10)
        glMatrixMode(GL_MODELVIEW)

    def run(self):
        global endPoint, startPoint
        global angle, axis
        global scalePoint, translationEnd

        # initializer timer
        glfw.set_time(0.0)
        t = 0.0
        while not glfw.window_should_close(self.window) and not self.exitNow:
            # update every x seconds
            currT = glfw.get_time()
            if currT - t > 1.0 / self.frame_rate:
                # update time
                t = currT
                # clear
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

                if pressed_left:  # get current axis and angle because of endPoint
                    endPoint = glfw.get_cursor_pos(self.window)
                    endPoint = self.projectOnSphere(endPoint[0], endPoint[1], self.r)

                    axis = np.cross(startPoint, endPoint)
                    try:
                        angle = np.arccos(np.dot(startPoint, endPoint))
                    except RuntimeWarning:
                        pass

                if pressed_middle:  # get current scaling point
                    scalePoint = np.array(glfw.get_cursor_pos(self.window))
                    scalePoint[0] = scalePoint[0] / (self.width / 2)
                    scalePoint[1] = 1 - (scalePoint[1] / (self.height / 2))

                if pressed_right:  # get curren position
                    translationEnd = np.array(glfw.get_cursor_pos(self.window))
                    translationEnd[0] = translationEnd[0] / (self.width / 2)
                    translationEnd[1] = 1 - (translationEnd[1] / (self.height / 2))

                self.chooseMode()

                # render scene
                self.scene.render()

                glfw.swap_buffers(self.window)
                # Poll for and process events
                glfw.poll_events()
        # end
        glfw.terminate()


# main() function
def main():
    rw = RenderWindow()
    rw.run()


# call main
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Please name the file you want to view in RenderWindow!')
    else:
        main()
