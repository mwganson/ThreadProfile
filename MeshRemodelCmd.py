# -*- coding: utf-8 -*-
###################################################################################
#
#  MeshRemodelCmd.py
#  
#  Copyright 2019 Mark Ganson <TheMarkster> mwganson at gmail
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
###################################################################################

__title__   = "MeshRemodel"
__author__  = "Mark Ganson <TheMarkster>"
__url__     = "https://github.com/mwganson/MeshRemodel"
__date__    = "2019.08.16"
__version__ = "1.00"
version = 1.00

import FreeCAD, FreeCADGui, Part, os, math
from PySide import QtCore, QtGui
import Draft, DraftGeomUtils, DraftVecUtils


if FreeCAD.GuiUp:
    from FreeCAD import Gui

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'Resources', 'icons' )
keepToolbar = False



#######################################################################################
# Keep Toolbar active even after leaving workbench

class MeshRemodelSettingsCommandClass(object):
    """Settings, currently only whether to keep toolbar after leaving workbench"""

    def __init__(self):
        pass       

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'Settings.png') , # the name of an icon file available in the resources
            'MenuText': "&Settings" ,
            'ToolTip' : "Workbench settings dialog"}
 
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        from PySide import QtGui
        window = QtGui.QApplication.activeWindow()
        pg = FreeCAD.ParamGet("User parameter:Plugins/MeshRemodel")
        keep = pg.GetBool('KeepToolbar',False)
        items=["Keep the toolbar active","Do not keep the toolbar active","Cancel"]
        item,ok = QtGui.QInputDialog.getItem(window,'MeshRemodel','Settings\n\nSelect the settings option\n',items,0,False)
        if ok and item == items[-1]:
            return
        elif ok and item == items[0]:
            keep = True
            pg.SetBool('KeepToolbar', keep)
        elif ok and item==items[1]:
            keep = False
            pg.SetBool('KeepToolbar', keep)
        return
   
    def IsActive(self):
        return True

#end settings class


####################################################################################
# Create the Mesh Remodel Points Object

class MeshRemodelCreatePointsObjectCommandClass(object):
    """Create Points Object command"""

    def __init__(self):
        self.mesh = None

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreatePointsObject.png') ,
            'MenuText': "&Create points object" ,
            'ToolTip' : "Create the points object"}
 
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        doc.openTransaction("Create points object")

        pts=[]
        meshpts = self.mesh.Mesh.Points
        for m in meshpts:
            pts.append(Part.Point(m.Vector).toShape())
        Part.show(Part.makeCompound(pts),"MR_Points")
        doc.recompute()

        doc.commitTransaction()
        QtGui.QApplication.restoreOverrideCursor()
        return
   
    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        sel = Gui.Selection.getSelectionEx()
        if len(sel) == 0:
            return False
        elif "Mesh.Feature" not in str(type(sel[0].Object)):
            return False
        else:
            self.mesh = sel[0].Object
        return True

# end create points class

####################################################################################
# Create a line from 2 selected points

class MeshRemodelCreateLineCommandClass(object):
    """Create Line from 2 selected points"""

    def __init__(self):
        self.pts = []

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreateLine.png') ,
            'MenuText': "&Create line" ,
            'ToolTip' : "Create a line from 2 selected points\n(Ctrl+Click to add midpoint)\n(Ctrl+Shift+Click for only midpoint)"}
 
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        modifiers = QtGui.QApplication.keyboardModifiers()
        #ctrl + click to include midpoint
        #ctrl + shift + click to include only the midpoint
        #QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        doc.openTransaction("Create line")

        line = Part.makeLine(self.pts[0],self.pts[1])
        lineName = "MR_Ref"
        if not modifiers == QtCore.Qt.ControlModifier.__or__(QtCore.Qt.ShiftModifier):
            Part.show(line,"MR_Line")
            lineName = doc.ActiveObject.Name
        if modifiers == QtCore.Qt.ControlModifier or modifiers == QtCore.Qt.ControlModifier.__or__(QtCore.Qt.ShiftModifier):
            Part.show(Part.Point(self.midpoint(self.pts[0],self.pts[1])).toShape(),lineName+"_Mid")
        doc.recompute()
        doc.commitTransaction()
        #QtGui.QApplication.restoreOverrideCursor()
        return
   
    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        sel = Gui.Selection.getSelectionEx()
        if len(sel) == 0:
            return False
        if not hasattr(sel[0],"PickedPoints"):
            return False
        count = 0
        self.pts = []
        for s in sel:
            if hasattr(s,"PickedPoints"):
                p = s.PickedPoints
                for pt in s.PickedPoints:
                    self.pts.append(pt)
                    count += 1
        if count == 2:
            return True
        return False

    def midpoint(self, A, B):       
        mid = FreeCAD.Base.Vector()
        mid.x = (A.x + B.x)/2.0
        mid.y = (A.y + B.y)/2.0
        mid.z = (A.z + B.z)/2.0
        return mid
# end create line class

####################################################################################
# Create a Polygon from 3 or more selected points

class MeshRemodelCreatePolygonCommandClass(object):
    """Create Polygon from 3 or more selected points"""

    def __init__(self):
        self.pts = []

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreatePolygon.png') ,
            'MenuText': "&Create Polygon" ,
            'ToolTip' : "Create a Polygon from 3 or more selected points\n(Shift+Click to not close polygon)"}
 
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        #QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        doc.openTransaction("Create polygon")
        modifiers = QtGui.QApplication.keyboardModifiers()
        if not modifiers == QtCore.Qt.ShiftModifier:
            self.pts.append(self.pts[0]) #don't close polygon on shift+click
        poly = Part.makePolygon(self.pts)
        Part.show(poly, "MR_Polygon")

        doc.recompute()
        doc.commitTransaction()
        #QtGui.QApplication.restoreOverrideCursor()
        return
   
    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        sel = Gui.Selection.getSelectionEx()
        if len(sel) == 0:
            return False
        if not hasattr(sel[0],"PickedPoints"):
            return False
        count = 0
        self.pts = []
        for s in sel:
            if hasattr(s,"PickedPoints"):
                p = s.PickedPoints
                for pt in s.PickedPoints:
                    self.pts.append(pt)
                    count += 1
        if count >= 3:
            return True
        return False

# end create Polygon class


# Create a Circle from 3 selected points

class MeshRemodelCreateCircleCommandClass(object):
    """Create Circle from 3 selected points"""

    def __init__(self):
        self.pts = []

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreateCircle.png') ,
            'MenuText': "&Create circle" ,
            'ToolTip' : "Create a circle from 3 selected points\n(Ctrl+Click to include Center point)\n(Ctrl+Shift+Click for only center)"}
 
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        #QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)


        #add_varargs_method("makeCircle",&Module::makeCircle,
        #    "makeCircle(radius,[pnt,dir,angle1,angle2]) -- Make a circle with a given radius\n"
        #    "By default pnt=Vector(0,0,0), dir=Vector(0,0,1), angle1=0 and angle2=360"
        #);

#python code below was adapted from this javascript code
#from here: https://gamedev.stackexchange.com/questions/60630/how-do-i-find-the-circumcenter-of-a-triangle-in-3d
#in a question answered by user greenthings

#function circumcenter(A,B,C) {
#    var z = crossprod(subv(C,B),subv(A,B));
#    var a=vlen(subv(A,B)),b=vlen(subv(B,C)),c=vlen(subv(C,A));
#    var r = ((b*b + c*c - a*a)/(2*b*c)) * outeradius(a,b,c);
#    return addv(midpoint(A,B),multv(normaliz(crossprod(subv(A,B),z)),r));
#}

#function outeradius(a,b,c) { /// 3 lens
#    return (a*b*c) / (4*sss_area(a,b,c));
#}

#function sss_area(a,b,c) {
#    var sp = (a+b+c)*0.5;
#    return Math.sqrt(sp*(sp-a)*(sp-b)*(sp-c));
#    //semi perimeter
#}
        modifiers = QtGui.QApplication.keyboardModifiers()
        poly = Part.makePolygon(self.pts)
        #Part.show(poly)
        normal = DraftGeomUtils.getNormal(poly)
       
        A = self.pts[0]
        B = self.pts[1]
        C = self.pts[2]

        if DraftVecUtils.isColinear([A,B,C]):
            FreeCAD.Console.PrintError("MeshRemodel Error: Cannot make arc/circle from 3 colinear points\n")
            return

        #Ax,Ay,Az = A[0],A[1],A[2] #this would find the incenter (I), not needed here
        #Bx,By,Bz = B[0],B[1],B[2]
        #Cx,Cy,Cz = C[0],C[1],C[2]
 
        #a = self.dist(B,C)
        #b = self.dist(C,A)
        #c = self.dist(A,B)
        #s = a+b+c
        
        #Ix = (a*Ax+b*Bx+c*Cx)/s
        #Iy = (a*Ay+b*By+c*Cy)/s
        #Iz = (a*Az+b*Bz+c*Cz)/s
        #I = FreeCAD.Base.Vector(Ix,Iy,Iz)

        I = self.circumcenter(A,B,C)
        radius = self.dist(I,A)

        doc.openTransaction("Create circle")
        circle = Part.makeCircle(radius, I, normal)
        circName="MR_Ref"
        if not modifiers == QtCore.Qt.ShiftModifier.__or__(QtCore.Qt.ControlModifier):
            Part.show(circle,"MR_Circle")
            circName = doc.ActiveObject.Name
        if modifiers == QtCore.Qt.ControlModifier or modifiers==QtCore.Qt.ControlModifier.__or__(QtCore.Qt.ShiftModifier):
            Part.show(Part.Point(I).toShape(),circName+"_Ctr") #show the center point on ctrl click or shift+ctrl click

        doc.recompute()
        doc.commitTransaction()
        #QtGui.QApplication.restoreOverrideCursor()
        return

    def circumcenter(self,A,B,C):
        z = C.sub(B).cross(A.sub(B))
        a = A.sub(B).Length
        b = B.sub(C).Length
        c = C.sub(A).Length
        r = ((b*b + c*c - a*a)/(2*b*c)) * self.outerradius(a,b,c)
        return  A.sub(B).cross(z).normalize().multiply(r).add(self.midpoint(A,B))

    def midpoint(self, A, B):       
        mid = FreeCAD.Base.Vector()
        mid.x = (A.x + B.x)/2.0
        mid.y = (A.y + B.y)/2.0
        mid.z = (A.z + B.z)/2.0
        return mid

    def outerradius(self, a, b, c):
        return (a*b*c) / (4*self.sss_area(a,b,c))

    def sss_area(self,a,b,c): #semiperimeter
        sp = (a+b+c)*0.5;
        return math.sqrt(sp*(sp-a)*(sp-b)*(sp-c))

    def dist(self, p1, p2):
        return self.getDistance3d(p1[0],p1[1],p1[2],p2[0],p2[1],p2[2])

    def getDistance3d(self, x1, y1, z1, x2, y2, z2):
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        sel = Gui.Selection.getSelectionEx()
        if len(sel) == 0:
            return False
        if not hasattr(sel[0],"PickedPoints"):
            return False
        count = 0
        self.pts = []
        for s in sel:
            if hasattr(s,"PickedPoints"):
                p = s.PickedPoints
                for pt in s.PickedPoints:
                    self.pts.append(pt)
                    count += 1
        if count >= 3:
            return True
        return False

# end create circle class

####################################################################################
# Create an Arc from 3 selected points
class MeshRemodelCreateArcCommandClass(object):

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreateArc.png') ,
            'MenuText': "&Create arc" ,
            'ToolTip' : "Create an arc from 3 selected points\n(Ctrl+Click to include Center point)\n(Ctrl+Shift+Click for only center)"}

    def __init__(self):
        self.pts = []

    def Activated(self):
        doc = FreeCAD.ActiveDocument

        modifiers = QtGui.QApplication.keyboardModifiers()
        poly = Part.makePolygon(self.pts)
#        Part.show(poly)
        normal = DraftGeomUtils.getNormal(poly)
       
        A = self.pts[0]
        B = self.pts[1]
        C = self.pts[2]

        if DraftVecUtils.isColinear([A,B,C]):
            FreeCAD.Console.PrintError("MeshRemodel Error: Cannot make arc/circle from 3 colinear points\n")
            return
        I = self.circumcenter(A,B,C)
        radius = self.dist(I,A)

        doc.openTransaction("Create Arc")
        arc = Part.ArcOfCircle(A,B,C)
        #on ctrl+shift click we only show center
        arcName="MR_Ref"
        if not modifiers == QtCore.Qt.ControlModifier.__or__(QtCore.Qt.ShiftModifier):
            Part.show(arc.toShape(),"MR_Arc")
            arcName = doc.ActiveObject.Name
        if modifiers == QtCore.Qt.ControlModifier or modifiers == QtCore.Qt.ControlModifier.__or__(QtCore.Qt.ShiftModifier):
            Part.show(Part.Point(I).toShape(),arcName+"_Ctr") #show the center point
        doc.recompute()
        doc.commitTransaction()
        #QtGui.QApplication.restoreOverrideCursor()
        return

    def circumcenter(self,A,B,C):
        z = C.sub(B).cross(A.sub(B))
        a = A.sub(B).Length
        b = B.sub(C).Length
        c = C.sub(A).Length
        r = ((b*b + c*c - a*a)/(2*b*c)) * self.outerradius(a,b,c)
        return  A.sub(B).cross(z).normalize().multiply(r).add(self.midpoint(A,B))

    def midpoint(self, A, B):       
        mid = FreeCAD.Base.Vector()
        mid.x = (A.x + B.x)/2.0
        mid.y = (A.y + B.y)/2.0
        mid.z = (A.z + B.z)/2.0
        return mid

    def outerradius(self, a, b, c):
        return (a*b*c) / (4*self.sss_area(a,b,c))

    def sss_area(self,a,b,c): #semiperimeter
        sp = (a+b+c)*0.5;
        return math.sqrt(sp*(sp-a)*(sp-b)*(sp-c))

    def dist(self, p1, p2):
        return self.getDistance3d(p1[0],p1[1],p1[2],p2[0],p2[1],p2[2])

    def getDistance3d(self, x1, y1, z1, x2, y2, z2):
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        sel = Gui.Selection.getSelectionEx()
        if len(sel) == 0:
            return False
        if not hasattr(sel[0],"PickedPoints"):
            return False
        count = 0
        self.pts = []
        for s in sel:
            if hasattr(s,"PickedPoints"):
                p = s.PickedPoints
                for pt in s.PickedPoints:
                    self.pts.append(pt)
                    count += 1
        if count >= 3:
            return True
        return False

# end create arc class

####################################################################################

# Make a sketch from selected objects
class MeshRemodelCreateSketchCommandClass(object):
    """Create sketch from selected objects"""

    def __init__(self):
        self.objs = []

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreateSketch.png') ,
            'MenuText': "&Create sketch" ,
            'ToolTip' : "Create a sketch from selected objects"}
 
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        doc.openTransaction("Create sketch")
        sketch = Draft.makeSketch(self.objs,autoconstraints=True)
        doc.recompute()
        for o in self.objs:
            if hasattr(o,"ViewObject"):
                o.ViewObject.Visibility=False
        doc.commitTransaction()
        #QtGui.QApplication.restoreOverrideCursor()
        return
   
    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        sel = Gui.Selection.getSelectionEx()
        if len(sel) == 0:
            return False
        count = 0
        self.objs = []
        for s in sel:
            if hasattr(s,"Object"):
                self.objs.append(s.Object)
                count += 1
        if count >= 1:
            return True
        return False

# end create sketch class
####################################################################################

# Make a wire from selected objects
class MeshRemodelCreateWireCommandClass(object):
    """Create wire from selected objects"""

    def __init__(self):
        self.objs = []

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreateWire.png') ,
            'MenuText': "&Create wire" ,
            'ToolTip' : "Create a wire from selected objects\n(All selected objects should be connected.)\n(Runs draft upgrade)"}
 
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        doc.openTransaction("Create wire")

        Draft.upgrade(self.objs)
        
        doc.recompute()
        for o in self.objs:
            if hasattr(o,"ViewObject"):
                o.ViewObject.Visibility=False
        doc.commitTransaction()
        #QtGui.QApplication.restoreOverrideCursor()
        return
   
    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        sel = Gui.Selection.getSelectionEx()
        if len(sel) == 0:
            return False
        count = 0
        self.objs = []
        for s in sel:
            if hasattr(s,"Object"):
                self.objs.append(s.Object)
                count += 1
        if count >= 1:
            return True
        return False

# end create wire class

####################################################################################

# Merge selected sketches
class MeshRemodelMergeSketchesCommandClass(object):
    """Merge selected sketches"""

    def __init__(self):
        self.objs = []

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'MergeSketches.png') ,
            'MenuText': "&Merge sketches" ,
            'ToolTip' : "Merge selected sketches with sketcher merge sketches tool"}
 
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        #doc.openTransaction("Merge sketches")  #not needed since the command does this
        Gui.runCommand("Sketcher_MergeSketches")
        doc.recompute()
        for o in self.objs:
            if hasattr(o,"ViewObject"):
                o.ViewObject.Visibility=False
        #doc.commitTransaction()
        #QtGui.QApplication.restoreOverrideCursor()
        return
   
    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        sel = Gui.Selection.getSelectionEx()
        if len(sel) == 0:
            return False
        count = 0
        self.objs = []
        for s in sel:
            if hasattr(s,"Object"):
                if "Sketch" in s.Object.Name:
                    self.objs.append(s.Object)
                    count += 1
        if count >= 2:
            return True
        return False

# end merge sketches

##################################################################################################
# initialize

def initialize():
    if FreeCAD.GuiUp:
        Gui.addCommand("MeshRemodelCreatePointsObject", MeshRemodelCreatePointsObjectCommandClass())
        Gui.addCommand("MeshRemodelCreateLine", MeshRemodelCreateLineCommandClass())
        Gui.addCommand("MeshRemodelCreatePolygon", MeshRemodelCreatePolygonCommandClass())
        Gui.addCommand("MeshRemodelCreateCircle", MeshRemodelCreateCircleCommandClass())
        Gui.addCommand("MeshRemodelCreateArc", MeshRemodelCreateArcCommandClass())
        Gui.addCommand("MeshRemodelCreateWire", MeshRemodelCreateWireCommandClass())
        Gui.addCommand("MeshRemodelCreateSketch", MeshRemodelCreateSketchCommandClass())
        Gui.addCommand("MeshRemodelMergeSketches", MeshRemodelMergeSketchesCommandClass())
        Gui.addCommand("MeshRemodelSettings", MeshRemodelSettingsCommandClass())


initialize()