# -*- coding: utf-8 -*-
###################################################################################
#
#  ThreadProfileCmd.py
#
#  Copyright 2019 Mark Ganson <TheMarkster> mwganson at gmail
#
#  Based on some code from Draft.py, authored by "Yorik van Havre, Werner Mayer,
#  Martin Burbaum, Ken Cline, Dmitry Chigrin, Daniel Falck"
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

__title__   = "ThreadProfile"
__author__  = "Mark Ganson <TheMarkster>"
__url__     = "https://github.com/mwganson/ThreadProfile"
__date__    = "2025.05.04"
__version__ = "1.96"
version = 1.96

import FreeCAD, FreeCADGui, Part, os, math, re
from PySide import QtCore, QtGui
import math
import traceback
import Draft
from FreeCAD import Base
import Draft_rc
from PySide.QtCore import QT_TRANSLATE_NOOP
from Draft import _DraftObject, _ViewProviderWire, formatObject, select

if FreeCAD.GuiUp:
    from FreeCAD import Gui

def tr(context, text):
    try:
        _encoding = QtGui.QApplication.UnicodeUTF8
        return QtGui.QApplication.translate(context, text, None, _encoding)
    except AttributeError:
        return QtGui.QApplication.translate(context, text, None)

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'Resources', 'icons' )
keepToolbar = False

class _ThreadProfile(_DraftObject):
    "The ThreadProfile object"

    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"ThreadProfile")
        obj.addProperty("App::PropertyFloat", "Version", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property","The version of ThreadProfile Workbench used to create this object")).Version = version
        obj.addProperty("App::PropertyFloat", "ThreadCount", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property","Height of thread in terms of number of threads, applied to Helix if created with workbench.\n Now readonly, adjust Height property instead.")).ThreadCount=10
        obj.addProperty("App::PropertyFloat","Height", "ThreadProfile","Height of swept thread, adjusts ThreadCount property").Height = 10
        obj.addProperty("App::PropertyVectorList","Points","ThreadProfile", QT_TRANSLATE_NOOP("App::Property","The points of the B-spline"))
        obj.addProperty("App::PropertyBool","Closed","ThreadProfile",QT_TRANSLATE_NOOP("App::Property","If the B-spline is closed or not"))
        obj.addProperty("App::PropertyBool","MakeFace","ThreadProfile",QT_TRANSLATE_NOOP("App::Property","Create a face if this spline is closed"))
        obj.addProperty("App::PropertyArea","Area","ThreadProfile",QT_TRANSLATE_NOOP("App::Property","The area of this object"))
        obj.addProperty("App::PropertyLength", "MinorDiameter", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "The minor diameter of the thread"))
        obj.addProperty("App::PropertyLength", "MinorDiameterFinal", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "The minor diameter of the thread with tolerance"))
        obj.addProperty("App::PropertyLength", "MajorDiameter", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "The major diameter of the thread"))
        obj.addProperty("App::PropertyLength", "MajorDiameterFinal", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "The major diameter of the thread with tolerance"))
        obj.addProperty("App::PropertyFloat", "d_delta", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", ""))
        obj.addProperty("App::PropertyFloat", "Tolerance", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "The tolerance of the thread. It will be added to diameters"))
        obj.addProperty("App::PropertyFloatList","internal_data","ThreadProfile",QT_TRANSLATE_NOOP("App::Property", "Data used to construct internal thread"))
        obj.addProperty("App::PropertyFloatList","external_data","ThreadProfile",QT_TRANSLATE_NOOP("App::Property", "Data used to construct external thread"))
        obj.addProperty("App::PropertyFloatList","internal2S_data","ThreadProfile",QT_TRANSLATE_NOOP("App::Property", "Data used to construct 2 start internal thread"))
        obj.addProperty("App::PropertyFloatList","external2S_data","ThreadProfile",QT_TRANSLATE_NOOP("App::Property", "Data used to construct 2 start external thread"))
        obj.addProperty("App::PropertyFloatList","internal3S_data","ThreadProfile",QT_TRANSLATE_NOOP("App::Property", "Data used to construct 3 start internal thread"))
        obj.addProperty("App::PropertyFloatList","external3S_data","ThreadProfile",QT_TRANSLATE_NOOP("App::Property", "Data used to construct 3 start external thread"))
        obj.addProperty("App::PropertyFloatList","internal45_data","ThreadProfile",QT_TRANSLATE_NOOP("App::Property", "Data used to construct 45 degree internal thread"))
        obj.addProperty("App::PropertyFloatList","external45_data","ThreadProfile",QT_TRANSLATE_NOOP("App::Property", "Data used to construct 45 degree external thread"))
        obj.addProperty("App::PropertyString","Helix","ThreadProfile","Name of the helix object associated with the profile, if any")
        obj.addProperty("App::PropertyStringList","preset_names","ThreadProfile",QT_TRANSLATE_NOOP("App::Property", "list of preset names"))
        obj.addProperty("App::PropertyFloatList","presets_data","ThreadProfile",QT_TRANSLATE_NOOP("App::Property","list of pitches and diameters"))
        obj.addProperty("App::PropertyFloatConstraint","Deviation","ThreadProfile", "Default is 0.1 for better looking threads, but 0.5 will be faster rendering.  Set this to 0 to ignore it and keep the sweep or body object at its current setting.").Deviation = (0.1,0,10000,0.1)
        obj.addProperty("App::PropertyLength", "Pitch", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "Pitch of the thread, use 25.4 / TPI if in mm mode else 1 / TPI to convert from threads per inch")).Pitch =1
        obj.addProperty("App::PropertyEnumeration", "InternalOrExternal", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "Whether to make internal or external thread profile"))
        obj.InternalOrExternal=["Internal", "External"]
        obj.InternalOrExternal="External"
        obj.addProperty("App::PropertyEnumeration","Variants","ThreadProfile",QT_TRANSLATE_NOOP("App::Property","Standard 60 degree V threads, experimental 3D printer-friendly 45 degree threads, 2-start, 3-start\n(Presets only valid for 60 degree types)")).Variants=["60","45","2-Start","3-Start"]
        obj.addProperty("App::PropertyEnumeration", "Presets", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "Some presets"))
        obj.addProperty("App::PropertyIntegerConstraint", "Quality", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "Quality of profile: controls how many points are used to create the bspline, the lower the number, the more points used. Experiment with different values if the thread looks rough up close.  Maximum points used is 720. Quality is divided into 720 to determine how many points to use.  You can also control appearance in the view tab of the Body or Sweep with the Angular Deflection and Deviation properties."))
        obj.addProperty("App::PropertyString", "Continuity", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "Continuity of the produced BSpline -- readonly"))
        obj.addProperty("App::PropertyStringList", "Instructions", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "Instructions")).Instructions=[\
"Expand this with the ... button to view instructions",\
"Sweep this object along a helix of the same pitch to produce your thread.",\
"It is recommended to make the helix in the ThreadProfile workbench.",\
"If there is an active Body the ThreadProfile object will be put into it.,"\
"If not it can be dragged and dropped into the body later.",\
"If there is an active Body when the helix is made there will be made a ShapeBinder for it",\
"For internal threads you will need to cut the Sweep object out of a cylinder, or if using Part Design sweep it as a Subtractive Pipe.",\
"Always use Frenet mode",\
"I have provided some presets, but it is possible there could be some errors.  Double check for mission critical applications.",\
"Also, the tolerances might be different from what you wish to have.  I believe the internal minor diameters are all minimum and the external are all maximum.",\
]
        obj.Quality = (11,1,240,1) #11 default, 1 minimum, 240 max, 1 step size
        obj.setEditorMode("internal_data", 2) #0 = normal, 1 = readonly, 2 = hidden
        obj.setEditorMode("Closed", 2)
        obj.setEditorMode("MakeFace", 2)
        obj.setEditorMode("external_data", 2)
        obj.setEditorMode("internal45_data",2)
        obj.setEditorMode("external45_data",2)
        obj.setEditorMode("internal2S_data",2)
        obj.setEditorMode("external2S_data",2)
        obj.setEditorMode("internal3S_data",2)
        obj.setEditorMode("external3S_data",2)
        obj.setEditorMode("Variants",2) #only shown for v thread types
        obj.setEditorMode("Area", 2)
        obj.setEditorMode("Version", 1)
        obj.setEditorMode("Continuity", 1)
        obj.setEditorMode("ThreadCount",1)
        obj.setEditorMode("preset_names", 2)
        obj.setEditorMode("presets_data", 2)
        obj.setEditorMode("MinorDiameterFinal", 1)
        obj.setEditorMode("MajorDiameterFinal", 1)
        obj.setEditorMode("d_delta", 2)
        obj.MakeFace = True
        obj.Closed = True
        obj.Points = []
        self.assureProperties(obj)


    def assureProperties(self, obj): # for Compatibility with older versions
        if not hasattr(obj, "Parameterization"):
            obj.addProperty("App::PropertyFloat","Parameterization","ThreadProfile",QT_TRANSLATE_NOOP("App::Property","Parameterization factor"))
            obj.Parameterization = 1.0
            obj.setEditorMode("Parameterization", 0)
            self.knotSeq = []

    def parameterization (self, pts, a, closed):
        # Computes a knot Sequence for a set of points
        # fac (0-1) : parameterization factor
        # fac=0 -> Uniform / fac=0.5 -> Centripetal / fac=1.0 -> Chord-Length
        if closed: # we need to add the first point as the end point
            pts.append(pts[0])
        params = [0]
        for i in range(1,len(pts)):
            p = pts[i].sub(pts[i-1])
            pl = pow(p.Length,a)
            params.append(params[-1] + pl)
        return params

    def makePoints(self, obj):
        if hasattr(obj.Pitch,"Value"): #compatibility with objects created with version <= 1.20
            pitch = obj.Pitch.Value
        else:
            pitch = obj.Pitch
        minor_diameter = obj.MinorDiameter.Value
        if "external" in obj.InternalOrExternal.lower():
            external = True
        else:
            if "internal" in obj.InternalOrExternal.lower():
                external=False
            else:
                FreeCAD.Console.PrintWarning("ThreadProfile: Unable to determine internal or external thread type, using external\n")
                external=True
        minor_diameter += obj.Tolerance
        step = obj.Quality #1 means do not skip any points, 2 means use every other, 3 every 3rd, etc.
        points = []
        alpha = 0
        idx = obj.preset_names.index(obj.Presets)

        if hasattr(obj,"Variants") and obj.Variants == "45": #only valid for v thread types
            if external:
                our_data = obj.external45_data
            else:
                our_data = obj.internal45_data
        elif hasattr(obj,"Variants") and obj.Variants == "2-Start":
            if external:
                our_data = obj.external2S_data
            else:
                our_data = obj.internal2S_data
        elif hasattr(obj,"Variants") and obj.Variants == "3-Start":
            if external:
                our_data = obj.external3S_data
            else:
                our_data = obj.internal3S_data
        else:
            if external:
                our_data = obj.external_data
            else:
                our_data = obj.internal_data
        max_diam = 0
        for ii in range(0, len(our_data),step):
            alpha += math.pi * 2 / len(our_data) * step
            od = our_data[ii]
            radius = minor_diameter / 2 + od * pitch
            max_diam = max(max_diam, radius * 2)
            x = math.cos(alpha) * radius
            y = math.sin(alpha) * radius
            points.append(Base.Vector(x,y,0))

        obj.d_delta = max_diam - minor_diameter
        obj.MajorDiameter = max_diam - obj.Tolerance
        obj.MinorDiameterFinal = obj.MinorDiameter.Value + obj.Tolerance
        obj.MajorDiameterFinal = obj.MajorDiameter.Value + obj.Tolerance

        return points

    def handleThreadCountChange(self, fp, prop):
        if not "ThreadCount" in prop:
            return
        ins = fp.InList
        for inobj in ins:
            if hasattr(inobj,"Spine"):
                spine = inobj.Spine
                helix = spine[0]
                edgeNames = []
                for ii in range(1,math.ceil(getattr(fp,prop))+1):
                    edgeNames.append("Edge"+str(ii))
                inobj.Spine = [helix,edgeNames]

    def onDocumentRestored(self, obj):
        if not hasattr(obj, "MajorDiameter") or not hasattr(obj, "MajorDiameterFinal"):
            if not hasattr(obj, "MajorDiameter"):
                obj.addProperty("App::PropertyLength", "MajorDiameter", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "The major diameter of the thread"))
                obj.addProperty("App::PropertyFloat", "Tolerance", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "The tolerance of the thread. It will be added to diameters"))
                obj.addProperty("App::PropertyFloat", "d_delta", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", ""))
                obj.setEditorMode("d_delta", 2)
            if not hasattr(obj, "MajorDiameterFinal"):
                obj.addProperty("App::PropertyLength", "MinorDiameterFinal", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "The minor diameter of the thread with tolerance"))
                obj.addProperty("App::PropertyLength", "MajorDiameterFinal", "ThreadProfile", QT_TRANSLATE_NOOP("App::Property", "The major diameter of the thread with tolerance"))
                obj.setEditorMode("MinorDiameterFinal", 1)
                obj.setEditorMode("MajorDiameterFinal", 1)
            self.makePoints(obj)

    def onChanged(self, fp, prop):
        if prop == "Parameterization":
            if fp.Parameterization < 0.:
                fp.Parameterization = 0.
            if fp.Parameterization > 1.0:
                fp.Parameterization = 1.0
        if prop == "Presets" or prop == "InternalOrExternal":
            if hasattr(fp,"Presets"):
                preset_string = getattr(fp,"Presets")
                if preset_string in fp.preset_names:
                    idx = fp.preset_names.index(preset_string)
                    if idx != 0:
                        fp.Pitch = fp.presets_data[idx*3]
                        if "External" in fp.InternalOrExternal:
                            fp.MinorDiameter = fp.presets_data[idx*3+1]
                        else:
                            fp.MinorDiameter = fp.presets_data[idx*3+2]
        if prop == "MajorDiameter":
            fp.MinorDiameter = fp.MajorDiameter.Value - fp.d_delta
        if prop == "ThreadCount":
            self.handleThreadCountChange(fp, prop)
        if prop == "Variants":
            helix = FreeCAD.ActiveDocument.getObject(fp.Helix)
            if helix:
                if fp.Variants =="2-Start":
                    helix.setExpression("Pitch",fp.Name+".Pitch*2")
                    helix.setExpression("Height",fp.Name+".ThreadCount*"+fp.Name+".Pitch*2")
                elif fp.Variants == "60" or fp.Variants == "45":
                    helix.setExpression("Pitch",fp.Name+".Pitch")
                    helix.setExpression("Height",fp.Name+".ThreadCount*"+fp.Name+".Pitch")
                elif fp.Variants == "3-Start":
                    helix.setExpression("Pitch",fp.Name+".Pitch*3")
                    helix.setExpression("Height",fp.Name+".ThreadCount*"+fp.Name+".Pitch*3")
        if prop == "Height" or prop == "Pitch" or prop == "Variants" or prop == "Presets":
            if hasattr(fp, "Variants") and hasattr(fp,"ThreadCount") and hasattr(fp,"Pitch") and fp.Pitch.Value != 0:
                fp.ThreadCount = fp.Height/fp.Pitch.Value
                fp.ThreadCount = fp.ThreadCount / 3 if fp.Variants == "3-Start" else fp.ThreadCount / 2 if fp.Variants == "2-Start" else fp.ThreadCount
                #self.handleThreadCountChange(fp, prop)
        if prop == "Deviation":
            for dep in fp.InList:
                if dep.isDerivedFrom("PartDesign::Body") or dep.isDerivedFrom("Part::Sweep"):
                    dep.ViewObject.Deviation = fp.Deviation if fp.Deviation else dep.ViewObject.Deviation

    def execute(self, obj):
        obj.Points = self.makePoints(obj)
        import Part
        self.assureProperties(obj)
        if obj.Points:
            self.knotSeq = self.parameterization(obj.Points, obj.Parameterization, obj.Closed)
            plm = obj.Placement
            if obj.Closed and (len(obj.Points) > 2):
                if obj.Points[0] == obj.Points[-1]:  # should not occur, but OCC will crash
                    FreeCAD.Console.PrintError(tr('ThreadProfile',  '_ThreadProfile.createGeometry: Closed with same first/last Point. Geometry not updated.')+"\n")
                    return
                spline = Part.BSplineCurve()
                spline.interpolate(obj.Points, PeriodicFlag = True, Parameters = self.knotSeq)
                #spline.approximate(Points = obj.Points, DegMin = 3, DegMax = 5, Tolerance = .003692, Continuity = 'C3', ParamType = 'ChordLength')
                #spline.setPeriodic()
                # DNC: bug fix: convert to face if closed
                shape = Part.Wire(spline.toShape())
                # Creating a face from a closed spline cannot be expected to always work
                # Usually, if the spline is not flat the call of Part.Face() fails
                try:
                    shape = Part.makeFace(shape, "Part::FaceMakerBullseye")
                except Part.OCCError as e:
                    FreeCAD.Console.PrintError(f"ThreadProfile can't make face {e}\n")
                obj.Shape = shape
                if hasattr(obj,"Area") and hasattr(shape,"Area"):
                    obj.Area = shape.Area
            else:
                spline = Part.BSplineCurve()
                spline.interpolate(obj.Points, PeriodicFlag = False, Parameters = self.knotSeq)
                #spline.approximate(Points = obj.Points, DegMin = 3, DegMax = 5, Tolerance = .003692, Continuity = 'C3', ParamType = 'ChordLength')
                #spline.setPeriodic()
                shape = spline.toShape()
                obj.Shape = shape
                if hasattr(obj,"Area") and hasattr(shape,"Area"):
                    obj.Area = shape.Area
            if hasattr(obj,"Variants"):
                if obj.Variants == "2-Start":
                    plm = obj.Shape.Placement
                    shape1 = obj.Shape.copy()
                    shape1.Placement = Base.Placement()
                    shape2 = shape1.copy().rotate(Base.Vector(0,0,0),Base.Vector(0,0,1),180)
                    fuse = shape1.fuse(shape2).removeSplitter().Face1
                    fuse.Placement = plm
                    obj.Shape = fuse
                elif obj.Variants == "3-Start":
                    plm = obj.Shape.Placement
                    shape1 = obj.Shape.copy()
                    shape1.Placement = Base.Placement()
                    shape2 = shape1.copy().rotate(Base.Vector(0,0,0),Base.Vector(0,0,1),120)
                    shape3 = shape1.copy().rotate(Base.Vector(0,0,0),Base.Vector(0,0,1),240)
                    fuse = shape1.multiFuse([shape2,shape3]).removeSplitter().Face1
                    fuse.Placement = plm
                    obj.Shape = fuse

            obj.Continuity = spline.Continuity
            obj.Placement = plm
        obj.positionBySupport()

    # for compatibility with older versions
    _ViewProviderBSpline = _ViewProviderWire

#######################################################################################
# Keep Toolbar active even after leaving workbench

class ThreadProfileSettingsCommandClass(object):
    """Settings, currently only whether to keep toolbar after leaving workbench"""

    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'Settings.svg') , # the name of an icon file available in the resources
            'MenuText': "&Settings" ,
            'ToolTip' : "Workbench settings dialog"}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        from PySide import QtGui
        window = QtGui.QApplication.activeWindow()
        pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/ThreadProfile")
        lh = pg.GetBool("LinkHelixPlacementParametrically", True)
        keep = pg.GetBool('KeepToolbar',True)
        items=["Keep the toolbar active","Do not keep the toolbar active","Link helix placement parametrically", "Do not link helix placement parametrically","Cancel"]
        if keep:
            items[0]="*"+items[0]
        else:
            items[1] = "*"+items[1]
        if lh:
            items[2] = "*"+items[2]
        else:
            items[3] = "*"+items[3]
        item,ok = QtGui.QInputDialog.getItem(window,'ThreadProfile','Settings\n\nSelect the settings option\n',items,0,False)
        if ok and item == items[-1]:
            return
        elif ok and item == items[0]:
            keep = True
            pg.SetBool('KeepToolbar', keep)
        elif ok and item==items[1]:
            keep = False
            pg.SetBool('KeepToolbar', keep)
        elif ok and item == items[2]:
            pg.SetBool('LinkHelixPlacementParametrically', True)
        elif ok and item == items[3]:
            pg.SetBool('LinkHelixPlacementParametrically', False)
        return

    def IsActive(self):
        return True


#Gui.addCommand("ThreadProfileKeepToolbar", ThreadProfileKeepToolbarCommandClass())
###################################################################################

class ThreadProfileMakeHelixCommandClass(object):
    """Make Helix command"""
    def __init__(self):
        self.Pitch = None
        self.Placement = None
        self.Name = None

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'MakeHelix.svg') ,
            'MenuText': "&Make Helix" ,
            'ToolTip' : "Make a Part::Helix object, set its pitch to match."}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        doc.openTransaction("Make Helix")
        import Part,PartGui
        helix = doc.addObject("Part::Helix","Helix")
        profile = doc.getObject(self.Name)
        doc.recompute()
        name = doc.ActiveObject.Name
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(doc.Name,profile.Name)
        FreeCADGui.Selection.addSelection(doc.Name,helix.Name)
        getattr(doc,name).Label = name
        getattr(doc,name).setExpression("Pitch",self.Name+'.Pitch')
        getattr(doc,name).setExpression("Height",self.Name+'.ThreadCount*'+self.Name+'.Pitch')
        if hasattr(helix,"SegmentLength"):
            helix.setExpression("SegmentLength","1")
        if hasattr(profile,"Helix"):
            profile.Helix = helix.Name
            if profile.Variants == "2-Start":
                getattr(doc,name).setExpression("Pitch",self.Name+'.Pitch*2')
                helix.setExpression("Height",self.Name+'.ThreadCount*'+self.Name+'.Pitch*2')
            elif profile.Variants == "3-Start":
                getattr(doc,name).setExpression("Pitch",self.Name+'.Pitch*3')
                helix.setExpression("Height",self.Name+'.ThreadCount*'+self.Name+'.Pitch*3')

        pg = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/ThreadProfile")
        if pg.GetBool("LinkHelixPlacementParametrically", True):
            if hasattr(helix,"Support"):
                helix.setExpression("Support",profile.Name+".Support")
            else:
                helix.setExpression("AttachmentSupport", profile.Name+".AttachmentSupport")
            helix.setExpression("MapMode",profile.Name+".MapMode")
            helix.setExpression("MapPathParameter",profile.Name+".MapPathParameter")
            helix.setExpression("MapReversed",profile.Name+".MapReversed")
            helix.setExpression("AttachmentOffset",profile.Name+".AttachmentOffset")
        else:
            if hasattr(helix,"Support"):
                helix.Support = profile.Support
            else:
                helix.AttachmentSupport = profileAttachmentSupport
            helix.MapMode = profile.MapMode
            helix.MapPathParameter = profile.MapPathParameter
            helix.MapReversed = profile.MapReversed
            helix.AttachmentOffset = profile.AttachmentOffset
        body=FreeCADGui.ActiveDocument.ActiveView.getActiveObject("pdbody")
        part=FreeCADGui.ActiveDocument.ActiveView.getActiveObject("part")
        if body:
            body.Group=body.Group+[getattr(doc,name)] #put helix in body to avoid out of scope warnings
        elif part:
            part.Group=part.Group+[getattr(doc,name)]
        doc.commitTransaction()
        doc.recompute()
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        selection = Gui.Selection.getSelectionEx()
        if not selection:
            return False
        if not "ThreadProfile" in selection[0].Object.Name:
            return False
        else:
            self.Pitch = selection[0].Object.Pitch
            self.Placement = selection[0].Object.Placement
            self.Name = selection[0].Object.Name
        return True
###################################################################################

class ThreadProfileDoSweepCommandClass(object):
    """Perform sweep command"""
    def __init__(self):
        self.helixName = None
        self.profileName = None

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'DoSweep.svg') ,
            'MenuText': "&Do Sweep" ,
            'ToolTip' : "Sweep selected thread profile along selected helix"}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        import PartDesignGui
        import Part
        from PySide import QtGui,QtCore
        profile = doc.getObject(self.profileName)
        if not hasattr(profile, "Deviation"):
            profile.addProperty("App::PropertyFloat","Deviation","ThreadProfile", "Default = 0.1, improves the looks of the thread, but 0.5 or higher is faster rendering.  Set to 0 to keep the current sweep or body deviation.").Deviation = (0.1,0,10000,0.1)

        body = FreeCADGui.ActiveDocument.ActiveView.getActiveObject("pdbody")
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        if not body:
            doc.openTransaction("Perform sweep")
            doc.addObject('Part::Sweep','Sweep')
            doc.ActiveObject.Sections=[getattr(doc,self.profileName),]
            edgeList = []
            count = len(getattr(doc,self.helixName).Shape.Edges)
            for ii in range(1,count+1):
                edgeList.append("Edge"+str(ii))
            doc.ActiveObject.Spine=(getattr(doc,self.helixName),edgeList)
            doc.ActiveObject.Solid=True
            doc.ActiveObject.Frenet=True
            doc.ActiveObject.ViewObject.Deviation = profile.Deviation if profile.Deviation else doc.ActiveObject.ViewObject.Deviation
            FreeCADGui.getDocument(doc.Name).getObject(self.profileName).Visibility = False
            FreeCADGui.getDocument(doc.Name).getObject(self.helixName).Visibility = False

        elif body: #if there is active part design body
            body.ViewObject.Deviation = profile.Deviation
            if "External" in getattr(doc,self.profileName).InternalOrExternal:
                #additive part design sweep
                doc.openTransaction("AdditivePipe")
                pipe = body.newObject("PartDesign::AdditivePipe","AdditivePipe")
            else:
                doc.openTransaction("SubtractivePipe")
                pipe = body.newObject("PartDesign::SubtractivePipe","SubtractivePipe")

            pipe.Profile = getattr(doc, self.profileName)
            pipe.Spine = getattr(doc,self.helixName)
            pipe.Mode = 'Frenet'
            Gui.activeDocument().hide(self.profileName)
            Gui.activeDocument().hide(self.helixName)
            #pipe.ViewObject.ShapeColor=body.ViewObject.ShapeColor
            #pipe.ViewObject.LineColor=body.ViewObject.LineColor
            #pipe.ViewObject.PointColor=body.ViewObject.PointColor
            #pipe.ViewObject.Transparency=body.ViewObject.Transparency
            #pipe.ViewObject.DisplayMode=body.ViewObject.DisplayMode
            pipe.ViewObject.makeTemporaryVisible(True)
            FreeCADGui.activeDocument().setEdit(pipe.Name,0)
            FreeCADGui.getDocument(doc.Name).getObject(pipe.Name).Visibility=True
        doc.commitTransaction()
        doc.recompute()
        QtGui.QApplication.restoreOverrideCursor()
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        selection = Gui.Selection.getSelectionEx()
        if not selection:
            return False
        if len(selection) != 2:
            return False
        profileFound = False
        helixFound = False
        self.helixName = ''
        for s in selection:
            if hasattr(s,"Object") and hasattr(s.Object,"Name") and "ThreadProfile" in s.Object.Name:
                profileFound = True
                self.profileName = s.Object.Name
            if hasattr(s, "Object") and hasattr(s.Object,"Name") and "Helix" in s.Object.Name:
                helixFound = True
                self.helixName = s.Object.Name
        if profileFound and helixFound:
            return True
        else:
            return False

###################################################################################

class ThreadProfileOpenOnlineCalculatorCommandClass(object):
    """Open Online Calculator command"""
    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'OpenOnlineCalculator.svg') ,
            'MenuText': "&Open Online Calculator" ,
            'ToolTip' : "Open online calculator to determine minor diameter for desired thread fit."}

    def Activated(self):
        import webbrowser
        items = ["Open online metric calculator", "Open online unified inch calculator", "Open online ANSI buttress thread calculator","Cancel"]
        window = QtGui.QApplication.activeWindow()
        item,ok = QtGui.QInputDialog.getItem(window,'ThreadProfile','Open online calculator in default browser?',items,0,False)
        if ok and item == items[0]:
            webbrowser.open('https://amesweb.info/Screws/IsoMetricScrewThread.aspx')
        elif ok and item == items[1]:
            webbrowser.open('https://amesweb.info/Screws/AsmeUnifiedInchScrewThread.aspx')
        elif ok and item == items[2]:
            webbrowser.open('https://amesweb.info/Screws/ButtressInchScrewThreads.aspx')

        return

    def IsActive(self):
        return True


####################################################################################
# Create the thread profile object

class ThreadProfileCreateObjectCommandClass(object):
    """Create Object command"""

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreateObject.svg') ,
            'MenuText': "&Create V thread profile" ,
            'ToolTip' : "Create the standard V thread ThreadProfile object"}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        doc.openTransaction("Create VThreadProfile")
        try:
            fp = self.makeThreadProfile()
            fp.setEditorMode("Variants",0)
        except Exception as e:
            FreeCAD.Console.PrintError(
    	        "ThreadProfile Error: Exception creating thread profile object.\n\n" +
    	        '\n'.join(traceback.format_exception(e)) + "\n"
            )
            QtGui.QApplication.restoreOverrideCursor()
        doc.commitTransaction()
        doc.recompute()
        QtGui.QApplication.restoreOverrideCursor()
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        return True

    def getHelp(self):
        return ["Created with ThreadProfile (v"+str(version)+") workbench.",
                "This is a thread profile object built",
                "for sweeping along a helix in either the",
                "Part or Part Design workbench."
                "installation of the ThreadProfile workbench is required.",
]

    def makeThreadProfile(self,name="VThreadProfile",minor_diameter=4.773,pitch=1,internal_or_external="External",internal_data=[],external_data=[],internal45_data=[],external45_data=[],internal2S_data=[],external2S_data=[],internal3S_data=[],external3S_data=[],presets=[],thread_count=10,Quality=11):
        '''minor_diameter=4.891,pitch=1,closed=True,placement=None,face=None,support=None,internal_or_external="External",internal_data=[],external_data=[]): Creates a thread profile object
    that can be swept along a helix to produce a thread.  Code is based on Draft.makeBSpline()'''
        if not FreeCAD.ActiveDocument:
            FreeCAD.Console.PrintError("No active document. Aborting\n")
            return
        else: fname = name
        obj = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython",fname)
        _ThreadProfile(obj)
        obj.Closed = True
        if hasattr(obj, "Support"):
            obj.Support = None
        obj.Quality = Quality
        #allow to include custom thread profile for internal_data or external_data
        #these are 720 floats of the x-coordinates
        #of a thread profile with pitch=1 sketched on the xz plane
        #with x=0 at the minor radius of the profile
        #the element position is the z-coordinate / 720 (2 points per degree)
        #y-coordinate is always zero
        #the thread profile produced is a function of these values, minor diameter, and pitch
        if len(internal_data)==0:
            obj.internal_data = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.002405626122,0.004811252243,0.007216878365,0.009622504486,0.012028130608,0.01443375673,0.016839382851,0.019245008973,0.021650635095,0.024056261216,0.026461887338,0.028867513459,0.031273139581,0.033678765703,0.036084391824,0.038490017946,0.040895644068,0.043301270189,0.045706896311,0.048112522432,0.050518148554,0.052923774676,0.055329400797,0.057735026919,0.060140653041,0.062546279162,0.064951905284,0.067357531405,0.069763157527,0.072168783649,0.07457440977,0.076980035892,0.079385662014,0.081791288135,0.084196914257,0.086602540378,0.0890081665,0.091413792622,0.093819418743,0.096225044865,0.098630670987,0.101036297108,0.10344192323,0.105847549351,0.108253175473,0.110658801595,0.113064427716,0.115470053838,0.11787567996,0.120281306081,0.122686932203,0.125092558324,0.127498184446,0.129903810568,0.132309436689,0.134715062811,0.137120688933,0.139526315054,0.141931941176,0.144337567297,0.146743193419,0.149148819541,0.151554445662,0.153960071784,0.156365697906,0.158771324027,0.161176950149,0.16358257627,0.165988202392,0.168393828514,0.170799454635,0.173205080757,0.175610706879,0.178016333,0.180421959122,0.182827585243,0.185233211365,0.187638837487,0.190044463608,0.19245008973,0.194855715851,0.197261341973,0.199666968095,0.202072594216,0.204478220338,0.20688384646,0.209289472581,0.211695098703,0.214100724824,0.216506350946,0.218911977068,0.221317603189,0.223723229311,0.226128855433,0.228534481554,0.230940107676,0.233345733797,0.235751359919,0.238156986041,0.240562612162,0.242968238284,0.245373864406,0.247779490527,0.250185116649,0.25259074277,0.254996368892,0.257401995014,0.259807621135,0.262213247257,0.264618873379,0.2670244995,0.269430125622,0.271835751743,0.274241377865,0.276647003987,0.279052630108,0.28145825623,0.283863882352,0.286269508473,0.288675134595,0.291080760716,0.293486386838,0.29589201296,0.298297639081,0.300703265203,0.303108891325,0.305514517446,0.307920143568,0.310325769689,0.312731395811,0.315137021933,0.317542648054,0.319948274176,0.322353900298,0.324759526419,0.327165152541,0.329570778662,0.331976404784,0.334382030906,0.336787657027,0.339193283149,0.341598909271,0.344004535392,0.346410161514,0.348815787635,0.351221413757,0.353627039879,0.356032666,0.358438292122,0.360843918244,0.363249544365,0.365655170487,0.368060796608,0.37046642273,0.372872048852,0.375277674973,0.377683301095,0.380088927216,0.382494553338,0.38490017946,0.387305805581,0.389711431703,0.392117057825,0.394522683946,0.396928310068,0.399333936189,0.401739562311,0.404145188433,0.406550814554,0.408956440676,0.411362066798,0.413767692919,0.416173319041,0.418578945162,0.420984571284,0.423390197406,0.425795823527,0.428201449649,0.430607075771,0.433012701892,0.435418328014,0.437823954135,0.440229580257,0.442635206379,0.4450408325,0.447446458622,0.449852084744,0.452257710865,0.454663336987,0.457068963108,0.45947458923,0.461880215352,0.464285841473,0.466691467595,0.469097093717,0.471502719838,0.47390834596,0.476313972081,0.478719598203,0.481125224325,0.483530850446,0.485936476568,0.48834210269,0.490747728811,0.493153354933,0.495558981054,0.497964607176,0.500370233298,0.502775859419,0.505181485541,0.507587111663,0.509992737784,0.512398363906,0.514803990027,0.517209616149,0.519615242271,0.522020868392,0.524426494514,0.526832120636,0.529237746757,0.531643372879,0.534048999,0.536454625122,0.538860251244,0.541265877365,0.543571138211,0.545698019279,0.547673314821,0.549517290262,0.55124571874,0.5528711653,0.554403833171,0.55585214206,0.557223135528,0.558522775457,0.55975615972,0.560927686209,0.56204117857,0.563099984046,0.56410705064,0.5650649887,0.565976120619,0.56684252132,0.567666051537,0.568448385396,0.56919103344,0.56989536197,0.570562609407,0.571193900198,0.571790256698,0.572352609371,0.57288180558,0.573378617192,0.573843747176,0.57427783534,0.574681463337,0.57505515903,0.575399400317,0.575714618461,0.576001201008,0.576259494329,0.576489805835,0.576692405885,0.576867529433,0.577015377435,0.577136118024,0.577229887482,0.577296791017,0.577336903362,0.57735026919,0.577336903362,0.577296791017,0.577229887482,0.577136118024,0.577015377435,0.576867529433,0.576692405885,0.576489805835,0.576259494329,0.576001201008,0.575714618461,0.575399400317,0.57505515903,0.574681463337,0.57427783534,0.573843747176,0.573378617192,0.57288180558,0.572352609371,0.571790256698,0.571193900198,0.570562609407,0.56989536197,0.56919103344,0.568448385396,0.567666051537,0.56684252132,0.565976120619,0.5650649887,0.56410705064,0.563099984047,0.56204117857,0.560927686209,0.55975615972,0.558522775457,0.557223135528,0.55585214206,0.554403833171,0.552871165301,0.55124571874,0.549517290262,0.547673314821,0.545698019279,0.543571138211,0.541265877365,0.538860251244,0.536454625122,0.534048999001,0.531643372879,0.529237746757,0.526832120636,0.524426494514,0.522020868393,0.519615242271,0.517209616149,0.514803990028,0.512398363906,0.509992737784,0.507587111663,0.505181485541,0.50277585942,0.500370233298,0.497964607176,0.495558981055,0.493153354933,0.490747728811,0.48834210269,0.485936476568,0.483530850447,0.481125224325,0.478719598203,0.476313972082,0.47390834596,0.471502719838,0.469097093717,0.466691467595,0.464285841474,0.461880215352,0.45947458923,0.457068963109,0.454663336987,0.452257710865,0.449852084744,0.447446458622,0.445040832501,0.442635206379,0.440229580257,0.437823954136,0.435418328014,0.433012701892,0.430607075771,0.428201449649,0.425795823528,0.423390197406,0.420984571284,0.418578945163,0.416173319041,0.413767692919,0.411362066798,0.408956440676,0.406550814555,0.404145188433,0.401739562311,0.39933393619,0.396928310068,0.394522683946,0.392117057825,0.389711431703,0.387305805582,0.38490017946,0.382494553338,0.380088927217,0.377683301095,0.375277674973,0.372872048852,0.37046642273,0.368060796609,0.365655170487,0.363249544365,0.360843918244,0.358438292122,0.356032666001,0.353627039879,0.351221413757,0.348815787636,0.346410161514,0.344004535392,0.341598909271,0.339193283149,0.336787657028,0.334382030906,0.331976404784,0.329570778663,0.327165152541,0.324759526419,0.322353900298,0.319948274176,0.317542648055,0.315137021933,0.312731395811,0.31032576969,0.307920143568,0.305514517446,0.303108891325,0.300703265203,0.298297639082,0.29589201296,0.293486386838,0.291080760717,0.288675134595,0.286269508473,0.283863882352,0.28145825623,0.279052630109,0.276647003987,0.274241377865,0.271835751744,0.269430125622,0.2670244995,0.264618873379,0.262213247257,0.259807621136,0.257401995014,0.254996368892,0.252590742771,0.250185116649,0.247779490527,0.245373864406,0.242968238284,0.240562612163,0.238156986041,0.235751359919,0.233345733798,0.230940107676,0.228534481554,0.226128855433,0.223723229311,0.22131760319,0.218911977068,0.216506350946,0.214100724825,0.211695098703,0.209289472581,0.20688384646,0.204478220338,0.202072594217,0.199666968095,0.197261341973,0.194855715852,0.19245008973,0.190044463608,0.187638837487,0.185233211365,0.182827585244,0.180421959122,0.178016333,0.175610706879,0.173205080757,0.170799454636,0.168393828514,0.165988202392,0.163582576271,0.161176950149,0.158771324027,0.156365697906,0.153960071784,0.151554445663,0.149148819541,0.146743193419,0.144337567298,0.141931941176,0.139526315054,0.137120688933,0.134715062811,0.13230943669,0.129903810568,0.127498184446,0.125092558325,0.122686932203,0.120281306081,0.11787567996,0.115470053838,0.113064427717,0.110658801595,0.108253175473,0.105847549352,0.10344192323,0.101036297108,0.098630670987,0.096225044865,0.093819418744,0.091413792622,0.0890081665,0.086602540379,0.084196914257,0.081791288135,0.079385662014,0.076980035892,0.074574409771,0.072168783649,0.069763157527,0.067357531406,0.064951905284,0.062546279162,0.060140653041,0.057735026919,0.055329400798,0.052923774676,0.050518148554,0.048112522433,0.045706896311,0.043301270189,0.040895644068,0.038490017946,0.036084391825,0.033678765703,0.031273139581,0.02886751346,0.026461887338,0.024056261216,0.021650635095,0.019245008973,0.016839382852,0.01443375673,0.012028130608,0.009622504487,0.007216878365,0.004811252244,0.002405626122]
        else:
            obj.internal_data = internal_data
        if len(external_data)==0:
            obj.external_data = [-0.002353874267,-0.004610521688,-0.006778280188,-0.008864283825,-0.010874693731,-0.012814874909,-0.014689533648,-0.016502825791,-0.018258443075,-0.019959682748,-0.021609504262,-0.023210575868,-0.024765313218,-0.026275911608,-0.027744373085,-0.029172529388,-0.030562061489,-0.031914516323,-0.033231321182,-0.034513796181,-0.035763165074,-0.036980564707,-0.038167053291,-0.039323617685,-0.040451179823,-0.041550602408,-0.042622693966,-0.043668213361,-0.04468787382,-0.045682346547,-0.046652263972,-0.047598222668,-0.048520785999,-0.049420486507,-0.050297828076,-0.051153287908,-0.051987318311,-0.052800348341,-0.05359278529,-0.05436501606,-0.055117408419,-0.055850312148,-0.056564060107,-0.057258969208,-0.057935341316,-0.058593464082,-0.059233611709,-0.059856045664,-0.06046101534,-0.061048758664,-0.061619502667,-0.062173464009,-0.062710849475,-0.063231856427,-0.06373667323,-0.064225479652,-0.06469844723,-0.06515573962,-0.065597512915,-0.066023915948,-0.066435090577,-0.066831171941,-0.067212288714,-0.067578563329,-0.067930112196,-0.068267045903,-0.068589469403,-0.06889748219,-0.069191178464,-0.069470647283,-0.069735972706,-0.069987233927,-0.070224505396,-0.070447856939,-0.070657353858,-0.070853057037,-0.071035023027,-0.071203304134,-0.071357948492,-0.071499000139,-0.071626499073,-0.071740481317,-0.071840978965,-0.071928020232,-0.072001629489,-0.072061827303,-0.07210863046,-0.072142051993,-0.072162101198,-0.072168783647,-0.072162101198,-0.072142051993,-0.07210863046,-0.072061827303,-0.072001629489,-0.071928020232,-0.071840978965,-0.071740481317,-0.071626499073,-0.071499000139,-0.071357948492,-0.071203304134,-0.071035023027,-0.070853057037,-0.070657353858,-0.070447856939,-0.070224505396,-0.069987233927,-0.069735972706,-0.069470647283,-0.069191178464,-0.06889748219,-0.068589469403,-0.068267045903,-0.067930112196,-0.067578563329,-0.067212288714,-0.066831171941,-0.066435090577,-0.066023915948,-0.065597512915,-0.06515573962,-0.06469844723,-0.064225479652,-0.06373667323,-0.063231856427,-0.062710849475,-0.062173464009,-0.061619502667,-0.061048758664,-0.06046101534,-0.059856045664,-0.059233611709,-0.058593464082,-0.057935341316,-0.057258969208,-0.056564060107,-0.055850312148,-0.055117408419,-0.05436501606,-0.05359278529,-0.052800348341,-0.051987318311,-0.051153287908,-0.050297828076,-0.049420486507,-0.048520785999,-0.047598222668,-0.046652263972,-0.045682346547,-0.04468787382,-0.043668213361,-0.042622693966,-0.041550602408,-0.040451179823,-0.039323617685,-0.038167053291,-0.036980564707,-0.035763165074,-0.034513796181,-0.033231321182,-0.031914516323,-0.030562061489,-0.029172529388,-0.027744373085,-0.026275911608,-0.024765313218,-0.023210575868,-0.021609504262,-0.019959682748,-0.018258443075,-0.016502825791,-0.014689533648,-0.012814874909,-0.010874693731,-0.008864283825,-0.006778280188,-0.004610521688,-0.002353874267,-1e-12,0.002405626125,0.004811252246,0.007216878368,0.009622504489,0.012028130611,0.014433756733,0.016839382854,0.019245008976,0.021650635097,0.024056261219,0.026461887341,0.028867513462,0.031273139584,0.033678765706,0.036084391827,0.038490017949,0.04089564407,0.043301270192,0.045706896314,0.048112522435,0.050518148557,0.052923774678,0.0553294008,0.057735026922,0.060140653043,0.062546279165,0.064951905286,0.067357531408,0.06976315753,0.072168783651,0.074574409773,0.076980035894,0.079385662016,0.081791288138,0.084196914259,0.086602540381,0.089008166503,0.091413792624,0.093819418746,0.096225044867,0.098630670989,0.101036297111,0.103441923232,0.105847549354,0.108253175475,0.110658801597,0.113064427719,0.11547005384,0.117875679962,0.120281306083,0.122686932205,0.125092558327,0.127498184448,0.12990381057,0.132309436692,0.134715062813,0.137120688935,0.139526315056,0.141931941178,0.1443375673,0.146743193421,0.149148819543,0.151554445664,0.153960071786,0.156365697908,0.158771324029,0.161176950151,0.163582576272,0.165988202394,0.168393828516,0.170799454637,0.173205080759,0.175610706881,0.178016333002,0.180421959124,0.182827585245,0.185233211367,0.187638837489,0.19004446361,0.192450089732,0.194855715853,0.197261341975,0.199666968097,0.202072594218,0.20447822034,0.206883846461,0.209289472583,0.211695098705,0.214100724826,0.216506350948,0.218911977069,0.221317603191,0.223723229313,0.226128855434,0.228534481556,0.230940107678,0.233345733799,0.235751359921,0.238156986042,0.240562612164,0.242968238286,0.245373864407,0.247779490529,0.25018511665,0.252590742772,0.254996368894,0.257401995015,0.259807621137,0.262213247258,0.26461887338,0.267024499502,0.269430125623,0.271835751745,0.274241377867,0.276647003988,0.27905263011,0.281458256231,0.283863882353,0.286269508475,0.288675134596,0.291080760718,0.293486386839,0.295892012961,0.298297639083,0.300703265204,0.303108891326,0.305514517447,0.307920143569,0.310325769691,0.312731395812,0.315137021934,0.317542648056,0.319948274177,0.322353900299,0.32475952642,0.327165152542,0.329570778664,0.331976404785,0.334382030907,0.336787657028,0.33919328315,0.341598909272,0.344004535393,0.346410161515,0.348815787636,0.351221413758,0.35362703988,0.356032666001,0.358438292123,0.360843918245,0.363249544366,0.365655170488,0.368060796609,0.370466422731,0.372872048853,0.375277674974,0.377683301096,0.380088927217,0.382494553339,0.384900179461,0.387305805582,0.389711431704,0.392117057825,0.394522683947,0.396928310069,0.39933393619,0.401739562312,0.404145188433,0.406550814555,0.408956440677,0.411362066798,0.41376769292,0.416173319042,0.418578945163,0.420984571285,0.423390197406,0.425795823528,0.42820144965,0.430607075771,0.433012701893,0.435418328014,0.437823954136,0.440229580258,0.442635206379,0.445040832501,0.447446458622,0.449852084744,0.452257710866,0.454663336987,0.457068963109,0.459474589231,0.461880215352,0.464285841474,0.466691467595,0.469097093717,0.471502719839,0.47390834596,0.476313972082,0.478719598203,0.481125224325,0.483530850447,0.485936476568,0.48834210269,0.490747728811,0.493153354933,0.495558981055,0.497964607176,0.500370233298,0.50277585942,0.505181485541,0.507587111663,0.509992737784,0.512398363906,0.514803990028,0.517209616149,0.519615242271,0.522020868392,0.524426494514,0.526832120636,0.529237746757,0.531643372879,0.534048999,0.536454625122,0.538860251244,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.538860251244,0.536454625122,0.534048999,0.531643372879,0.529237746757,0.526832120636,0.524426494514,0.522020868392,0.519615242271,0.517209616149,0.514803990027,0.512398363906,0.509992737784,0.507587111663,0.505181485541,0.502775859419,0.500370233298,0.497964607176,0.495558981054,0.493153354933,0.490747728811,0.48834210269,0.485936476568,0.483530850446,0.481125224325,0.478719598203,0.476313972081,0.47390834596,0.471502719838,0.469097093717,0.466691467595,0.464285841473,0.461880215352,0.45947458923,0.457068963108,0.454663336987,0.452257710865,0.449852084744,0.447446458622,0.4450408325,0.442635206379,0.440229580257,0.437823954135,0.435418328014,0.433012701892,0.430607075771,0.428201449649,0.425795823527,0.423390197406,0.420984571284,0.418578945162,0.416173319041,0.413767692919,0.411362066798,0.408956440676,0.406550814554,0.404145188433,0.401739562311,0.399333936189,0.396928310068,0.394522683946,0.392117057825,0.389711431703,0.387305805581,0.38490017946,0.382494553338,0.380088927217,0.377683301095,0.375277674973,0.372872048852,0.37046642273,0.368060796608,0.365655170487,0.363249544365,0.360843918244,0.358438292122,0.356032666,0.353627039879,0.351221413757,0.348815787635,0.346410161514,0.344004535392,0.341598909271,0.339193283149,0.336787657027,0.334382030906,0.331976404784,0.329570778662,0.327165152541,0.324759526419,0.322353900298,0.319948274176,0.317542648054,0.315137021933,0.312731395811,0.310325769689,0.307920143568,0.305514517446,0.303108891325,0.300703265203,0.298297639081,0.29589201296,0.293486386838,0.291080760716,0.288675134595,0.286269508473,0.283863882352,0.28145825623,0.279052630108,0.276647003987,0.274241377865,0.271835751743,0.269430125622,0.2670244995,0.264618873379,0.262213247257,0.259807621135,0.257401995014,0.254996368892,0.25259074277,0.250185116649,0.247779490527,0.245373864406,0.242968238284,0.240562612162,0.238156986041,0.235751359919,0.233345733797,0.230940107676,0.228534481554,0.226128855433,0.223723229311,0.221317603189,0.218911977068,0.216506350946,0.214100724824,0.211695098703,0.209289472581,0.20688384646,0.204478220338,0.202072594216,0.199666968095,0.197261341973,0.194855715851,0.19245008973,0.190044463608,0.187638837487,0.185233211365,0.182827585243,0.180421959122,0.178016333,0.175610706879,0.173205080757,0.170799454635,0.168393828514,0.165988202392,0.16358257627,0.161176950149,0.158771324027,0.156365697906,0.153960071784,0.151554445662,0.149148819541,0.146743193419,0.144337567297,0.141931941176,0.139526315054,0.137120688933,0.134715062811,0.132309436689,0.129903810568,0.127498184446,0.125092558324,0.122686932203,0.120281306081,0.11787567996,0.115470053838,0.113064427716,0.110658801595,0.108253175473,0.105847549351,0.10344192323,0.101036297108,0.098630670987,0.096225044865,0.093819418743,0.091413792622,0.0890081665,0.086602540378,0.084196914257,0.081791288135,0.079385662014,0.076980035892,0.07457440977,0.072168783649,0.069763157527,0.067357531405,0.064951905284,0.062546279162,0.060140653041,0.057735026919,0.055329400797,0.052923774676,0.050518148554,0.048112522432,0.045706896311,0.043301270189,0.040895644068,0.038490017946,0.036084391824,0.033678765703,0.031273139581,0.028867513459,0.026461887338,0.024056261216,0.021650635095,0.019245008973,0.016839382851,0.01443375673,0.012028130608,0.009622504486,0.007216878365,0.004811252243,0.002405626122]
        else:
            obj.external_data = external_data
        if len(internal45_data)==0:
            obj.internal45_data = [-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,0.001388888889,0.002777777778,0.004166666667,0.005555555556,0.006944444444,0.008333333333,0.009722222222,0.011111111111,0.0125,0.013888888889,0.015277777778,0.016666666667,0.018055555556,0.019444444444,0.020833333333,0.022222222222,0.023611111111,0.025,0.026388888889,0.027777777778,0.029166666667,0.030555555556,0.031944444444,0.033333333333,0.034722222222,0.036111111111,0.0375,0.038888888889,0.040277777778,0.041666666667,0.043055555556,0.044444444444,0.045833333333,0.047222222222,0.048611111111,0.05,0.051388888889,0.052777777778,0.054166666667,0.055555555556,0.056944444444,0.058333333333,0.059722222222,0.061111111111,0.0625,0.063888888889,0.065277777778,0.066666666667,0.068055555556,0.069444444444,0.070833333333,0.072222222222,0.073611111111,0.075,0.076388888889,0.077777777778,0.079166666667,0.080555555556,0.081944444444,0.083333333333,0.084722222222,0.086111111111,0.0875,0.088888888889,0.090277777778,0.091666666667,0.093055555556,0.094444444444,0.095833333333,0.097222222222,0.098611111111,0.1,0.101388888889,0.102777777778,0.104166666667,0.105555555556,0.106944444444,0.108333333333,0.109722222222,0.111111111111,0.1125,0.113888888889,0.115277777778,0.116666666667,0.118055555556,0.119444444444,0.120833333333,0.122222222222,0.123611111111,0.125,0.126388888889,0.127777777778,0.129166666667,0.130555555556,0.131944444444,0.133333333333,0.134722222222,0.136111111111,0.1375,0.138888888889,0.140277777778,0.141666666667,0.143055555556,0.144444444444,0.145833333333,0.147222222222,0.148611111111,0.15,0.151388888889,0.152777777778,0.154166666667,0.155555555556,0.156944444444,0.158333333333,0.159722222222,0.161111111111,0.1625,0.163888888889,0.165277777778,0.166666666667,0.168055555556,0.169444444444,0.170833333333,0.172222222222,0.173611111111,0.175,0.176388888889,0.177777777778,0.179166666667,0.180555555556,0.181944444444,0.183333333333,0.184722222222,0.186111111111,0.1875,0.188888888889,0.190277777778,0.191666666667,0.193055555556,0.194444444444,0.195833333333,0.197222222222,0.198611111111,0.2,0.201388888889,0.202777777778,0.204166666667,0.205555555556,0.206944444444,0.208333333333,0.209722222222,0.211111111111,0.2125,0.213888888889,0.215277777778,0.216666666667,0.218055555556,0.219444444444,0.220833333333,0.222222222222,0.223611111111,0.225,0.226388888889,0.227777777778,0.229166666667,0.230555555556,0.231944444444,0.233333333333,0.234722222222,0.236111111111,0.2375,0.238888888889,0.240277777778,0.241666666667,0.243055555556,0.244444444444,0.245833333333,0.247222222222,0.248611111111,0.25,0.251388888889,0.252777777778,0.254166666667,0.255555555556,0.256944444444,0.258333333333,0.259722222222,0.261111111111,0.2625,0.263888888889,0.265277777778,0.266666666667,0.268055555556,0.269444444444,0.270833333333,0.272222222222,0.273611111111,0.275,0.276388888889,0.277777777778,0.279166666667,0.280555555556,0.281944444444,0.283333333333,0.284722222222,0.286111111111,0.2875,0.288888888889,0.290277777778,0.291666666667,0.293055555556,0.294444444444,0.295833333333,0.297222222222,0.298611111111,0.3,0.301388888889,0.302777777778,0.304166666667,0.305555555556,0.306944444444,0.308333333333,0.309722222222,0.311111111111,0.3125,0.313858688514,0.315159467254,0.316405739377,0.317600519576,0.318746492615,0.319846060893,0.320901383434,0.321914408144,0.322886898686,0.323820457033,0.324716542535,0.325576488113,0.326401514108,0.327192740176,0.327951195558,0.32867782799,0.329373511457,0.330039052968,0.330675198508,0.331282638269,0.331862011268,0.33241390944,0.33293888126,0.333437434977,0.333910041483,0.334357136884,0.334779124789,0.335176378369,0.335549242191,0.335898033867,0.336223045529,0.336524545151,0.336802777733,0.337057966357,0.337290313125,0.3375,0.337687189543,0.33785202556,0.337994633675,0.338115121809,0.338213580601,0.338290083752,0.338344688299,0.338377434833,0.338388347648,0.338377434833,0.338344688299,0.338290083752,0.338213580601,0.338115121809,0.337994633675,0.33785202556,0.337687189543,0.3375,0.337290313125,0.337057966357,0.336802777733,0.336524545151,0.336223045529,0.335898033867,0.335549242191,0.335176378369,0.334779124789,0.334357136884,0.333910041483,0.333437434977,0.33293888126,0.33241390944,0.331862011268,0.331282638269,0.330675198508,0.330039052968,0.329373511457,0.32867782799,0.327951195558,0.327192740176,0.326401514108,0.325576488113,0.324716542535,0.323820457033,0.322886898686,0.321914408144,0.320901383434,0.319846060893,0.318746492615,0.317600519576,0.316405739377,0.315159467254,0.313858688514,0.3125,0.311111111111,0.309722222222,0.308333333333,0.306944444444,0.305555555556,0.304166666667,0.302777777778,0.301388888889,0.3,0.298611111111,0.297222222222,0.295833333333,0.294444444444,0.293055555556,0.291666666667,0.290277777778,0.288888888889,0.2875,0.286111111111,0.284722222222,0.283333333333,0.281944444444,0.280555555556,0.279166666667,0.277777777778,0.276388888889,0.275,0.273611111111,0.272222222222,0.270833333333,0.269444444444,0.268055555556,0.266666666667,0.265277777778,0.263888888889,0.2625,0.261111111111,0.259722222222,0.258333333333,0.256944444444,0.255555555556,0.254166666667,0.252777777778,0.251388888889,0.25,0.248611111111,0.247222222222,0.245833333333,0.244444444444,0.243055555556,0.241666666667,0.240277777778,0.238888888889,0.2375,0.236111111111,0.234722222222,0.233333333333,0.231944444444,0.230555555556,0.229166666667,0.227777777778,0.226388888889,0.225,0.223611111111,0.222222222222,0.220833333333,0.219444444444,0.218055555556,0.216666666667,0.215277777778,0.213888888889,0.2125,0.211111111111,0.209722222222,0.208333333333,0.206944444444,0.205555555556,0.204166666667,0.202777777778,0.201388888889,0.2,0.198611111111,0.197222222222,0.195833333333,0.194444444444,0.193055555556,0.191666666667,0.190277777778,0.188888888889,0.1875,0.186111111111,0.184722222222,0.183333333333,0.181944444444,0.180555555556,0.179166666667,0.177777777778,0.176388888889,0.175,0.173611111111,0.172222222222,0.170833333333,0.169444444444,0.168055555556,0.166666666667,0.165277777778,0.163888888889,0.1625,0.161111111111,0.159722222222,0.158333333333,0.156944444444,0.155555555556,0.154166666667,0.152777777778,0.151388888889,0.15,0.148611111111,0.147222222222,0.145833333333,0.144444444444,0.143055555556,0.141666666667,0.140277777778,0.138888888889,0.1375,0.136111111111,0.134722222222,0.133333333333,0.131944444444,0.130555555556,0.129166666667,0.127777777778,0.126388888889,0.125,0.123611111111,0.122222222222,0.120833333333,0.119444444444,0.118055555556,0.116666666667,0.115277777778,0.113888888889,0.1125,0.111111111111,0.109722222222,0.108333333333,0.106944444444,0.105555555556,0.104166666667,0.102777777778,0.101388888889,0.1,0.098611111111,0.097222222222,0.095833333333,0.094444444444,0.093055555556,0.091666666667,0.090277777778,0.088888888889,0.0875,0.086111111111,0.084722222222,0.083333333333,0.081944444444,0.080555555556,0.079166666667,0.077777777778,0.076388888889,0.075,0.073611111111,0.072222222222,0.070833333333,0.069444444444,0.068055555556,0.066666666667,0.065277777778,0.063888888889,0.0625,0.061111111111,0.059722222222,0.058333333333,0.056944444444,0.055555555556,0.054166666667,0.052777777778,0.051388888889,0.05,0.048611111111,0.047222222222,0.045833333333,0.044444444444,0.043055555556,0.041666666667,0.040277777778,0.038888888889,0.0375,0.036111111111,0.034722222222,0.033333333333,0.031944444444,0.030555555556,0.029166666667,0.027777777778,0.026388888889,0.025,0.023611111111,0.022222222222,0.020833333333,0.019444444444,0.018055555556,0.016666666667,0.015277777778,0.013888888889,0.0125,0.011111111111,0.009722222222,0.008333333333,0.006944444444,0.005555555556,0.004166666667,0.002777777778,0.001388888889,]
        else:
            obj.internal45_data = internal45_data
        if len(external45_data)==0:
            obj.external45_data = [-0.001373625452,-0.002717377028,-0.00403218806,-0.005318934508,-0.006578439732,-0.007811478754,-0.009018782081,-0.010201039151,-0.011358901433,-0.01249298523,-0.013603874226,-0.014692121785,-0.015758253053,-0.016802766868,-0.017826137508,-0.018828816289,-0.019811233024,-0.020773797371,-0.021716900067,-0.022640914066,-0.023546195583,-0.02443308507,-0.025301908106,-0.026152976227,-0.026986587696,-0.027803028216,-0.028602571593,-0.029385480351,-0.030152006309,-0.030902391115,-0.031636866748,-0.032355655981,-0.03305897282,-0.033747022914,-0.034420003934,-0.035078105936,-0.035721511693,-0.036350397016,-0.036964931046,-0.037565276538,-0.038151590118,-0.038724022536,-0.039282718898,-0.039827818879,-0.040359456941,-0.04087776252,-0.041382860213,-0.041874869954,-0.042353907175,-0.042820082967,-0.043273504219,-0.043714273767,-0.044142490518,-0.044558249578,-0.044961642368,-0.045352756738,-0.045731677071,-0.046098484383,-0.046453256416,-0.046796067734,-0.047126989799,-0.047446091057,-0.047753437014,-0.048049090302,-0.048333110755,-0.048605555467,-0.048866478854,-0.049115932713,-0.049353966274,-0.04958062625,-0.049795956885,-0.05,-0.050192795035,-0.050374379085,-0.050544786941,-0.050704051121,-0.050852201901,-0.05098926735,-0.051115273347,-0.051230243617,-0.051334199746,-0.051427161202,-0.051509145358,-0.051580167503,-0.051640240861,-0.051689376598,-0.051727583837,-0.051754869666,-0.051771239142,-0.051776695297,-0.051771239142,-0.051754869666,-0.051727583837,-0.051689376598,-0.051640240861,-0.051580167503,-0.051509145358,-0.051427161202,-0.051334199746,-0.051230243617,-0.051115273347,-0.05098926735,-0.050852201901,-0.050704051121,-0.050544786941,-0.050374379085,-0.050192795035,-0.05,-0.049795956885,-0.04958062625,-0.049353966274,-0.049115932713,-0.048866478854,-0.048605555467,-0.048333110755,-0.048049090302,-0.047753437014,-0.047446091057,-0.047126989799,-0.046796067734,-0.046453256416,-0.046098484383,-0.045731677071,-0.045352756738,-0.044961642368,-0.044558249578,-0.044142490518,-0.043714273767,-0.043273504219,-0.042820082967,-0.042353907175,-0.041874869954,-0.041382860213,-0.04087776252,-0.040359456941,-0.039827818879,-0.039282718898,-0.038724022536,-0.038151590118,-0.037565276538,-0.036964931046,-0.036350397016,-0.035721511693,-0.035078105936,-0.034420003934,-0.033747022914,-0.03305897282,-0.032355655981,-0.031636866748,-0.030902391115,-0.030152006309,-0.029385480351,-0.028602571593,-0.027803028216,-0.026986587696,-0.026152976227,-0.025301908106,-0.02443308507,-0.023546195583,-0.022640914066,-0.021716900067,-0.020773797371,-0.019811233024,-0.018828816289,-0.017826137508,-0.016802766868,-0.015758253053,-0.014692121785,-0.013603874226,-0.01249298523,-0.011358901433,-0.010201039151,-0.009018782081,-0.007811478754,-0.006578439732,-0.005318934508,-0.00403218806,-0.002717377028,-0.001373625452,-0.0,0.001388888889,0.002777777778,0.004166666667,0.005555555556,0.006944444445,0.008333333334,0.009722222223,0.011111111112,0.0125,0.013888888889,0.015277777778,0.016666666667,0.018055555556,0.019444444445,0.020833333334,0.022222222223,0.023611111112,0.025,0.026388888889,0.027777777778,0.029166666667,0.030555555556,0.031944444445,0.033333333334,0.034722222223,0.036111111111,0.0375,0.038888888889,0.040277777778,0.041666666667,0.043055555556,0.044444444445,0.045833333334,0.047222222223,0.048611111111,0.05,0.051388888889,0.052777777778,0.054166666667,0.055555555556,0.056944444445,0.058333333334,0.059722222223,0.061111111111,0.0625,0.063888888889,0.065277777778,0.066666666667,0.068055555556,0.069444444445,0.070833333334,0.072222222223,0.073611111111,0.075,0.076388888889,0.077777777778,0.079166666667,0.080555555556,0.081944444445,0.083333333334,0.084722222223,0.086111111111,0.0875,0.088888888889,0.090277777778,0.091666666667,0.093055555556,0.094444444445,0.095833333334,0.097222222223,0.098611111111,0.1,0.101388888889,0.102777777778,0.104166666667,0.105555555556,0.106944444445,0.108333333334,0.109722222222,0.111111111111,0.1125,0.113888888889,0.115277777778,0.116666666667,0.118055555556,0.119444444445,0.120833333334,0.122222222222,0.123611111111,0.125,0.126388888889,0.127777777778,0.129166666667,0.130555555556,0.131944444445,0.133333333334,0.134722222222,0.136111111111,0.1375,0.138888888889,0.140277777778,0.141666666667,0.143055555556,0.144444444445,0.145833333334,0.147222222222,0.148611111111,0.15,0.151388888889,0.152777777778,0.154166666667,0.155555555556,0.156944444445,0.158333333334,0.159722222222,0.161111111111,0.1625,0.163888888889,0.165277777778,0.166666666667,0.168055555556,0.169444444445,0.170833333334,0.172222222222,0.173611111111,0.175,0.176388888889,0.177777777778,0.179166666667,0.180555555556,0.181944444445,0.183333333334,0.184722222222,0.186111111111,0.1875,0.188888888889,0.190277777778,0.191666666667,0.193055555556,0.194444444445,0.195833333333,0.197222222222,0.198611111111,0.2,0.201388888889,0.202777777778,0.204166666667,0.205555555556,0.206944444445,0.208333333333,0.209722222222,0.211111111111,0.2125,0.213888888889,0.215277777778,0.216666666667,0.218055555556,0.219444444445,0.220833333333,0.222222222222,0.223611111111,0.225,0.226388888889,0.227777777778,0.229166666667,0.230555555556,0.231944444445,0.233333333333,0.234722222222,0.236111111111,0.2375,0.238888888889,0.240277777778,0.241666666667,0.243055555556,0.244444444445,0.245833333333,0.247222222222,0.248611111111,0.25,0.251388888889,0.252777777778,0.254166666667,0.255555555556,0.256944444445,0.258333333333,0.259722222222,0.261111111111,0.2625,0.263888888889,0.265277777778,0.266666666667,0.268055555556,0.269444444445,0.270833333333,0.272222222222,0.273611111111,0.275,0.276388888889,0.277777777778,0.279166666667,0.280555555556,0.281944444444,0.283333333333,0.284722222222,0.286111111111,0.2875,0.288888888889,0.290277777778,0.291666666667,0.293055555556,0.294444444444,0.295833333333,0.297222222222,0.298611111111,0.3,0.301388888889,0.302777777778,0.304166666667,0.305555555556,0.306944444444,0.308333333333,0.309722222222,0.311111111111,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.3125,0.311111111111,0.309722222222,0.308333333333,0.306944444444,0.305555555556,0.304166666667,0.302777777778,0.301388888889,0.3,0.298611111111,0.297222222222,0.295833333333,0.294444444444,0.293055555556,0.291666666667,0.290277777778,0.288888888889,0.2875,0.286111111111,0.284722222222,0.283333333333,0.281944444444,0.280555555556,0.279166666667,0.277777777778,0.276388888889,0.275,0.273611111111,0.272222222222,0.270833333333,0.269444444444,0.268055555556,0.266666666667,0.265277777778,0.263888888889,0.2625,0.261111111111,0.259722222222,0.258333333333,0.256944444444,0.255555555556,0.254166666667,0.252777777778,0.251388888889,0.25,0.248611111111,0.247222222222,0.245833333333,0.244444444444,0.243055555555,0.241666666667,0.240277777778,0.238888888889,0.2375,0.236111111111,0.234722222222,0.233333333333,0.231944444444,0.230555555555,0.229166666667,0.227777777778,0.226388888889,0.225,0.223611111111,0.222222222222,0.220833333333,0.219444444444,0.218055555555,0.216666666667,0.215277777778,0.213888888889,0.2125,0.211111111111,0.209722222222,0.208333333333,0.206944444444,0.205555555555,0.204166666667,0.202777777778,0.201388888889,0.2,0.198611111111,0.197222222222,0.195833333333,0.194444444444,0.193055555555,0.191666666667,0.190277777778,0.188888888889,0.1875,0.186111111111,0.184722222222,0.183333333333,0.181944444444,0.180555555555,0.179166666667,0.177777777778,0.176388888889,0.175,0.173611111111,0.172222222222,0.170833333333,0.169444444444,0.168055555555,0.166666666667,0.165277777778,0.163888888889,0.1625,0.161111111111,0.159722222222,0.158333333333,0.156944444444,0.155555555555,0.154166666667,0.152777777778,0.151388888889,0.15,0.148611111111,0.147222222222,0.145833333333,0.144444444444,0.143055555555,0.141666666667,0.140277777778,0.138888888889,0.1375,0.136111111111,0.134722222222,0.133333333333,0.131944444444,0.130555555555,0.129166666667,0.127777777778,0.126388888889,0.125,0.123611111111,0.122222222222,0.120833333333,0.119444444444,0.118055555555,0.116666666667,0.115277777778,0.113888888889,0.1125,0.111111111111,0.109722222222,0.108333333333,0.106944444444,0.105555555555,0.104166666666,0.102777777778,0.101388888889,0.1,0.098611111111,0.097222222222,0.095833333333,0.094444444444,0.093055555555,0.091666666666,0.090277777778,0.088888888889,0.0875,0.086111111111,0.084722222222,0.083333333333,0.081944444444,0.080555555555,0.079166666666,0.077777777778,0.076388888889,0.075,0.073611111111,0.072222222222,0.070833333333,0.069444444444,0.068055555555,0.066666666666,0.065277777778,0.063888888889,0.0625,0.061111111111,0.059722222222,0.058333333333,0.056944444444,0.055555555555,0.054166666666,0.052777777778,0.051388888889,0.05,0.048611111111,0.047222222222,0.045833333333,0.044444444444,0.043055555555,0.041666666666,0.040277777778,0.038888888889,0.0375,0.036111111111,0.034722222222,0.033333333333,0.031944444444,0.030555555555,0.029166666666,0.027777777778,0.026388888889,0.025,0.023611111111,0.022222222222,0.020833333333,0.019444444444,0.018055555555,0.016666666666,0.015277777778,0.013888888889,0.0125,0.011111111111,0.009722222222,0.008333333333,0.006944444444,0.005555555555,0.004166666666,0.002777777778,0.001388888889,]
        else:
            obj.external45_data = external45_data
#2start
        if len(internal2S_data)==0:
            obj.internal2S_data = [-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,0.004811279452,0.009622558905,0.014433838357,0.019245117809,0.024056397261,0.028867676714,0.033678956166,0.038490235618,0.043301515071,0.048112794523,0.052924073975,0.057735353427,0.06254663288,0.067357912332,0.072169191784,0.076980471237,0.081791750689,0.086603030141,0.091414309593,0.096225589046,0.101036868498,0.10584814795,0.110659427403,0.115470706855,0.120281986307,0.12509326576,0.129904545212,0.134715824664,0.139527104116,0.144338383569,0.149149663021,0.153960942473,0.158772221926,0.163583501378,0.16839478083,0.173206060282,0.178017339735,0.182828619187,0.187639898639,0.192451178092,0.197262457544,0.202073736996,0.206885016448,0.211696295901,0.216507575353,0.221318854805,0.226130134258,0.23094141371,0.235752693162,0.240563972614,0.245375252067,0.250186531519,0.254997810971,0.259809090424,0.264620369876,0.269431649328,0.27424292878,0.279054208233,0.283865487685,0.288676767137,0.29348804659,0.298299326042,0.303110605494,0.307921884946,0.312733164399,0.317544443851,0.322355723303,0.327167002756,0.331978282208,0.33678956166,0.341600841113,0.346412120565,0.351223400017,0.356034679469,0.360845958922,0.365657238374,0.370468517826,0.375279797279,0.380091076731,0.384902356183,0.389713635635,0.394524915088,0.39933619454,0.404147473992,0.408958753445,0.413770032897,0.418581312349,0.423392591801,0.428203871254,0.433015150706,0.437826430158,0.442637709611,0.447448989063,0.452260268515,0.457071547967,0.46188282742,0.466694106872,0.471505386324,0.476316665777,0.481127945229,0.485939224681,0.490750504133,0.495561783586,0.500373063038,0.50518434249,0.509995621943,0.514806901395,0.519618180847,0.524429460299,0.529240739752,0.534052019204,0.538863298656,0.543574230063,0.547676454226,0.551248893689,0.554407036112,0.557226361347,0.559759404764,0.562044440121,0.564110326611,0.56597940937,0.567669351749,0.569194344037,0.570565929497,0.571793585533,0.572885142526,0.573847091694,0.574684814962,0.575402758649,0.576004565696,0.576493176578,0.576870905964,0.577139500113,0.577300178463,0.577353661816,0.577300188674,0.577139520581,0.57687093678,0.576493217883,0.576004617684,0.575402821569,0.574684889128,0.573847177489,0.572885240417,0.571793696083,0.570566053385,0.569194482084,0.56766950495,0.565979578942,0.564110514058,0.562044647329,0.55975963414,0.557226616038,0.55440732035,0.5512492134,0.547676818145,0.543574652051,0.53886379862,0.534052600794,0.529241402969,0.524430205143,0.519619007317,0.514807809491,0.509996611665,0.505185413839,0.500374216013,0.495563018188,0.490751820362,0.485940622536,0.48112942471,0.476318226884,0.471507029058,0.466695831232,0.461884633407,0.457073435581,0.452262237755,0.447451039929,0.442639842103,0.437828644277,0.433017446451,0.428206248626,0.4233950508,0.418583852974,0.413772655148,0.408961457322,0.404150259496,0.39933906167,0.394527863845,0.389716666019,0.384905468193,0.380094270367,0.375283072541,0.370471874715,0.365660676889,0.360849479064,0.356038281238,0.351227083412,0.346415885586,0.34160468776,0.336793489934,0.331982292108,0.327171094283,0.322359896457,0.317548698631,0.312737500805,0.307926302979,0.303115105153,0.298303907327,0.293492709502,0.288681511676,0.28387031385,0.279059116024,0.274247918198,0.269436720372,0.264625522546,0.259814324721,0.255003126895,0.250191929069,0.245380731243,0.240569533417,0.235758335591,0.230947137765,0.22613593994,0.221324742114,0.216513544288,0.211702346462,0.206891148636,0.20207995081,0.197268752985,0.192457555159,0.187646357333,0.182835159507,0.178023961681,0.173212763855,0.168401566029,0.163590368204,0.158779170378,0.153967972552,0.149156774726,0.1443455769,0.139534379074,0.134723181248,0.129911983423,0.125100785597,0.120289587771,0.115478389945,0.110667192119,0.105855994293,0.101044796467,0.096233598642,0.091422400816,0.08661120299,0.081800005164,0.076988807338,0.072177609512,0.067366411686,0.062555213861,0.057744016035,0.052932818209,0.048121620383,0.043310422557,0.038499224731,0.033688026905,0.02887682908,0.024065631254,0.019254433428,0.014443235602,0.009632037776,0.00482083995,9.642124e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,2.754918e-06,]
        else:
            obj.internal2S_data = internal2S_data
        if len(external2S_data)==0:
            obj.external2S_data = [-0.004610509437,-0.008864261505,-0.01281484414,-0.016502787814,-0.019959638539,-0.023210526211,-0.026275857144,-0.029172470647,-0.031914453753,-0.034513730164,-0.036980495571,-0.039323545713,-0.041550527849,-0.043668136434,-0.045682267448,-0.04759814157,-0.049420403565,-0.051153203265,-0.052800262124,-0.054364928386,-0.055850223123,-0.057258878931,-0.058593372644,-0.059855953149,-0.06104866515,-0.06217336957,-0.063231761131,-0.064225383563,-0.0651556428,-0.066023818454,-0.066831073828,-0.067578464649,-0.068266946707,-0.068897382525,-0.069470547196,-0.069987133462,-0.070447756139,-0.070852955945,-0.07120320279,-0.071498898583,-0.071740379589,-0.071927918371,-0.072061725347,-0.072141949981,-0.072168681616,-0.072141949981,-0.072061725347,-0.071927918371,-0.071740379589,-0.071498898583,-0.07120320279,-0.070852955945,-0.070447756139,-0.069987133462,-0.069470547196,-0.068897382525,-0.068266946707,-0.067578464649,-0.066831073828,-0.066023818454,-0.0651556428,-0.064225383563,-0.06323176113,-0.062173369569,-0.06104866515,-0.059855953149,-0.058593372644,-0.057258878931,-0.055850223122,-0.054364928385,-0.052800262123,-0.051153203264,-0.049420403565,-0.047598141569,-0.045682267447,-0.043668136433,-0.041550527848,-0.039323545712,-0.03698049557,-0.034513730163,-0.031914453752,-0.029172470646,-0.026275857143,-0.02321052621,-0.019959638538,-0.016502787813,-0.012814844138,-0.008864261504,-0.004610509435,-0.0,0.004811279455,0.009622558907,0.01443383836,0.019245117812,0.024056397264,0.028867676716,0.033678956169,0.038490235621,0.043301515073,0.048112794525,0.052924073978,0.05773535343,0.062546632882,0.067357912334,0.072169191787,0.076980471239,0.081791750691,0.086603030143,0.091414309596,0.096225589048,0.1010368685,0.105848147952,0.110659427405,0.115470706857,0.120281986309,0.125093265761,0.129904545214,0.134715824666,0.139527104118,0.14433838357,0.149149663023,0.153960942475,0.158772221927,0.163583501379,0.168394780832,0.173206060284,0.178017339736,0.182828619188,0.187639898641,0.192451178093,0.197262457545,0.202073736997,0.20688501645,0.211696295902,0.216507575354,0.221318854806,0.226130134259,0.230941413711,0.235752693163,0.240563972615,0.245375252068,0.25018653152,0.254997810972,0.259809090424,0.264620369877,0.269431649329,0.274242928781,0.279054208233,0.283865487686,0.288676767138,0.29348804659,0.298299326042,0.303110605495,0.307921884947,0.312733164399,0.317544443851,0.322355723304,0.327167002756,0.331978282208,0.33678956166,0.341600841113,0.346412120565,0.351223400017,0.356034679469,0.360845958922,0.365657238374,0.370468517826,0.375279797278,0.380091076731,0.384902356183,0.389713635635,0.394524915087,0.39933619454,0.404147473992,0.408958753444,0.413770032896,0.418581312349,0.423392591801,0.428203871253,0.433015150705,0.437826430158,0.44263770961,0.447448989062,0.452260268514,0.457071547967,0.461882827419,0.466694106871,0.471505386323,0.476316665776,0.481127945228,0.48593922468,0.490750504132,0.495561783585,0.500373063037,0.505184342489,0.509995621941,0.514806901394,0.519618180846,0.524429460298,0.52924073975,0.534052019203,0.538863298655,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.541268938381,0.538863339468,0.534052141642,0.529240943817,0.524429745991,0.519618548165,0.514807350339,0.509996152514,0.505184954688,0.500373756862,0.495562559037,0.490751361211,0.485940163385,0.481128965559,0.476317767734,0.471506569908,0.466695372082,0.461884174257,0.457072976431,0.452261778605,0.447450580779,0.442639382954,0.437828185128,0.433016987302,0.428205789477,0.423394591651,0.418583393825,0.413772195999,0.408960998174,0.404149800348,0.399338602522,0.394527404696,0.389716206871,0.384905009045,0.380093811219,0.375282613394,0.370471415568,0.365660217742,0.360849019916,0.356037822091,0.351226624265,0.346415426439,0.341604228614,0.336793030788,0.331981832962,0.327170635136,0.322359437311,0.317548239485,0.312737041659,0.307925843833,0.303114646008,0.298303448182,0.293492250356,0.288681052531,0.283869854705,0.279058656879,0.274247459053,0.269436261228,0.264625063402,0.259813865576,0.255002667751,0.250191469925,0.245380272099,0.240569074273,0.235757876448,0.230946678622,0.226135480796,0.22132428297,0.216513085145,0.211701887319,0.206890689493,0.202079491668,0.197268293842,0.192457096016,0.18764589819,0.182834700365,0.178023502539,0.173212304713,0.168401106888,0.163589909062,0.158778711236,0.15396751341,0.149156315585,0.144345117759,0.139533919933,0.134722722108,0.129911524282,0.125100326456,0.12028912863,0.115477930805,0.110666732979,0.105855535153,0.101044337327,0.096233139502,0.091421941676,0.08661074385,0.081799546025,0.076988348199,0.072177150373,0.067365952547,0.062554754722,0.057743556896,0.05293235907,0.048121161245,0.043309963419,0.038498765593,0.033687567767,0.028876369942,0.024065172116,0.01925397429,0.014442776464,0.009631578639,0.004820380813,9.182987e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,2.295753e-06,]
        else:
            obj.external2S_data = external2S_data
#3start
        if len(internal3S_data)==0:
            obj.internal3S_data = [-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,0.007216878365,0.01443375673,0.021650635095,0.028867513459,0.036084391824,0.043301270189,0.050518148554,0.057735026919,0.064951905284,0.072168783649,0.079385662014,0.086602540378,0.093819418743,0.101036297108,0.108253175473,0.115470053838,0.122686932203,0.129903810568,0.137120688933,0.144337567297,0.151554445662,0.158771324027,0.165988202392,0.173205080757,0.180421959122,0.187638837487,0.194855715851,0.202072594216,0.209289472581,0.216506350946,0.223723229311,0.230940107676,0.238156986041,0.245373864406,0.25259074277,0.259807621135,0.2670244995,0.274241377865,0.28145825623,0.288675134595,0.29589201296,0.303108891325,0.310325769689,0.317542648054,0.324759526419,0.331976404784,0.339193283149,0.346410161514,0.353627039879,0.360843918243,0.368060796608,0.375277674973,0.382494553338,0.389711431703,0.396928310068,0.404145188433,0.411362066798,0.418578945162,0.425795823527,0.433012701892,0.440229580257,0.447446458622,0.454663336987,0.461880215352,0.469097093717,0.476313972081,0.483530850446,0.490747728811,0.497964607176,0.505181485541,0.512398363906,0.519615242271,0.526832120636,0.534048999,0.541265877365,0.547673314821,0.5528711653,0.557223135528,0.560927686209,0.56410705064,0.56684252132,0.56919103344,0.571193900198,0.57288180558,0.57427783534,0.575399400317,0.576259494329,0.576867529433,0.577229887482,0.57735026919,0.577229887482,0.576867529433,0.576259494329,0.575399400317,0.57427783534,0.57288180558,0.571193900198,0.56919103344,0.56684252132,0.56410705064,0.560927686209,0.557223135528,0.5528711653,0.547673314821,0.541265877365,0.534048999001,0.526832120636,0.519615242271,0.512398363906,0.505181485541,0.497964607176,0.490747728811,0.483530850447,0.476313972082,0.469097093717,0.461880215352,0.454663336987,0.447446458622,0.440229580257,0.433012701892,0.425795823528,0.418578945163,0.411362066798,0.404145188433,0.396928310068,0.389711431703,0.382494553338,0.375277674973,0.368060796609,0.360843918244,0.353627039879,0.346410161514,0.339193283149,0.331976404784,0.324759526419,0.317542648055,0.31032576969,0.303108891325,0.29589201296,0.288675134595,0.28145825623,0.274241377865,0.2670244995,0.259807621136,0.252590742771,0.245373864406,0.238156986041,0.230940107676,0.223723229311,0.216506350946,0.209289472581,0.202072594217,0.194855715852,0.187638837487,0.180421959122,0.173205080757,0.165988202392,0.158771324027,0.151554445663,0.144337567298,0.137120688933,0.129903810568,0.122686932203,0.115470053838,0.108253175473,0.101036297108,0.093819418744,0.086602540379,0.079385662014,0.072168783649,0.064951905284,0.057735026919,0.050518148554,0.043301270189,0.036084391825,0.02886751346,0.021650635095,0.01443375673,0.007216878365,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,]
        else:
            obj.internal3S_data = internal3S_data
        if len(external3S_data)==0:
            obj.external3S_data = [-0.006778280188,-0.012814874909,-0.018258443075,-0.023210575868,-0.027744373085,-0.031914516323,-0.035763165074,-0.039323617685,-0.042622693966,-0.045682346547,-0.048520785999,-0.051153287908,-0.05359278529,-0.055850312148,-0.057935341316,-0.059856045664,-0.061619502667,-0.063231856427,-0.06469844723,-0.066023915948,-0.067212288714,-0.068267045903,-0.069191178464,-0.069987233927,-0.070657353858,-0.071203304134,-0.071626499073,-0.071928020232,-0.07210863046,-0.072168783647,-0.07210863046,-0.071928020232,-0.071626499073,-0.071203304134,-0.070657353858,-0.069987233927,-0.069191178464,-0.068267045903,-0.067212288714,-0.066023915948,-0.06469844723,-0.063231856427,-0.061619502667,-0.059856045664,-0.057935341316,-0.055850312148,-0.05359278529,-0.051153287908,-0.048520785999,-0.045682346547,-0.042622693966,-0.039323617685,-0.035763165074,-0.031914516323,-0.027744373085,-0.023210575868,-0.018258443075,-0.012814874909,-0.006778280188,-1e-12,0.007216878368,0.014433756733,0.021650635097,0.028867513462,0.036084391827,0.043301270192,0.050518148557,0.057735026922,0.064951905286,0.072168783651,0.079385662016,0.086602540381,0.093819418746,0.101036297111,0.108253175475,0.11547005384,0.122686932205,0.12990381057,0.137120688935,0.1443375673,0.151554445664,0.158771324029,0.165988202394,0.173205080759,0.180421959124,0.187638837489,0.194855715853,0.202072594218,0.209289472583,0.216506350948,0.223723229313,0.230940107678,0.238156986042,0.245373864407,0.252590742772,0.259807621137,0.267024499502,0.274241377867,0.281458256231,0.288675134596,0.295892012961,0.303108891326,0.310325769691,0.317542648056,0.32475952642,0.331976404785,0.33919328315,0.346410161515,0.35362703988,0.360843918245,0.368060796609,0.375277674974,0.382494553339,0.389711431704,0.396928310069,0.404145188433,0.411362066798,0.418578945163,0.425795823528,0.433012701893,0.440229580258,0.447446458622,0.454663336987,0.461880215352,0.469097093717,0.476313972082,0.483530850447,0.490747728811,0.497964607176,0.505181485541,0.512398363906,0.519615242271,0.526832120636,0.534048999,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.541265877365,0.534048999,0.526832120636,0.519615242271,0.512398363906,0.505181485541,0.497964607176,0.490747728811,0.483530850446,0.476313972081,0.469097093717,0.461880215352,0.454663336987,0.447446458622,0.440229580257,0.433012701892,0.425795823527,0.418578945162,0.411362066798,0.404145188433,0.396928310068,0.389711431703,0.382494553338,0.375277674973,0.368060796608,0.360843918244,0.353627039879,0.346410161514,0.339193283149,0.331976404784,0.324759526419,0.317542648054,0.310325769689,0.303108891325,0.29589201296,0.288675134595,0.28145825623,0.274241377865,0.2670244995,0.259807621135,0.25259074277,0.245373864406,0.238156986041,0.230940107676,0.223723229311,0.216506350946,0.209289472581,0.202072594216,0.194855715851,0.187638837487,0.180421959122,0.173205080757,0.165988202392,0.158771324027,0.151554445662,0.144337567297,0.137120688933,0.129903810568,0.122686932203,0.115470053838,0.108253175473,0.101036297108,0.093819418743,0.086602540378,0.079385662014,0.072168783649,0.064951905284,0.057735026919,0.050518148554,0.043301270189,0.036084391824,0.028867513459,0.021650635095,0.01443375673,0.007216878365,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,-0.0,]
        else:
            obj.external3S_data = external3S_data


        obj.Pitch = pitch #default pitch
        obj.MinorDiameter = minor_diameter #M6x1 internal 6g tolerance class is default

        if len (presets) == 0:
            tmp_presets_data=[
            ['V Thread Presets',0,0,0],
            ['Garden Hose NHR',0.08696*25.4,0.9495*25.4,0.9720*25.4],
            ['M1 Coarse',0.25,0.693,0.729],
            ['M1.1 Coarse',0.25,0.793,0.829],
            ['M1.2 Coarse',0.25,0.893,0.929],
            ['M1.4 Coarse',0.30,1.032,1.075],
            ['M1.6 Coarse',0.35,1.171,1.221],
            ['M1.8 Coarse',0.35,1.371,1.421],
            ['M2 Coarse',0.40,1.509,1.567],
            ['M2.2 Coarse',0.45,1.648,1.713],
            ['M2.5 Coarse',0.45,1.948,2.013],
            ['M3 Coarse',0.50,2.387,2.459],
            ['M3.5 Coarse',0.60,2.764,2.850],
            ['M4 Coarse',0.70,3.141,3.242],
            ['M4.5 Coarse',0.75,3.580,3.688],
            ['M5 Coarse',0.80,4.019,4.134],
            ['M6 Coarse',1.00,4.773,4.917],
            ['M7 Coarse',1.00,5.773,5.917],
            ['M8 Coarse',1.25,6.466,6.647],
            ['M9 Coarse',1.25,7.466,7.647],
            ['M10 Coarse',1.50,8.160,8.376],
            ['M11 Coarse',1.50,9.160,9.376],
            ['M12 Coarse',1.75,9.853,10.106],
            ['M14 Coarse',2.00,11.546,11.835],
            ['M16 Coarse',2.00,13.546,13.835],
            ['M18 Coarse',2.50,14.933,15.394],
            ['M20 Coarse',2.50,16.933,17.294],
            ['M22 Coarse',2.50,18.933,19.294],
            ['M24 Coarse',3.00,20.319,20.752],
            ['M27 Coarse',3.00,23.319,23.752],
            ['M30 Coarse',3.50,25.706,26.211],
            ['M33 Coarse',3.50,28.706,29.211],
            ['M36 Coarse',4.00,31.093,31.670],
            ['M39 Coarse',4.00,34.093,34.670],
            ['M42 Coarse',4.50,36.479,37.129],
            ['M45 Coarse',4.50,39.479,40.129],
            ['M48 Coarse',5.00,41.866,42.857],
            ['M52 Coarse',5.00,45.866,46.587],
            ['M56 Coarse',5.50,49.252,50.046],
            ['M60 Coarse',5.50,53.252,54.046],
            ['M64 Coarse',6.00,56.639,57.505],
            ['M68 Coarse',6.00,60.639,61.505],
            ['M1 Fine',0.20,0.755,0.783],
            ['M1.1 Fine',0.20,0.855,0.883],
            ['M1.2 Fine',0.20,0.955,0.983],
            ['M1.4 Fine',0.20,1.155,1.183],
            ['M1.6 Fine',0.20,1.355,1.383],
            ['M1.8 Fine',0.20,1.555,1.583],
            ['M2 Fine',0.25,1.693,1.729],
            ['M2.2 Fine',0.25,1.893,1.929],
            ['M2.5 Fine',0.35,2.071,2.121],
            ['M3 Fine',0.35,2.571,2.621],
            ['M3.5 Fine',0.35,3.071,3.121],
            ['M4 Fine',0.50,3.387,3.459],
            ['M4.5 Fine',0.50,3.887,3.959],
            ['M5 Fine',0.50,4.387,4.459],
            ['M5.5 Fine',0.50,4.887,4.959],
            ['M6 Fine',0.75,5.080,5.188],
            ['M7 Fine',0.75,6.080,6.188],
            ['M8 Fine',0.75,7.080,7.188],
            ['M8 Fine',1.00,6.773,6.917],
            ['M9 Fine',0.75,8.080,8.188],
            ['M9 Fine',1.00,7.773,7.917],
            ['M10 Fine',0.75,9.080,9.188],
            ['M10 Fine',1.00,8.773,8.917],
            ['M10 Fine',1.25,8.466,8.647],
            ['M11 Fine',0.75,10.080,10.188],
            ['M11 Fine',1.00,9.773,9.917],
            ['M12 Fine',1.00,10.773,10.917],
            ['M12 Fine',1.25,10.466,10.647],
            ['M12 Fine',1.50,10.160,10.376],
            ['M14 Fine',1.00,12.773,12.917],
            ['M14 Fine',1.25,12.466,12.647],
            ['M14 Fine',1.50,12.160,12.376],
            ['M15 Fine',1.00,13.773,13.917],
            ['M15 Fine',1.50,13.160,13.376],
            ['M16 Fine',1.00,14.773,14.917],
            ['M16 Fine',1.50,14.160,14.376],
            ['M17 Fine',1.00,15.773,15.917],
            ['M17 Fine',1.50,15.160,15.376],
            ['M18 Fine',1.00,16.773,16.917],
            ['M18 Fine',1.50,16.160,16.376],
            ['M18 Fine',2.00,15.546,15.835],
            ['M20 Fine',1.00,18.773,18.917],
            ['M20 Fine',1.50,18.160,18.376],
            ['M20 Fine',2.00,17.546,17.835],
            ['M22 Fine',1.00,20.773,20.917],
            ['M22 Fine',1.50,20.160,20.376],
            ['M22 Fine',2.00,19.546,19.835],
            ['M24 Fine',1.00,22.773,22.917],
            ['M24 Fine',1.50,22.160,22.376],
            ['M24 Fine',2.00,21.546,21.835],
            ['M25 Fine',1.00,23.773,23.917],
            ['M25 Fine',1.50,23.160,23.376],
            ['M25 Fine',2.00,22.546,22.835],
            ['M27 Fine',1.00,25.773,25.917],
            ['M27 Fine',1.50,25.160,25.376],
            ['M27 Fine',2.00,24.546,24.835],
            ['M28 Fine',1.00,26.773,26.917],
            ['M28 Fine',1.50,26.160,26.376],
            ['M28 Fine',2.00,25.546,25.835],
            ['M30 Fine',1.00,28.773,28.917],
            ['M30 Fine',1.50,28.160,28.376],
            ['M30 Fine',2.00,27.546,27.835],
            ['M30 Fine',3.00,26.319,26.752],
            ['M32 Fine',1.50,30.160,30.376],
            ['M32 Fine',2.00,29.546,29.835],
            ['M33 Fine',1.50,31.160,31.376],
            ['M33 Fine',2.00,30.546,30.835],
            ['M33 Fine',3.00,29.319,29.752],
            ['M35 Fine',1.50,33.160,33.376],
            ['M35 Fine',2.00,32.546,32.835],
            ['M36 Fine',1.50,34.160,34.376],
            ['M36 Fine',2.00,33.546,33.835],
            ['M36 Fine',3.00,32.319,32.752],
            ['M39 Fine',1.50,37.160,37.376],
            ['M39 Fine',2.00,36.546,36.835],
            ['M39 Fine',3.00,35.319,35.752],
            ['M40 Fine',1.50,38.160,38.376],
            ['M40 Fine',2.00,37.546,37.835],
            ['M40 Fine',3.00,36.619,36.752],
            ['M42 Fine',1.50,40.160,40.376],
            ['M42 Fine',2.00,39.546,39.835],
            ['M42 Fine',3.00,38.319,38.752],
            ['M42 Fine',4.00,37.093,37.670],
            ['M45 Fine',1.50,43.160,43.376],
            ['M45 Fine',2.00,42.546,42.835],
            ['M45 Fine',3.00,41.319,41.752],
            ['M45 Fine',4.00,40.093,40.670],
            ['M48 Fine',1.50,46.160,46.376],
            ['M48 Fine',2.00,45.546,45.835],
            ['M48 Fine',3.00,44.319,44.752],
            ['M48 Fine',4.00,43.093,43.670],
            ['M50 Fine',1.50,48.160,48.376],
            ['M50 Fine',2.00,47.546,47.835],
            ['M50 Fine',3.00,46.319,46.752],
            ['M52 Fine',1.50,50.160,50.376],
            ['M52 Fine',2.00,49.546,49.835],
            ['M52 Fine',3.00,48.319,48.752],
            ['M52 Fine',4.00,47.093,47.670],
            ['M55 Fine',1.50,53.160,53.376],
            ['M55 Fine',2.00,52.546,52.835],
            ['M55 Fine',3.00,51.319,51.752],
            ['M55 Fine',4.00,50.093,50.670],
            ['M56 Fine',1.50,54.160,54.376],
            ['M56 Fine',2.00,43.546,53.835],
            ['M56 Fine',3.00,52.319,52.752],
            ['M56 Fine',4.00,51.903,51.670],
            ['M58 Fine',1.50,56.160,56.376],
            ['M58 Fine',2.00,55.546,55.835],
            ['M58 Fine',3.00,54.319,54.752],
            ['M58 Fine',4.00,53.093,53.670],
            ['M60 Fine',1.50,58.160,58.376],
            ['M60 Fine',2.00,57.546,57.835],
            ['M60 Fine',3.00,56.319,56.752],
            ['M60 Fine',4.00,55.093,55.670],
            ['M62 Fine',1.50,60.160,60.376],
            ['M62 Fine',2.00,59.546,59.835],
            ['M62 Fine',3.00,58.319,58.752],
            ['M62 Fine',4.00,57.093,57.670],
            ['M64 Fine',1.50,62.160,62.376],
            ['M64 Fine',2.00,61.546,61.835],
            ['M64 Fine',3.00,60.319,60.752],
            ['M64 Fine',4.00,59.093,59.670],
            ['M65 Fine',1.50,63.160,63.376],
            ['M65 Fine',2.00,62.546,62.835],
            ['M65 Fine',3.00,61.319,61.752],
            ['M65 Fine',4.00,60.093,60.670],
            ['M68 Fine',1.50,66.160,66.376],
            ['M68 Fine',2.00,65.546,65.835],
            ['M68 Fine',3.00,64.319,64.752],
            ['M68 Fine',4.00,63.093,63.670],
            ['M70 Fine',1.50,68.160,68.376],
            ['M70 Fine',2.00,67.546,67.835],
            ['M70 Fine',3.00,66.319,66.752],
            ['M70 Fine',4.00,65.093,65.670],
            ['M70 Fine',6.00,62.639,63.505],
            ['M72 Fine',1.50,70.160,70.376],
            ['M72 Fine',2.00,69.546,69.835],
            ['M72 Fine',3.00,68.319,68.752],
            ['M72 Fine',4.00,67.093,67.670],
            ['M72 Fine',6.00,64.639,65.505],
            ['M75 Fine',1.50,73.160,73.376],
            ['M75 Fine',2.00,72.546,72.835],
            ['M75 Fine',3.00,71.319,71.752],
            ['M75 Fine',4.00,70.093,70.670],
            ['M75 Fine',6.00,67.639,68.505],
            ['M76 Fine',1.50,74.160,74.376],
            ['M76 Fine',2.00,73.546,73.835],
            ['M76 Fine',3.00,72.319,72.752],
            ['M76 Fine',4.00,71.093,71.670],
            ['M76 Fine',6.00,68.639,69.505],
            ['M80 Fine',1.50,78.160,78.376],
            ['M80 Fine',2.00,77.546,77.835],
            ['M80 Fine',3.00,76.319,76.752],
            ['M80 Fine',4.00,75.093,75.670],
            ['M80 Fine',6.00,72.639,73.505],
            ['M85 Fine',2.00,82.546,82.535],
            ['M85 Fine',3.00,81.319,81.752],
            ['M85 Fine',4.00,80.093,80.670],
            ['M85 Fine',6.00,77.639,78.505],
            ['M90 Fine',2.00,87.546,87.835],
            ['M90 Fine',3.00,86.319,86.752],
            ['M90 Fine',4.00,85.093,85.670],
            ['M90 Fine',6.00,82.639,83.505],
            ['M95 Fine',2.00,92.546,92.835],
            ['M95 Fine',3.00,91.319,91.752],
            ['M95 Fine',4.00,90.093,90.670],
            ['M95 Fine',6.00,87.639,88.505],
            ['M100 Fine',2.00,97.546,97.835],
            ['M100 Fine',3.00,96.319,96.752],
            ['M100 Fine',4.00,95.093,95.670],
            ['M100 Fine',6.00,92.639,93.505],
            ['1/4 in-20 UNC',25.4*0.0500,25.4*0.1887,25.4*0.1959],
            ['5/16 in-18 UNC UNC',25.4*0.0556,25.4*0.2443,25.4*0.2524],
            ['3/8 in-16 UNC UNC',25.4*0.0625,25.4*0.2983,25.4*0.3073],
            ['7/16 in-14 UNC',25.4*0.0714,25.4*0.3499,25.4*0.3602],
            ['1/2 in-13 UNC',25.4*0.0769,25.4*0.4056,25.4*0.4167],
            ['9/16 in-12 UNC',25.4*0.0833,25.4*0.4603,25.4*0.4723],
            ['5/8 in-11 UNC',25.4*0.0909,25.4*0.5135,25.4*0.5266],
            ['3/4 in-10 UNC',25.4*0.1000,25.4*0.6273,25.4*0.6417],
            ['7/8 in-9 UNC',25.4*0.1111,25.4*0.7387,25.4*0.7547],
            ['1 in-8 UNC',25.4*0.1250,25.4*0.8466,25.4*0.8647],
            ['1 1/8 in-7 UNC',25.4*0.1429,25.4*0.9497,25.4*0.9704],
            ['1 1/4 in-7 UNC',25.4*0.1429,25.4*1.0747,25.4*1.0954],
            ['1 3/8 in-6 UNC',25.4*0.1667,25.4*1.1705,25.4*1.1946],
            ['1 1/2 in-6 UNC',25.4*0.1667,25.4*1.2955,25.4*1.3196],
            ['1 3/4 in-5 UNC',25.4*0.2000,25.4*1.5046,25.4*1.5335],
            ['2 in-4 1/2 UNC',25.4*0.2222,25.4*1.7274,25.4*1.7594],
            ['2 1/4 in-4 1/2 UNC',25.4*0.2222,25.4*1.9774,25.4*2.0094],
            ['2-1/2 in-4 UNC',25.4*0.2500,25.4*2.1992,25.4*2.229 ],
            ['2-3/4 in-4 UNC',25.4*0.2500,25.4*2.4491,25.4*2.479],
            ['3 in-4 UNC',25.4*0.2500,25.4*2.699,25.4*2.729],
            ['3-1/4 in-4 UNC',25.4*0.2500,25.4*2.949,25.4*2.979],
            ['3-1/2 in-4 UNC',25.4*0.2500,25.4*3.199,25.4*3.229 ],
            ['3-3/4 in-4 UNC',25.4*0.2500,25.4*3.4489,25.4*3.479 ],
            ['4 in-4 UNC',25.4*0.2500,25.4*3.6989,25.4*3.729],
            ['1/4 in-28 UNF UNF',25.4*0.0357,25.4*0.2062,25.4*0.2113],
            ['5/16 in-24 UNF',25.4*0.0417,25.4*0.2614,25.4*0.2674],
            ['3/8 in-24 UNF',25.4*0.0417,25.4*0.3239,25.4*0.3299],
            ['7/16 in-20 UNF',25.4*0.0500,25.4*0.3762,25.4*0.3834],
            ['1/2 in-20 UNF',25.4*0.0500,25.4*0.4387,25.4*0.4459],
            ['9/16 in-18 UNF',25.4*0.0556,25.4*0.4943,25.4*0.5024],
            ['5/8 in-18 UNF',25.4*0.0556,25.4*0.5568,25.4*0.5649],
            ['3/4 in-16 UNF',25.4*0.0625,25.4*0.6733,25.4*0.6823],
            ['7/8 in-14 UNF',25.4*0.0714,25.4*0.7874,25.4*0.7977],
            ['1 in-12 UNF',25.4*0.0714,25.4*0.8978,25.4*0.9098],
            ['1 in-14 UNF',25.4*0.0714,25.4*0.9132,25.4*0.923],
            ['1 1/8 in-12 UNF',25.4*0.0833,25.4*1.0228,25.4*1.0348],
            ['1 1/4 in-12 UNF',25.4*0.0833,25.4*1.1478,25.4*1.1598],
            ['1 3/8 in-12 UNF',25.4*0.0833,25.4*1.2728,25.4*1.2848],
            ['1 1/2 in-12 UNF',25.4*0.0833,25.4*1.3978,25.4*1.4098]]
        else:
            tmp_presets_data = presets
        tmp=[]
        for ii in range(0,len(tmp_presets_data)):
            tmp.extend(tmp_presets_data[ii][1:]) #strip out string, only include pitch and both minor diameters
        obj.presets_data = tmp
        preset_names=[]
        for td in tmp_presets_data:
            preset_name = td[0]
            if "M" in preset_name:
                preset_name += " " + str(td[1])
            preset_names.append(preset_name)
        obj.Presets = preset_names
        obj.preset_names = preset_names
        obj.InternalOrExternal = internal_or_external
        obj.ThreadCount = thread_count

        if FreeCAD.GuiUp:
            _ViewProviderWire(obj.ViewObject)
            formatObject(obj)
            select(obj)
            body=FreeCADGui.ActiveDocument.ActiveView.getActiveObject("pdbody")
            part=FreeCADGui.ActiveDocument.ActiveView.getActiveObject("part")
            if body:
                body.Group=body.Group+[obj]
            elif part:
                part.Group=part.Group+[obj]
        FreeCAD.ActiveDocument.recompute()
        return obj

#Gui.addCommand("ThreadProfileCreateObject", ThreadProfileCreateObjectCommandClass())

####################################################################################
# Create the buttress thread profile object

class ThreadProfileCreateButtressObjectCommandClass(ThreadProfileCreateObjectCommandClass):
    """Create Object command"""

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreateButtressObject.svg') ,
            'MenuText': "&Create Buttress thread profile" ,
            'ToolTip' : "Create the 45 / 7 degree buttress thread ThreadProfile object"}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        doc.openTransaction("Create Buttress ThreadProfile")
        try:
            self.makeButtressThreadProfile()
        except Exception as e:
            FreeCAD.Console.PrintError(
    	        "ThreadProfile Error: Exception creating thread profile object.\n\n" +
    	        '\n'.join(traceback.format_exception(e)) + "\n"
            )
            QtGui.QApplication.restoreOverrideCursor()
        doc.commitTransaction()
        doc.recompute()
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        return True

    def getHelp(self):
        return ["Created with ThreadProfile (v"+str(version)+") workbench.",
                "This is a thread profile object built",
                "for sweeping along a helix in either the",
                "Part or Part Design workbench."
                "installation of the ThreadProfile workbench is required.",
]
    def makeButtressThreadProfile(self):

        def cd(txt, tpi, nominal): #cd = calculate diameters
            pitch = 25.4/tpi
            length_of_engagement = 10 * pitch #10 * pitch, longer engagements should have more tolerance
            nom = nominal * 25.4
            minor = nom - 0.66271 * pitch
            tolerance = 0.002 * (nom)**(1/3) + .00278 * length_of_engagement**(1/2) + 0.00854 * pitch**(1/2)
            return[txt, pitch, minor - tolerance, minor + tolerance]
        buttress_presets_data = [
            ["Buttress presets",0,0,0], #just fillers, not used
            cd("1/2-12",12,1/2),cd("1/2-16",16,1/2),cd("1/2-20",20,1/2),
            cd("5/8-12",12,5/8),cd("5/8-16",16,5/8),cd("5/8-20",20,5/8),
            cd("3/4-12",12,3/4),cd("3/4-16",16,3/4),cd("3/4-20",20,3/4),
            cd("7/8-10",10,7/8),cd("7/8-12",12,7/8),cd("7/8-16",16,7/8),
            cd("1-10",10,1),cd("1-12",12,1),cd("1-16",16,1),
            cd("1 1/4-8",8,1.25),cd("1 1/4-10",10,1.25),cd("1 1/4-12",12,1.25),
            cd("1 3/8-8",8,1.25),cd("1 3/8-10",10,1.375),cd("1 3/8-12",12,1.375),
            cd("1 1/2-8",8,1.5),cd("1 1/2-10",10,1.5),cd("1 1/2-12",12,1.5),
            cd("1 3/4-6",6,1+3/4),cd("1 3/4-6",8,1+3/4),cd("1 3/4-10",10,1+3/4),
            cd("2-6",6,2),cd("2-8",8,2),cd("2-10",10,2),
            cd("2 1/4-6",6,2+1/4),cd("2 1/4-8",8,2+1/4),cd("2 1/4-10",10,2+1/4),
            cd("2 1/2-6",6,2+1/2),cd("2 1/2-8",8,2+1/2),cd("2 1/2-10",10,2+1/2),
            cd("2 3/4-5",5,2+3/4),cd("2 3/4-6",6,2+3/4),cd("2 3/4-8",8,2+3/4),
            cd("3-5",5,3),cd("3-6",6,3),cd("3-8",8,3),
            cd("3 1/2-5",5,3+1/2),cd("3 1/2-6",6,3+1/2),cd("3 1/2-8",8,3+1/2),
            cd("4-5",5,4),cd("4-6",6,4),cd("4-8",8,4),
            cd("4 1/2-4",4,4+1/2),cd("4 1/2-5",5,4+1/2),cd("4 1/2-6",6,4+1/2),
            cd("5-4",4,5),cd("5-5",5,5),cd("5-6",6,5),
            cd("5 1/2-4",4,5+1/2),cd("5 1/2-5",5,5+1/2),cd("5 1/2-6",6,5+1/2),
            cd("6-4",4,6),cd("6-5",5,6),cd("6-6",6,6),
            cd("7-3",3,7),cd("7-4",4,7),cd("7-5",5,7),
            cd("8-3",3,8),cd("8-4",4,8),cd("8-5",5,8),
            cd("9-3",3,9),cd("9-4",4,9),cd("9-5",5,9),
            cd("10-3",3,10),cd("10-4",4,10),cd("10-5",5,10),
            cd("11-2.5",2.5,11),cd("11-3",3,11),cd("11-4",4,11),
            cd("12-2.5",2.5,12),cd("12-3",3,12),cd("12-4",4,12),
            cd("13-2.5",2.5,13),cd("13-3",3,13),cd("13-4",4,13),
            cd("14-2.5",2.5,14),cd("14-3",3,14),cd("14-4",4,14),
            cd("16-2.5",2.5,16),cd("16-3",3,16),cd("16-4",4,16),
            cd("18-2",2,18),cd("18-2.5",2.5,18),cd("18-3",3,18),
            cd("20-2",2,20),cd("20-2.5",2.5,20),cd("20-3",3,20),
            cd("22-2",2,22),cd("22-2.5",2.5,22),cd("22-3",3,22),
            cd("24-2",2,24),cd("24-2.5",2.5,24),cd("24-3",3,24)]
        external_buttress_data = [0.651362286512,0.640050694251,0.62873910199,0.617427509729,0.606115917468,0.594804325207,0.583492732945,0.572181140684,0.560869548423,0.549557956162,0.538246363901,0.52693477164,0.515623179379,0.504311587118,0.492999994857,0.481688402596,0.470376810335,0.459065218074,0.447753625813,0.436442033552,0.42513044129,0.413818849029,0.402507256768,0.391195664507,0.379884072246,0.368572479985,0.357260887724,0.345949295463,0.334637703202,0.323326110941,0.31201451868,0.300702926419,0.289391334158,0.278079741896,0.266768149635,0.255456557374,0.244144965113,0.232833372852,0.221521780591,0.21021018833,0.198898596069,0.187587003808,0.176275411547,0.164963819286,0.153652227025,0.142340634764,0.131029042502,0.119717450241,0.10840585798,0.097094265719,0.085782673458,0.074471081197,0.063159488936,0.051847896675,0.040536304414,0.029224712153,0.017913119892,0.006601527631,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.001307212106,0.002696100995,0.004084989884,0.005473878773,0.006862767662,0.008251656551,0.00964054544,0.011029434329,0.012418323217,0.013807212106,0.015196100995,0.016584989884,0.017973878773,0.019362767662,0.020751656551,0.02214054544,0.023529434329,0.024918323217,0.026307212106,0.027696100995,0.029084989884,0.030473878773,0.031862767662,0.033251656551,0.03464054544,0.036029434329,0.037418323217,0.038807212106,0.040196100995,0.041584989884,0.042973878773,0.044362767662,0.045751656551,0.04714054544,0.048529434329,0.049918323217,0.051307212106,0.052696100995,0.054084989884,0.055473878773,0.056862767662,0.058251656551,0.05964054544,0.061029434329,0.062418323217,0.063807212106,0.065196100995,0.066584989884,0.067973878773,0.069362767662,0.070751656551,0.07214054544,0.073529434329,0.074918323217,0.076307212106,0.077696100995,0.079084989884,0.080473878773,0.081862767662,0.083251656551,0.08464054544,0.086029434329,0.087418323217,0.088807212106,0.090196100995,0.091584989884,0.092973878773,0.094362767662,0.095751656551,0.09714054544,0.098529434329,0.099918323217,0.101307212106,0.102696100995,0.104084989884,0.105473878773,0.106862767662,0.108251656551,0.10964054544,0.111029434329,0.112418323217,0.113807212106,0.115196100995,0.116584989884,0.117973878773,0.119362767662,0.120751656551,0.12214054544,0.123529434329,0.124918323217,0.126307212106,0.127696100995,0.129084989884,0.130473878773,0.131862767662,0.133251656551,0.13464054544,0.136029434329,0.137418323217,0.138807212106,0.140196100995,0.141584989884,0.142973878773,0.144362767662,0.145751656551,0.14714054544,0.148529434329,0.149918323217,0.151307212106,0.152696100995,0.154084989884,0.155473878773,0.156862767662,0.158251656551,0.15964054544,0.161029434329,0.162418323217,0.163807212106,0.165196100995,0.166584989884,0.167973878773,0.169362767662,0.170751656551,0.17214054544,0.173529434329,0.174918323217,0.176307212106,0.177696100995,0.179084989884,0.180473878773,0.181862767662,0.183251656551,0.18464054544,0.186029434329,0.187418323217,0.188807212106,0.190196100995,0.191584989884,0.192973878773,0.194362767662,0.195751656551,0.19714054544,0.198529434329,0.199918323217,0.201307212106,0.202696100995,0.204084989884,0.205473878773,0.206862767662,0.208251656551,0.20964054544,0.211029434329,0.212418323217,0.213807212106,0.215196100995,0.216584989884,0.217973878773,0.219362767662,0.220751656551,0.22214054544,0.223529434329,0.224918323217,0.226307212106,0.227696100995,0.229084989884,0.230473878773,0.231862767662,0.233251656551,0.23464054544,0.236029434329,0.237418323217,0.238807212106,0.240196100995,0.241584989884,0.242973878773,0.244362767662,0.245751656551,0.24714054544,0.248529434329,0.249918323217,0.251307212106,0.252696100995,0.254084989884,0.255473878773,0.256862767662,0.258251656551,0.25964054544,0.261029434329,0.262418323217,0.263807212106,0.265196100995,0.266584989884,0.267973878773,0.269362767662,0.270751656551,0.27214054544,0.273529434329,0.274918323217,0.276307212106,0.277696100995,0.279084989884,0.280473878773,0.281862767662,0.283251656551,0.28464054544,0.286029434329,0.287418323217,0.288807212106,0.290196100995,0.291584989884,0.292973878773,0.294362767662,0.295751656551,0.29714054544,0.298529434329,0.299918323217,0.301307212106,0.302696100995,0.304084989884,0.305473878773,0.306862767662,0.308251656551,0.30964054544,0.311029434329,0.312418323217,0.313807212106,0.315196100995,0.316584989884,0.317973878773,0.319362767662,0.320751656551,0.32214054544,0.323529434329,0.324918323217,0.326307212106,0.327696100995,0.329084989884,0.330473878773,0.331862767662,0.333251656551,0.33464054544,0.336029434329,0.337418323217,0.338807212106,0.340196100995,0.341584989884,0.342973878773,0.344362767662,0.345751656551,0.34714054544,0.348529434329,0.349918323217,0.351307212106,0.352696100995,0.354084989884,0.355473878773,0.356862767662,0.358251656551,0.35964054544,0.361029434329,0.362418323217,0.363807212106,0.365196100995,0.366584989884,0.367973878773,0.369362767662,0.370751656551,0.37214054544,0.373529434329,0.374918323217,0.376307212106,0.377696100995,0.379084989884,0.380473878773,0.381862767662,0.383251656551,0.38464054544,0.386029434329,0.387418323217,0.388807212106,0.390196100995,0.391584989884,0.392973878773,0.394362767662,0.395751656551,0.39714054544,0.398529434329,0.399918323217,0.401307212106,0.402696100995,0.404084989884,0.405473878773,0.406862767662,0.408251656551,0.40964054544,0.411029434329,0.412418323217,0.413807212106,0.415196100995,0.416584989884,0.417973878773,0.419362767662,0.420751656551,0.42214054544,0.423529434329,0.424918323217,0.426307212106,0.427696100995,0.429084989884,0.430473878773,0.431862767662,0.433251656551,0.43464054544,0.436029434329,0.437418323217,0.438807212106,0.440196100995,0.441584989884,0.442973878773,0.444362767662,0.445751656551,0.44714054544,0.448529434329,0.449918323217,0.451307212106,0.452696100995,0.454084989884,0.455473878773,0.456862767662,0.458251656551,0.45964054544,0.461029434329,0.462418323217,0.463807212106,0.465196100995,0.466584989884,0.467973878773,0.469362767662,0.470751656551,0.47214054544,0.473529434329,0.474918323217,0.476307212106,0.477696100995,0.479084989884,0.480473878773,0.481862767662,0.483251656551,0.48464054544,0.486029434329,0.487418323217,0.488807212106,0.490196100995,0.491584989884,0.492973878773,0.494362767662,0.495751656551,0.49714054544,0.498529434329,0.499918323217,0.501307212106,0.502696100995,0.504084989884,0.505473878773,0.506862767662,0.508251656551,0.50964054544,0.511029434329,0.512418323217,0.513807212106,0.515196100995,0.516584989884,0.517973878773,0.519362767662,0.520751656551,0.52214054544,0.523529434329,0.524918323217,0.526307212106,0.527696100995,0.529084989884,0.530473878773,0.531862767662,0.533251656551,0.53464054544,0.536029434329,0.537418323217,0.538807212106,0.540196100995,0.541584989884,0.542973878773,0.544362767662,0.545751656551,0.54714054544,0.548529434329,0.549918323217,0.551307212106,0.552696100995,0.554084989884,0.555473878773,0.556862767662,0.558251656551,0.55964054544,0.561029434329,0.562418323217,0.563807212106,0.565196100995,0.566584989884,0.567973878773,0.569362767662,0.570751656551,0.57214054544,0.573529434329,0.574918323217,0.576307212106,0.577696100995,0.579084989884,0.580473878773,0.581862767662,0.583251656551,0.58464054544,0.586029434329,0.587418323217,0.588807212106,0.590196100995,0.591584989884,0.592973878773,0.594362767662,0.595751656551,0.59714054544,0.598529434329,0.599918323217,0.601307212106,0.602696100995,0.604084989884,0.605473878773,0.606862767662,0.608251656551,0.60964054544,0.611029434329,0.612418323217,0.613807212106,0.615196100995,0.616584989884,0.617973878773,0.619362767662,0.620751656551,0.62214054544,0.623529434329,0.624918323217,0.626307212106,0.627696100995,0.629084989884,0.630473878773,0.631862767662,0.633251656551,0.63464054544,0.636029434329,0.637418323217,0.638807212106,0.640196100995,0.641584989884,0.642973878773,0.644362767662,0.645751656551,0.64714054544,0.648529434329,0.649918323217,0.651307212106,0.652696100995,0.654084989884,0.655473878773,0.656862767662,0.658251656551,0.65964054544,0.661029434329,0.662418323217,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773,0.662673878773]
        internal_buttress_data = [0.651400386759,0.640088794497,0.628777202236,0.617465609975,0.606154017714,0.594842425453,0.583530833192,0.572219240931,0.56090764867,0.549596056409,0.538284464148,0.526972871887,0.515661279626,0.504349687365,0.493038095104,0.481726502842,0.470414910581,0.45910331832,0.447791726059,0.436480133798,0.425168541537,0.413856949276,0.402545357015,0.391233764754,0.379922172493,0.368610580232,0.357298987971,0.34598739571,0.334675803449,0.323364211188,0.312052618926,0.300741026665,0.289429434404,0.278117842143,0.266806249882,0.255494657621,0.24418306536,0.232871473099,0.221559880838,0.210248288577,0.198936696316,0.187625104055,0.176313511794,0.165001919533,0.153690327272,0.14237873501,0.131067142749,0.119755550488,0.108443958227,0.097132365966,0.085820773705,0.074509181444,0.063197589183,0.051885996925,0.040574404667,0.029262812409,0.017951220151,0.006639627893,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.000871979,0.00226086789,0.00364975678,0.005038645671,0.006427534561,0.007816423451,0.009205312341,0.010594201232,0.011983090122,0.013371979012,0.014760867902,0.016149756793,0.017538645683,0.018927534573,0.020316423463,0.021705312353,0.023094201242,0.024483090131,0.02587197902,0.027260867909,0.028649756797,0.030038645686,0.031427534575,0.032816423464,0.034205312353,0.035594201242,0.036983090131,0.03837197902,0.039760867909,0.041149756797,0.042538645686,0.043927534575,0.045316423464,0.046705312353,0.048094201242,0.049483090131,0.05087197902,0.052260867909,0.053649756797,0.055038645686,0.056427534575,0.057816423464,0.059205312353,0.060594201242,0.061983090131,0.06337197902,0.064760867908,0.066149756797,0.067538645686,0.068927534575,0.070316423464,0.071705312353,0.073094201242,0.074483090131,0.07587197902,0.077260867908,0.078649756797,0.080038645686,0.081427534575,0.082816423464,0.084205312353,0.085594201242,0.086983090131,0.08837197902,0.089760867908,0.091149756797,0.092538645686,0.093927534575,0.095316423464,0.096705312353,0.098094201242,0.099483090131,0.10087197902,0.102260867908,0.103649756797,0.105038645686,0.106427534575,0.107816423464,0.109205312353,0.110594201242,0.111983090131,0.11337197902,0.114760867908,0.116149756797,0.117538645686,0.118927534575,0.120316423464,0.121705312353,0.123094201242,0.124483090131,0.12587197902,0.127260867908,0.128649756797,0.130038645686,0.131427534575,0.132816423464,0.134205312353,0.135594201242,0.136983090131,0.13837197902,0.139760867908,0.141149756797,0.142538645686,0.143927534575,0.145316423464,0.146705312353,0.148094201242,0.149483090131,0.15087197902,0.152260867908,0.153649756797,0.155038645686,0.156427534575,0.157816423464,0.159205312353,0.160594201242,0.161983090131,0.16337197902,0.164760867908,0.166149756797,0.167538645686,0.168927534575,0.170316423464,0.171705312353,0.173094201242,0.174483090131,0.17587197902,0.177260867908,0.178649756797,0.180038645686,0.181427534575,0.182816423464,0.184205312353,0.185594201242,0.186983090131,0.18837197902,0.189760867908,0.191149756797,0.192538645686,0.193927534575,0.195316423464,0.196705312353,0.198094201242,0.199483090131,0.20087197902,0.202260867908,0.203649756797,0.205038645686,0.206427534575,0.207816423464,0.209205312353,0.210594201242,0.211983090131,0.21337197902,0.214760867908,0.216149756797,0.217538645686,0.218927534575,0.220316423464,0.221705312353,0.223094201242,0.224483090131,0.22587197902,0.227260867908,0.228649756797,0.230038645686,0.231427534575,0.232816423464,0.234205312353,0.235594201242,0.236983090131,0.23837197902,0.239760867908,0.241149756797,0.242538645686,0.243927534575,0.245316423464,0.246705312353,0.248094201242,0.249483090131,0.25087197902,0.252260867908,0.253649756797,0.255038645686,0.256427534575,0.257816423464,0.259205312353,0.260594201242,0.261983090131,0.26337197902,0.264760867908,0.266149756797,0.267538645686,0.268927534575,0.270316423464,0.271705312353,0.273094201242,0.274483090131,0.27587197902,0.277260867908,0.278649756797,0.280038645686,0.281427534575,0.282816423464,0.284205312353,0.285594201242,0.286983090131,0.28837197902,0.289760867908,0.291149756797,0.292538645686,0.293927534575,0.295316423464,0.296705312353,0.298094201242,0.299483090131,0.30087197902,0.302260867908,0.303649756797,0.305038645686,0.306427534575,0.307816423464,0.309205312353,0.310594201242,0.311983090131,0.31337197902,0.314760867908,0.316149756797,0.317538645686,0.318927534575,0.320316423464,0.321705312353,0.323094201242,0.324483090131,0.32587197902,0.327260867908,0.328649756797,0.330038645686,0.331427534575,0.332816423464,0.334205312353,0.335594201242,0.336983090131,0.33837197902,0.339760867908,0.341149756797,0.342538645686,0.343927534575,0.345316423464,0.346705312353,0.348094201242,0.349483090131,0.35087197902,0.352260867908,0.353649756797,0.355038645686,0.356427534575,0.357816423464,0.359205312353,0.360594201242,0.361983090131,0.36337197902,0.364760867908,0.366149756797,0.367538645686,0.368927534575,0.370316423464,0.371705312353,0.373094201242,0.374483090131,0.37587197902,0.377260867908,0.378649756797,0.380038645686,0.381427534575,0.382816423464,0.384205312353,0.385594201242,0.386983090131,0.38837197902,0.389760867908,0.391149756797,0.392538645686,0.393927534575,0.395316423464,0.396705312353,0.398094201242,0.399483090131,0.40087197902,0.402260867908,0.403649756797,0.405038645686,0.406427534575,0.407816423464,0.409205312353,0.410594201242,0.411983090131,0.41337197902,0.414760867908,0.416149756797,0.417538645686,0.418927534575,0.420316423464,0.421705312353,0.423094201242,0.424483090131,0.42587197902,0.427260867908,0.428649756797,0.430038645686,0.431427534575,0.432816423464,0.434205312353,0.435594201242,0.436983090131,0.43837197902,0.439760867908,0.441149756797,0.442538645686,0.443927534575,0.445316423464,0.446705312353,0.448094201242,0.449483090131,0.45087197902,0.452260867908,0.453649756797,0.455038645686,0.456427534575,0.457816423464,0.459205312353,0.460594201242,0.461983090131,0.46337197902,0.464760867908,0.466149756797,0.467538645686,0.468927534575,0.470316423464,0.471705312353,0.473094201242,0.474483090131,0.47587197902,0.477260867908,0.478649756797,0.480038645686,0.481427534575,0.482816423464,0.484205312353,0.485594201242,0.486983090131,0.48837197902,0.489760867908,0.491149756797,0.492538645686,0.493927534575,0.495316423464,0.496705312353,0.498094201242,0.499483090131,0.50087197902,0.502260867908,0.503649756797,0.505038645686,0.506427534575,0.507816423464,0.509205312353,0.510594201242,0.511983090131,0.51337197902,0.514760867908,0.516149756797,0.517538645686,0.518927534575,0.520316423464,0.521705312353,0.523094201242,0.524483090131,0.52587197902,0.527260867908,0.528649756797,0.530038645686,0.531427534575,0.532816423464,0.534205312353,0.535594201242,0.536983090131,0.53837197902,0.539760867908,0.541149756797,0.542538645686,0.543927534575,0.545316423464,0.546705312353,0.548094201242,0.549483090131,0.55087197902,0.552260867908,0.553649756797,0.555038645686,0.556427534575,0.557816423464,0.559205312353,0.560594201242,0.561983090131,0.56337197902,0.564760867908,0.566149756797,0.567538645686,0.568927534575,0.570316423464,0.571705312353,0.573094201242,0.574483090131,0.57587197902,0.577260867908,0.578649756797,0.580038645686,0.581427534575,0.582816423464,0.584205312353,0.585594201242,0.586983090131,0.58837197902,0.589760867908,0.591149756797,0.592538645686,0.593927534575,0.595316423464,0.596705312353,0.598094201242,0.599483090131,0.60087197902,0.602260867908,0.603649756797,0.605038645686,0.606427534575,0.607816423464,0.609205312353,0.610594201242,0.611983090131,0.61337197902,0.614760867908,0.616149756797,0.617538645686,0.618927534575,0.620316423464,0.621705312353,0.623094201242,0.624483090131,0.62587197902,0.627260867908,0.628649756797,0.630038645686,0.631427534575,0.632816423464,0.634205312353,0.635594201242,0.636983090131,0.63837197902,0.639760867908,0.641149756797,0.642538645686,0.643927534575,0.645316423464,0.646705312353,0.648094201242,0.649483090131,0.65087197902,0.652260867908,0.653649756797,0.655038645686,0.656427534575,0.657816423464,0.659205312353,0.660594201242,0.661983090131,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902,0.66271197902]
        super(ThreadProfileCreateButtressObjectCommandClass, self).makeThreadProfile(name="BThreadProfile",internal_data = internal_buttress_data, external_data = external_buttress_data, presets = buttress_presets_data,minor_diameter=buttress_presets_data[13][2],pitch=25.4/10,internal_or_external="External",thread_count=10,Quality=6)

#Gui.addCommand("ThreadProfileCreateButtressObject", ThreadProfileCreateButtressObjectCommandClass())

####################################################################################
# Create the bottle thread profile object

class ThreadProfileCreateBottleObjectCommandClass(ThreadProfileCreateObjectCommandClass):
    """Create Object command"""

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreateBottleObject.svg') ,
            'MenuText': "&Create Bottle thread profile" ,
            'ToolTip' : "Create the SP4xx (M) 45 degree / 10 degree buttress bottle thread ThreadProfile object"}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        doc.openTransaction("Create Bottle ThreadProfile")
        try:
            self.makeBottleThreadProfile()
        except Exception as e:
            FreeCAD.Console.PrintError(
    	        "ThreadProfile Error: Exception creating thread profile object.\n\n" +
    	        '\n'.join(traceback.format_exception(e)) + "\n"
            )
            QtGui.QApplication.restoreOverrideCursor()
        doc.commitTransaction()
        doc.recompute()
        return

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        return True

    def getHelp(self):
        return ["Created with ThreadProfile (v"+str(version)+") workbench.",
                "This is a thread profile object built",
                "for sweeping along a helix in either the",
                "Part or Part Design workbench."
                "installation of the ThreadProfile workbench is required.",
]
    def makeBottleThreadProfile(self):

        def cd(txt, minor, major, tpi): #cd = calculate diameters
            pitch = 25.4/tpi
            offset = .25 #.25 mm
            external = minor
            internal = minor + offset
            return[txt, pitch, external, internal]
        bottle_presets_data = [
            ["Bottle presets",0,0,0], #just fillers, not used
            cd('13-SP415(M)',11.53,13.06,12),
            cd('15-SP415(M)',13.23,14.76,12),
            cd('18-SP400(M)',15.75,17.88,8),
            cd('20-SP400(M)',17.75,19.89,8),
            cd('22-SP400(M)',19.76,21.89,8),
            cd('24-SP400(M)',21.74,23.87,8),
            cd('28-SP400(M)',25.25,27.64,6),
            cd('30-SP400(M)',26.23,28.62,6),
            cd('33-SP400(M)',29.74,32.14,6),
            cd('35-SP400(M)',32.25,34.64,6),
            cd('38-SP400(M)',35.10,37.50,6),
            cd('40-SP400(M)',37.75,40.13,6),
            cd('43-SP400(M)',39.62,42.00,6),
            cd('45-SP400(M)',41.81,44.20,6),
            cd('48-SP400(M)',45.11,47.50,6),
            cd('51-SP400(M)',47.60,50.00,6),
            cd('53-SP400(M)',50.11,52.50,6),
            cd('58-SP400(M)',54.10,56.50,6),
            cd('60-SP400(M)',57.10,59.50,6),
            cd('63-SP400(M)',60.12,62.51,6),
            cd('66-SP400(M)',63.12,65.50,6),
            cd('70-SP400(M)',67.00,69.50,6),
            cd('75-SP400(M)',71.60,74.00,6),
            cd('77-SP400(M)',74.70,77.10,6),
            cd('83-SP400(M)',80.00,83.00,5),
            cd('89-SP400(M)',86.12,89.18,5),
            cd('100-SP400(M)',96.95,100.00,5),
            cd('110-SP400(M)',107.00,110.00,5),
            cd('120-SP400(M)',117.00,120.00,5)]

        internal_bottle_data = [6.8683031e-05,0.000137366062,0.000212133459,0.000297079403,0.00043472746,0.000654671378,0.000874564607,0.001094356609,0.001359150971,0.001721121373,0.002082807209,0.002443804942,0.002850563041,0.003361308354,0.003871704024,0.004381405087,0.004955897908,0.005628737414,0.006300748062,0.006971927834,0.007756613829,0.008607819995,0.009457347838,0.010315734263,0.011370310303,0.012423445314,0.013473928827,0.014685365793,0.015972298608,0.017255462058,0.018731355311,0.020298896767,0.021860838018,0.023734575329,0.0256608722,0.027746830253,0.030156669021,0.032682649119,0.035784784003,0.039333119593,0.043607169802,0.050108303718,0.058203072769,0.066297841819,0.074392610869,0.082487379919,0.090582148969,0.09867691802,0.10677168707,0.114715457724,0.122454130079,0.130192802434,0.137931474789,0.145783494053,0.153739940852,0.16169638765,0.169652834449,0.177609281248,0.185565728047,0.193522174845,0.201478621644,0.209435068443,0.217250848149,0.225058671756,0.232866495362,0.239116950513,0.243239377186,0.246810305242,0.249853555844,0.252406769649,0.254797942824,0.256883002572,0.258810868767,0.2606626839,0.262236336952,0.263809990003,0.265260684115,0.266549898945,0.267839113775,0.269050111281,0.270106429841,0.271162748401,0.272203697656,0.273058398511,0.273913099365,0.27476780022,0.275542163288,0.276214672995,0.276887182703,0.27755969241,0.278135951759,0.278642295503,0.279148639248,0.279654982993,0.280079914105,0.280431233266,0.280782552427,0.281133871587,0.281437919761,0.281640871019,0.281843822278,0.282046773536,0.282248726063,0.282314318596,0.28237991113,0.282445645984,0.282510772153,0.282532145192,0.282553518231,0.28257489127,0.28259626431,0.282617637349,0.282639010388,0.282660383427,0.282681756466,0.282703129505,0.282724502544,0.282745875583,0.282767248622,0.282788621661,0.282809994701,0.28283136774,0.282852740779,0.282874113818,0.282895486857,0.282916859896,0.282938232935,0.282959605974,0.282980979013,0.283002352052,0.283023725092,0.283045098131,0.28306647117,0.283087844209,0.283109217248,0.283130590287,0.283151963326,0.283173336365,0.283194709404,0.283216082443,0.283237455483,0.283258828522,0.283280201561,0.2833015746,0.283322947639,0.283344320678,0.283365693717,0.283387066756,0.283408439795,0.283429812834,0.283451185874,0.283472558913,0.283493931952,0.283515304991,0.28353667803,0.283558051069,0.283579424108,0.283600797147,0.283622170186,0.283643543225,0.283664916265,0.283686289304,0.283707662343,0.283729035382,0.283750408421,0.28377178146,0.283793154499,0.283814527538,0.283835900577,0.283857273616,0.283878646656,0.283900019695,0.283921392734,0.283942765773,0.283951688599,0.283902194483,0.283852700366,0.283803206249,0.283753712132,0.283704218016,0.283654723899,0.283611569121,0.283630031582,0.283648494043,0.283666956504,0.283685418965,0.283689560214,0.283620503218,0.283551446222,0.283482389226,0.28341333223,0.283344275234,0.283275218238,0.283206161242,0.283137104246,0.28306804725,0.282998990254,0.282929933258,0.282861100274,0.282719757663,0.282512040929,0.282304324194,0.28209660746,0.281888890725,0.281681173991,0.281473457256,0.281265740522,0.281058023788,0.280850307053,0.280642590319,0.280434873584,0.280213015121,0.279862714081,0.279512413041,0.279162112001,0.278811810961,0.278461509921,0.278111208881,0.277760907841,0.277410606801,0.277060305761,0.276710004721,0.276359703681,0.276009998755,0.275530567714,0.275029495361,0.274528423008,0.274027350656,0.273526278303,0.273025205951,0.272524133598,0.272023061246,0.271521988893,0.271020916541,0.270519844188,0.270018438336,0.269367290509,0.268703541348,0.268039792187,0.267376043026,0.266712293865,0.266048544704,0.265384795543,0.264721046382,0.264057297221,0.26339354806,0.262729703442,0.261990260998,0.261146476239,0.260302691481,0.259458906723,0.258615121965,0.257771337207,0.256927552448,0.25608376769,0.255239982932,0.254396198174,0.25355230571,0.25261348976,0.251565238425,0.25051698709,0.249468735755,0.24842048442,0.247372233085,0.24632398175,0.245275730415,0.24422747908,0.243179227745,0.242086677594,0.240815575077,0.239545391949,0.238275208821,0.237005025693,0.235734842565,0.234464659437,0.233194476309,0.231924293181,0.230568655072,0.229206476602,0.227844298132,0.226482119662,0.225119941192,0.223757762722,0.222395584252,0.221033405782,0.219650107646,0.218236464012,0.216822820379,0.215409176745,0.213995533111,0.212581889477,0.211168245844,0.20975460221,0.208340958576,0.206927314943,0.205513671309,0.204100027675,0.202686384042,0.201272740408,0.199859096774,0.19844545314,0.197031809507,0.195618165873,0.194204522239,0.192790878606,0.191377234972,0.189963591338,0.188549947705,0.187136304071,0.185722660437,0.184309016804,0.18289537317,0.181481729536,0.180068085902,0.178654442269,0.177240798635,0.175827155001,0.174413511368,0.172999867734,0.1715862241,0.170172580467,0.168758936833,0.167345293199,0.165931649565,0.164518005932,0.163104362298,0.161690718664,0.160277075031,0.158863431397,0.157449787763,0.15603614413,0.154622500496,0.153208856862,0.151795213228,0.150381569595,0.148967925961,0.147554282327,0.146140638694,0.14472699506,0.143313351426,0.141899707793,0.140500737494,0.139112056243,0.137723374992,0.13633469374,0.134946012489,0.133557331238,0.132168649987,0.130779968736,0.129391287485,0.128002606234,0.126613924982,0.125225243731,0.12383656248,0.122447881229,0.121059199978,0.119670518727,0.118281837476,0.116893156224,0.115504474973,0.114115793722,0.112727112471,0.11133843122,0.109949749969,0.108561068718,0.107172387466,0.105783706215,0.104395024964,0.103006343713,0.101617662462,0.100228981211,0.09884029996,0.097451618709,0.096062937457,0.094674256206,0.093285574955,0.091896893704,0.090508212453,0.089119531202,0.087730849951,0.086342168699,0.084953487448,0.083564806197,0.082176124946,0.080788287214,0.079404069355,0.078019851497,0.076635633638,0.07525141578,0.073867197921,0.072482980062,0.071098762204,0.069714544345,0.068330326487,0.066946108628,0.06556189077,0.064177672911,0.062793455052,0.061409237194,0.060025019335,0.058640801477,0.057256583618,0.05587236576,0.054488147901,0.053103930042,0.051733224667,0.050401495599,0.04906976653,0.047784638712,0.046568266765,0.045351894818,0.04413552287,0.042919150923,0.041702778976,0.040486407028,0.03943618023,0.03841146284,0.03738674545,0.036359968043,0.03533264278,0.034305317518,0.033277992255,0.032250666993,0.03122334173,0.030196016468,0.0293209833,0.028493936502,0.027666889704,0.026838996003,0.026010063867,0.025181131732,0.024352199596,0.023523267461,0.022694335326,0.02186540319,0.021036471055,0.020370341413,0.019719415915,0.019068490416,0.018417074611,0.017764922316,0.017112770022,0.016460617727,0.015808465432,0.015156313138,0.014504160843,0.013852008548,0.013269101482,0.012779696297,0.012290291113,0.011800885928,0.01131111685,0.010821219432,0.010331322013,0.009841424595,0.009351527176,0.008861629757,0.008371732339,0.00788183492,0.007452335438,0.007114370116,0.006776404795,0.006438439474,0.006100222288,0.005761820231,0.005423418173,0.005085016115,0.004746614058,0.004408212,0.004069809943,0.003731407885,0.003393005828,0.003191735689,0.002998655249,0.00280557481,0.002612490228,0.002419282801,0.002226075374,0.002032867947,0.00183966052,0.001646453093,0.001453245666,0.001260038239,0.001066830812,0.000900522301,0.000839410957,0.000778299614,0.00071718827,0.000656076927,0.000594965583,0.00053385424,0.000472742896,0.000411828152,0.00035115619,0.000290484228,0.000230947612,0.000238906289,0.000246864967,0.000254823645,0.000262782322,0.000270741,0.000278699678,0.000286658355,0.000294617033,0.000302575711,0.000310534388,0.000318493066,0.000326451744,0.000334410422,0.000342369099,0.000350327777,0.000358286455,0.000366245132,0.00037420381,0.000382162488,0.000390121165,0.000398079843,0.000406038521,0.000413997198,0.000421955876,0.000429914554,0.000437873231,0.000445831909,0.000453790587,0.000461749264,0.000469707942,0.00047766662,0.000485625297,0.000493583975,0.000501542653,0.00050950133,0.000517460008,0.000525418686,0.000533377363,0.000541336041,0.000549294719,0.000557253396,0.000565212074,0.000573170752,0.000581129429,0.000589088107,0.000597046785,0.000605005462,0.00061296414,0.000620922818,0.000628881496,0.000636840173,0.000644798851,0.000652757529,0.000660716206,0.000668674884,0.000676633562,0.000684592239,0.000692550917,0.000700509595,0.000708468272,0.00071642695,0.000724385628,0.000732344305,0.000740302983,0.000748261661,0.000756220338,0.000764179016,0.000772137694,0.000780096371,0.000788055049,0.000796013727,0.000803972404,0.000811931082,0.00081988976,0.000827848437,0.000835807115,0.000843765793,0.00085172447,0.000859683148,0.000867641826,0.000875600503,0.000883559181,0.000891517859,0.000899476536,0.000907435214,0.000915393892,0.00092335257,0.000931311247,0.000939269925,0.000947228603,0.00095518728,0.000963145958,0.000971104636,0.000979063313,0.000987021991,0.000994980669,0.001002939346,0.001010898024,0.001018856702,0.001026815379,0.001034774057,0.001042732735,0.001050691412,0.00105865009,0.001066608768,0.001074567445,0.001082526123,0.001090484801,0.001098443478,0.001106402156,0.001114360834,0.001122319511,0.001130278189,0.001138236867,0.001146195544,0.001154154222,0.0011621129,0.001170071577,0.001178030255,0.001185988933,0.001193947611,0.001201906288,0.001209864966,0.001217823644,0.001225782321,0.001233740999,0.001241699677,0.001249658354,0.001257617032,0.00126557571,0.001273534387,0.001281493065,0.001289451743,0.00129741042,0.001305369098,0.001313327776,0.001321286453,0.001329245131,0.001337203809,0.001345162486,0.001353121164,0.001361079842,0.001369038519,0.001376997197,0.001384955875,0.001392914552,0.00140087323,0.001408831908,0.001416790585,0.001403595664,0.001384628155,0.001365660646,0.001346693137,0.001327725628,0.001308758119,0.00128979061,0.001270823101,0.001251855592,0.001232888083,0.001213920574,0.001194953065,0.001175985556,0.001157018047,0.001138050538,0.001119083029,0.00110011552,0.001081148011,0.001062180502,0.001043212993,0.001024245484,0.001005277975,0.000986310466,0.000967342957,0.000948375448,0.00092940794,0.000910440431,0.000891472922,0.000872505413,0.000853537904,0.000834570395,0.000815602886,0.000796635377,0.000777667868,0.000758700359,0.00073973285,0.000720765341,0.000701797832,0.000682830323,0.000663862814,0.000644895305,0.000625927796,0.000606960287,0.000587992778,0.000569025269,0.00055005776,0.000531090251,0.000512122742,0.000493155233,0.000474187724,0.000455220215,0.000436252706,0.000417285197,0.000398317688,0.000379350179,0.00036038267,0.000341415161,0.000322447652,0.000303480144,0.000284512635,0.000265545126,0.000246577617,0.000227610108,0.000208642599,0.00018967509,0.000170707581,0.000151740072,0.000132772563,0.000113805054,9.4837545e-05,7.5870036e-05,5.6902527e-05,3.7935018e-05,1.8967509e-05]
        external_bottle_data = internal_bottle_data
        super(ThreadProfileCreateBottleObjectCommandClass, self).makeThreadProfile(name="Bottle_M_ThreadProfile",internal_data = internal_bottle_data, external_data = external_bottle_data, presets = bottle_presets_data,minor_diameter=bottle_presets_data[13][2],pitch=bottle_presets_data[13][1],internal_or_external="External",thread_count=3,Quality=6)

#Gui.addCommand("ThreadProfileCreateBottleObject", ThreadProfileCreateBottleObjectCommandClass())
####################################################################################

def initialize():
    if FreeCAD.GuiUp:
        Gui.addCommand("ThreadProfileCreateObject", ThreadProfileCreateObjectCommandClass())
        Gui.addCommand("ThreadProfileMakeHelix", ThreadProfileMakeHelixCommandClass())
        Gui.addCommand("ThreadProfileOpenOnlineCalculator", ThreadProfileOpenOnlineCalculatorCommandClass())
        Gui.addCommand("ThreadProfileCreateButtressObject", ThreadProfileCreateButtressObjectCommandClass())
        Gui.addCommand("ThreadProfileCreateBottleObject", ThreadProfileCreateBottleObjectCommandClass())
        Gui.addCommand("ThreadProfileDoSweep", ThreadProfileDoSweepCommandClass())
        Gui.addCommand("ThreadProfileSettings", ThreadProfileSettingsCommandClass())


initialize()
