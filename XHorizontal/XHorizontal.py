#FusionAPI_python Addin
#Author-kantoku
#Description-When you start working on the sketch, rotate it so that the X axis is horizontal.

import adsk.core
import adsk.fusion
import traceback
import threading
import json

_onSktEventContainer = None
_DEBUG = False

class OnSketchEvent():
    _app = None
    _handlers = []
    _customEventId = 'OnSketchEventId'
    _customEvent = None
    _stopFlag = None

    def __init__(self):
        self._app = adsk.core.Application.get()
        self._customEvent = self._app.registerCustomEvent(self._customEventId)
        onSktCheckEvent = self._onSketchCheckHandler()
        self._customEvent.add(onSktCheckEvent)
        self._handlers.append(onSktCheckEvent)

        self._stopFlag = threading.Event()
        onSktCheckThread = self._onSketchCheckThread(
            self._stopFlag, self._customEventId, 0.1)
        onSktCheckThread.start()

    def __del__(self):
        if self._handlers.count:
            self._customEvent.remove(self._handlers[0])
        self._stopFlag.set() 
        self._app.unregisterCustomEvent(self._customEventId)

    class _onSketchCheckHandler(adsk.core.CustomEventHandler):
        _previousState = False
        _previousCamera = None

        def __init__(self):
            super().__init__()
            self._previousCamera = self._getCamera()

        def __del__(self):
            pass

        def notify(self, args):
            app = adsk.core.Application.get()
            des :adsk.fusion.Design = app.activeProduct

            try:
                if adsk.fusion.Sketch.cast(des.activeEditObject):
                    # if _DEBUG:
                    #     dumpMsg('On Sketch')
                    if not self._previousState:
                        # in Sketch
                        if _DEBUG:
                            dumpMsg('in Sketch')

                        # 3d sketch
                        if not self._isEqualCamera(self._previousCamera, self._getCamera()):
                            self._rotation_V_Up()

                    self._previousState = True

                else:
                    # if _DEBUG:
                    #     dumpMsg('Off Sketch')

                    if self._previousState:
                        # exit Sketch
                        if _DEBUG:
                            dumpMsg('exit Sketch')

                        self._setCamera(self._previousCamera, True)

                    self._previousState = False
                    self._previousCamera = self._getCamera()

            except:
                dumpMsg('Failed:\n{}'.format(traceback.format_exc()))
        
        # Vを上方向にする
        # 但しXZ平面はGUIに合わせて反転する
        def _rotation_V_Up(self):
            app = adsk.core.Application.get()
            des :adsk.fusion.Design = app.activeProduct

            skt = adsk.fusion.Sketch.cast(des.activeEditObject)
            if not skt: return

            cam :adsk.core.Camera = self._getCamera()
            if self._getCompInvertZVec(skt).isEqualTo(skt.yDirection):
                vec = skt.yDirection.copy()
                vec.scaleBy(-1)
                cam.upVector = vec
            else:
                cam.upVector = skt.yDirection
                
            self._setCamera(cam)

        def _getCompInvertZVec(self, skt :adsk.fusion.Sketch) -> adsk.core.Vector3D:
            try:
                # occ
                occ :adsk.fusion.Occurrence = skt.assemblyContext
                _,_,_, zVec = occ.transform.getAsCoordinateSystem()
                zVec.scaleBy(-1)
                return zVec
            except:
                # root
                return adsk.core.Vector3D.create(0,0,-1)

        # カメラの一致? - イベント利用すべき？
        def _isEqualCamera(self, cam1 :adsk.core.Camera, cam2 :adsk.core.Camera) -> bool:
            if _DEBUG:
                dumpMsg(f'cam1:{cam1.upVector.asArray()}')
                dumpMsg(f'cam2:{cam2.upVector.asArray()}')

            if not cam1.upVector.isEqualTo(cam2.upVector):
                return False

            return True

        # カメラの取得
        def _getCamera(self) -> adsk.core.Camera:
            app = adsk.core.Application.get()

            if not app.isStartupComplete:
                return adsk.core.Camera.cast(None)

            vp :adsk.core.Viewport = app.activeViewport
            cam :adsk.core.Camera = vp.camera
            return cam

        # カメラの設定
        def _setCamera(self, cam :adsk.core.Camera, smooth = False):
            cam.isSmoothTransition = smooth
            app = adsk.core.Application.get()
            app.activeViewport.camera = cam

    class _onSketchCheckThread(threading.Thread):
        _checkTime :float = 0.1
        _customEventId = ''

        def __init__(self, event, customEventId, checkTime):
            threading.Thread.__init__(self)
            self.stopped = event
            self._checkTime = checkTime
            self._customEventId = customEventId

        def run(self):
            while not self.stopped.wait(self._checkTime):
                app = adsk.core.Application.get()
                app.fireCustomEvent(self._customEventId, json.dumps({})) 


def run(context):
    try:
        global _onSktEventContainer
        _onSktEventContainer = OnSketchEvent()
        dumpMsg('start addins - Skectch_X_Horizontal')

    except:
        dumpMsg('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        dumpMsg('stop addins - Skectch_X_Horizontal')
        global _onSktEventContainer
        del _onSktEventContainer

    except:
        dumpMsg('Failed:\n{}'.format(traceback.format_exc()))

def dumpMsg(msg :str):
    adsk.core.Application.get().userInterface.palettes.itemById('TextCommands').writeText(str(msg))