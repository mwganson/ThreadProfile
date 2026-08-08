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
__date__    = "2026.07.28"
__version__ = "2.02"

from fractions import Fraction
from numbers import Rational

version = 2.02

import FreeCAD, FreeCADGui, Part, os
from PySide import QtCore, QtGui
import math
import traceback
import Draft
from FreeCAD import Base
import Draft_rc
from PySide.QtCore import QT_TRANSLATE_NOOP
from Draft import _DraftObject, formatObject, select

if FreeCAD.GuiUp:
    from FreeCAD import Gui
    from Draft import _ViewProviderWire

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
        items = ["Open online metric calculator", "Open online unified inch calculator", "Open online ANSI buttress thread calculator", "Open PG (DIN 40430) thread chart (British Metrics)", "Open BSW Whitworth thread chart", "Open BSF Whitworth fine thread chart", "Cancel"]
        window = QtGui.QApplication.activeWindow()
        item,ok = QtGui.QInputDialog.getItem(window,'ThreadProfile','Open online calculator in default browser?',items,0,False)
        if ok and item == items[0]:
            webbrowser.open('https://amesweb.info/Screws/IsoMetricScrewThread.aspx')
        elif ok and item == items[1]:
            webbrowser.open('https://amesweb.info/Screws/AsmeUnifiedInchScrewThread.aspx')
        elif ok and item == items[2]:
            webbrowser.open('https://amesweb.info/Screws/ButtressInchScrewThreads.aspx')
        elif ok and item == items[3]:
            webbrowser.open('https://www.britishmetrics.com/images/pdf/technical/pgstd_4.htm')
        elif ok and item == items[4]:
            webbrowser.open('https://www.machiningdoctor.com/charts/bsw/')
        elif ok and item == items[5]:
            webbrowser.open('https://www.machiningdoctor.com/charts/bsf/')

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

        def preset_v_thread(name: str, major_diameter: float, pitch: float, angle_deg: float):
            height = pitch / (2 * math.tan(math.radians(angle_deg) / 2))
            internal_minor_diameter = major_diameter - 2 * 5 / 8 * height
            external_minor_diameter = major_diameter - 2 * 0.7085 * height
            return [name, pitch, external_minor_diameter, internal_minor_diameter]

        def preset_metric(name_postfix: str, major_diameter: float, pitch: float):
            return preset_v_thread(f'M{major_diameter} x {pitch} {name_postfix}', major_diameter, pitch, 60)

        def mc(major_diameter: float, pitch: float): # metric coarse
            return preset_metric('Coarse', major_diameter, pitch)

        def mf(major_diameter: float, pitch: float):  # metric coarse
            return preset_metric('Fine', major_diameter, pitch)

        def ttp(tpi: float): # TPI to pitch
            return 25.4 / tpi

        def format_rational(rational: Rational):
            denominator = int(rational.denominator)
            numerator = int(rational.numerator)
            whole = numerator // denominator
            fraction_numerator = numerator % denominator
            if fraction_numerator == 0:
                return f'{whole}'
            elif whole == 0:
                return f'{fraction_numerator}/{denominator}'
            else:
                return f'{whole} {fraction_numerator}/{denominator}'

        def mixed(whole: int, numerator: int, denominator: int):
            return Fraction(denominator * whole + numerator, denominator)

        def uts_number_diameter(number: int):
            return number * 0.013 + 0.06

        def preset_uts(name_postfix: str, size_name: str, major_diameter_in: float, tpi: float):
            name = f'{size_name} - {tpi} {name_postfix}'
            return preset_v_thread(name, major_diameter_in * 25.4, ttp(tpi), 60)

        def uts_numbered_major_diameter_in(number):
            return number * 0.013 + 0.06

        def unc(major_diameter_in: Fraction, tpi: float):
            name = f'{format_rational(major_diameter_in)} in'
            return preset_uts('UNC', name, float(major_diameter_in), tpi)

        # numbered UNC
        def nunc(number: int, tpi: float):
            major_diameter_in = uts_numbered_major_diameter_in(number)
            return preset_uts('UNC', f'#{number}', major_diameter_in, tpi)

        def unf(major_diameter_in: Fraction, tpi: float):
            name = f'{format_rational(major_diameter_in)} in'
            return preset_uts('UNF', name, float(major_diameter_in), tpi)

        # numbered UNF
        def nunf(number: int, tpi: float):
            major_diameter_in = uts_numbered_major_diameter_in(number)
            return preset_uts('UNF', f'#{number}', major_diameter_in, tpi)

        def uns(major_diameter_in: Fraction, tpi: float):
            name = f'{format_rational(major_diameter_in)} in'
            return preset_uts('UNS', name, float(major_diameter_in), tpi)

        # numbered UNS
        def nuns(number: int, tpi: float):
            major_diameter_in = uts_numbered_major_diameter_in(number)
            return preset_uts('UNS', f'#{number}', major_diameter_in, tpi)


        if len (presets) == 0:
            tmp_presets_data=[
            ['V Thread Presets',0,0,0],
            ['Garden Hose NHR',0.08696*25.4,0.9495*25.4,0.9720*25.4],
                mc(1.6, 0.35),
                mc(2, 0.4),
                mc(2.5, 0.45),
                mc(3, 0.5),
                mc(3.5, 0.6),
                mc(4, 0.7),
                mc(5, 0.8),
                mc(6, 1),
                mc(8, 1.25),
                mc(8, 1),
                mc(10, 1.5),
                mc(10, 1.25),
                mc(10, 1),
                mc(10, 0.75),
                mc(12, 1.75),
                mc(12, 1.5),
                mc(12, 1.25),
                mc(12, 1),
                mc(14, 2),
                mc(14, 1.5),
                mc(15, 1),
                mc(16, 2),
                mc(16, 1.5),
                mc(17, 1),
                mc(18, 1.5),
                mc(20, 2.5),
                mc(20, 1.5),
                mc(20, 1),
                mc(22, 2.5),
                mc(22, 1.5),
                mc(24, 3),
                mc(24, 2),
                mc(25, 1.5),
                mc(27, 3),
                mc(27, 2),
                mc(30, 3.5),
                mc(30, 2),
                mc(30, 1.5),
                mc(33, 2),
                mc(35, 1.5),
                mc(36, 4),
                mc(36, 2),
                mc(39, 2),
                mc(40, 1.5),
                mc(42, 4.5),
                mc(42, 2),
                mc(45, 1.5),
                mc(48, 5),
                mc(48, 2),
                mc(50, 1.5),
                mc(55, 1.5),
                mc(56, 5.5),
                mc(56, 2),
                mc(60, 1.5),
                mc(64, 6),
                mc(64, 2),
                mc(65, 1.5),
                mc(70, 1.5),
                mc(72, 6),
                mc(72, 2),
                mc(75, 1.5),
                mc(80, 6),
                mc(80, 2),
                mc(80, 1.5),
                mc(85, 2),
                mc(90, 6),
                mc(90, 2),
                mc(95, 2),
                mc(100, 6),
                mc(100, 2),
                mc(105, 2),
                mc(110, 2),
                mc(120, 2),
                mc(130, 2),
                mc(140, 2),
                mc(150, 2),
                mc(160, 3),
                mc(170, 3),
                mc(180, 3),
                mc(190, 3),
                mc(200, 3),
                mf(1, 0.2),
                mf(1.1, 0.2),
                mf(1.2, 0.2),
                mf(1.4, 0.2),
                mf(1.6, 0.2),
                mf(1.8, 0.2),
                mf(2, 0.25),
                mf(2.2, 0.25),
                mf(2.5, 0.35),
                mf(3, 0.35),
                mf(3.5, 0.35),
                mf(4, 0.5),
                mf(4.5, 0.5),
                mf(5, 0.5),
                mf(5.5, 0.5),
                mf(6, 0.75),
                mf(7, 0.75),
                mf(8, 0.75),
                mf(8, 1),
                mf(9, 0.75),
                mf(9, 1),
                mf(10, 0.75),
                mf(10, 1),
                mf(10, 1.25),
                mf(11, 0.75),
                mf(11, 1),
                mf(12, 1),
                mf(12, 1.25),
                mf(12, 1.5),
                mf(14, 1),
                mf(14, 1.25),
                mf(14, 1.5),
                mf(15, 1),
                mf(15, 1.5),
                mf(16, 1),
                mf(16, 1.5),
                mf(17, 1),
                mf(17, 1.5),
                mf(18, 1),
                mf(18, 1.5),
                mf(18, 2),
                mf(20, 1),
                mf(20, 1.5),
                mf(20, 2),
                mf(22, 1),
                mf(22, 1.5),
                mf(22, 2),
                mf(24, 1),
                mf(24, 1.5),
                mf(24, 2),
                mf(25, 1),
                mf(25, 1.5),
                mf(25, 2),
                mf(27, 1),
                mf(27, 1.5),
                mf(27, 2),
                mf(28, 1),
                mf(28, 1.5),
                mf(28, 2),
                mf(30, 1),
                mf(30, 1.5),
                mf(30, 2),
                mf(30, 3),
                mf(32, 1.5),
                mf(32, 2),
                mf(33, 1.5),
                mf(33, 2),
                mf(33, 3),
                mf(35, 1.5),
                mf(35, 2),
                mf(36, 1.5),
                mf(36, 2),
                mf(36, 3),
                mf(39, 1.5),
                mf(39, 2),
                mf(39, 3),
                mf(40, 1.5),
                mf(40, 2),
                mf(40, 3),
                mf(42, 1.5),
                mf(42, 2),
                mf(42, 3),
                mf(42, 4),
                mf(45, 1.5),
                mf(45, 2),
                mf(45, 3),
                mf(45, 4),
                mf(48, 1.5),
                mf(48, 2),
                mf(48, 3),
                mf(48, 4),
                mf(50, 1.5),
                mf(50, 2),
                mf(50, 3),
                mf(52, 1.5),
                mf(52, 2),
                mf(52, 3),
                mf(52, 4),
                mf(55, 1.5),
                mf(55, 2),
                mf(55, 3),
                mf(55, 4),
                mf(56, 1.5),
                mf(56, 2),
                mf(56, 3),
                mf(56, 4),
                mf(58, 1.5),
                mf(58, 2),
                mf(58, 3),
                mf(58, 4),
                mf(60, 1.5),
                mf(60, 2),
                mf(60, 3),
                mf(60, 4),
                mf(62, 1.5),
                mf(62, 2),
                mf(62, 3),
                mf(62, 4),
                mf(64, 1.5),
                mf(64, 2),
                mf(64, 3),
                mf(64, 4),
                mf(65, 1.5),
                mf(65, 2),
                mf(65, 3),
                mf(65, 4),
                mf(68, 1.5),
                mf(68, 2),
                mf(68, 3),
                mf(68, 4),
                mf(70, 1.5),
                mf(70, 2),
                mf(70, 3),
                mf(70, 4),
                mf(70, 6),
                mf(72, 1.5),
                mf(72, 2),
                mf(72, 3),
                mf(72, 4),
                mf(72, 6),
                mf(75, 1.5),
                mf(75, 2),
                mf(75, 3),
                mf(75, 4),
                mf(75, 6),
                nunc(1, 64),
                nunc(2, 56),
                nunc(3, 48),
                nunc(4, 40),
                nunc(5, 40),
                nunc(6, 32),
                nunc(8, 32),
                nunc(10, 24),
                nunc(12, 24),
                unc(Fraction(1, 4), 20),
                unc(Fraction(5, 16), 18),
                unc(Fraction(3, 8), 16),
                unc(Fraction(7, 16), 14),
                unc(Fraction(1, 2), 13),
                unc(Fraction(9, 16), 12),
                unc(Fraction(5, 8), 11),
                unc(Fraction(3, 4), 10),
                unc(Fraction(7, 8), 9),
                unc(Fraction(1), 8),
                unc(mixed(1, 1, 8), 7),
                unc(mixed(1, 1, 4), 7),
                unc(mixed(1, 3, 8), 6),
                unc(mixed(1, 3, 4), 5),
                unc(Fraction(2), 4.5),
                unc(mixed(2, 1, 4), 4.5),
                unc(mixed(2, 1, 2), 4),
                unc(mixed(2, 3, 4), 4),
                unc(Fraction(3), 4),
                unc(mixed(3, 1, 4), 4),
                unc(mixed(3, 1, 2), 4),
                unc(mixed(3, 3, 4), 4),
                unc(Fraction(4), 4),
                nunf(1, 64),
                nunf(2, 56),
                nunf(3, 48),
                nunf(4, 40),
                nunf(5, 40),
                nunf(6, 32),
                nunf(8, 32),
                nunf(10, 24),
                nunf(12, 24),
                unf(Fraction(1, 4), 20),
                unf(Fraction(5, 16), 18),
                unf(Fraction(3, 8), 16),
                unf(Fraction(7, 16), 14),
                unf(Fraction(1, 2), 20),
                unf(Fraction(9, 16), 12),
                unf(Fraction(5, 8), 11),
                unf(Fraction(3, 4), 10),
                unf(Fraction(7, 8), 9),
                unf(Fraction(1), 8),
                unf(mixed(1, 1, 8), 7),
                unf(mixed(1, 1, 4), 7),
                unf(mixed(1, 3, 8), 6),
                unf(mixed(1, 1, 2), 6),
                unf(mixed(1, 3, 4), 5),
                unf(Fraction(2), 4.5),
                unf(mixed(2, 1, 4), 4.5),
                unf(mixed(2, 1, 2), 4),
                unf(mixed(2, 3, 4), 4),
                unf(Fraction(3), 4),
                unf(mixed(3, 1, 4), 4),
                unf(mixed(3, 1, 2), 4),
                unf(mixed(3, 3, 4), 4),
                unf(Fraction(4), 4),
                nuns(10, 28),
                nuns(10, 36),
                nuns(10, 40),
                nuns(10, 48),
                nuns(10, 56),
                nuns(12, 36),
                nuns(12, 40),
                nuns(12, 48),
                nuns(12, 56),
                uns(Fraction(1, 4), 24),
                uns(Fraction(1, 4), 36),
                uns(Fraction(1, 4), 40),
                uns(Fraction(1, 4), 48),
                uns(Fraction(1, 4), 56),
                uns(Fraction(5, 16), 27),
                uns(Fraction(5, 16), 36),
                uns(Fraction(5, 16), 40),
                uns(Fraction(5, 16), 48),
                uns(Fraction(3, 8), 18),
                uns(Fraction(3, 8), 27),
                uns(Fraction(3, 8), 36),
                uns(Fraction(3, 8), 40),
                uns(Fraction(7, 16), 18),
                uns(Fraction(7, 16), 24),
                uns(Fraction(7, 16), 27),
                uns(Fraction(1, 2), 12),
                uns(Fraction(1, 2), 14),
                uns(Fraction(1, 2), 18),
                uns(Fraction(1, 2), 24),
                uns(Fraction(1, 2), 27),
                uns(Fraction(9, 16), 14),
                uns(Fraction(9, 16), 27),
                uns(Fraction(5, 8), 14),
                uns(Fraction(5, 8), 27),
                uns(Fraction(3, 4), 14),
                uns(Fraction(3, 4), 18),
                uns(Fraction(3, 4), 24),
                uns(Fraction(7, 8), 10),
                uns(Fraction(7, 8), 18),
                uns(Fraction(7, 8), 24),
                uns(Fraction(7, 8), 27),
                uns(mixed(1, 0, 1), 10),
                uns(mixed(1, 0, 1), 14),
                uns(mixed(1, 0, 1), 18),
                uns(mixed(1, 0, 1), 24),
                uns(mixed(1, 0, 1), 27),
                uns(mixed(1, 1, 8), 10),
                uns(mixed(1, 1, 8), 14),
                uns(mixed(1, 1, 8), 24),
                uns(mixed(1, 1, 4), 10),
                uns(mixed(1, 1, 4), 14),
                uns(mixed(1, 1, 4), 24),
                uns(mixed(1, 3, 8), 10),
                uns(mixed(1, 3, 8), 14),
                uns(mixed(1, 3, 8), 24),
                uns(mixed(1, 1, 2), 10),
                uns(mixed(1, 1, 2), 14),
                uns(mixed(1, 1, 2), 24),
                uns(mixed(1, 5, 8), 10),
                uns(mixed(1, 5, 8), 14),
                uns(mixed(1, 5, 8), 24),
                uns(mixed(1, 3, 4), 10),
                uns(mixed(1, 3, 4), 14),
                uns(mixed(1, 3, 4), 18),
                uns(mixed(1, 7, 8), 10),
                uns(mixed(1, 7, 8), 14),
                uns(mixed(1, 7, 8), 18),
                uns(Fraction(2), 10),
                uns(Fraction(2), 14),
                uns(Fraction(2), 18),
                uns(mixed(2, 1, 16), 16),
                uns(mixed(2, 3, 16), 16),
                uns(mixed(2, 1, 4), 10),
                uns(mixed(2, 1, 4), 14),
                uns(mixed(2, 1, 4), 18),
                uns(mixed(2, 5, 16), 16),
                uns(mixed(2, 7, 16), 16),
                uns(mixed(2, 1, 2), 10),
                uns(mixed(2, 1, 2), 14),
                uns(mixed(2, 1, 2), 18),
                uns(mixed(2, 3, 4), 10),
                uns(mixed(2, 3, 4), 14),
                uns(mixed(2, 3, 4), 18),
                uns(Fraction(3), 10),
                uns(Fraction(3), 14),
                uns(Fraction(3), 18),
                uns(mixed(3, 1, 4), 10),
                uns(mixed(3, 1, 4), 14),
                uns(mixed(3, 1, 4), 18),
                uns(mixed(3, 1, 2), 10),
                uns(mixed(3, 1, 2), 14),
                uns(mixed(3, 1, 2), 18),
                uns(mixed(3, 3, 4), 10),
                uns(mixed(3, 3, 4), 14),
                uns(mixed(3, 3, 4), 18),
                uns(Fraction(4), 10),
                uns(Fraction(4), 14),
                uns(mixed(4, 1, 4), 10),
                uns(mixed(4, 1, 4), 14),
                uns(mixed(4, 1, 2), 10),
                uns(mixed(4, 1, 2), 14),
                uns(mixed(5, 3, 4), 10),
                uns(mixed(5, 3, 4), 14),
                uns(Fraction(6), 10),
                uns(Fraction(6), 14),
            ]
        else:
            tmp_presets_data = presets
        tmp=[]
        for ii in range(0,len(tmp_presets_data)):
            tmp.extend(tmp_presets_data[ii][1:]) #strip out string, only include pitch and both minor diameters
        obj.presets_data = tmp
        preset_names=[]
        for td in tmp_presets_data:
            preset_name = td[0]
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


####################################################################################
# Create the PG (Panzergewinde / DIN 40430) 80 degree thread profile object

class ThreadProfileCreatePGObjectCommandClass(ThreadProfileCreateObjectCommandClass):
    """Create PG (Panzergewinde) thread profile command"""

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreatePGObject.svg') ,
            'MenuText': "&Create PG thread profile" ,
            'ToolTip' : "Create DIN 40430 Panzergewinde (PG) 80 degree ThreadProfile object"}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        doc.openTransaction("Create PG ThreadProfile")
        try:
            self.makePGThreadProfile()
        except Exception as e:
            FreeCAD.Console.PrintError(
                "ThreadProfile Error: Exception creating PG thread profile object.\n\n" +
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
                "This is a PG (DIN 40430) 80 degree thread profile",
                "for sweeping along a helix in either the",
                "Part or Part Design workbench.",
                "installation of the ThreadProfile workbench is required.",
]

    def makePGThreadProfile(self):
        # Preset format: [name, pitch, external_minor, internal_minor]
        # Sources: British Metrics PG chart + Sealcon catalog (major/pitch).
        # Profile: pitch=1, 80 deg included angle, trunc. height 0.48.
        # print_clearance: external slightly smaller for 3D-print fit (cf. Bottle).

        def pg(txt, major_ext, minor_int, tpi, print_clearance=0.15):
            pitch = 25.4 / float(tpi)
            internal_minor = float(minor_int)
            external_minor = float(minor_int) - float(print_clearance)
            return [txt, pitch, external_minor, internal_minor]

        pg_presets_data = [
            ["PG presets", 0, 0, 0],
            pg("PG 7", 12.50, 11.28, 20),
            pg("PG 9", 15.20, 13.86, 18),
            pg("PG 11", 18.60, 17.26, 18),
            pg("PG 13.5", 20.40, 19.06, 18),
            pg("PG 16", 22.50, 21.16, 18),
            pg("PG 21", 28.30, 26.78, 16),
            pg("PG 29", 37.00, 35.48, 16),
            pg("PG 36", 47.00, 45.48, 16),
            pg("PG 42", 54.00, 52.48, 16),
            pg("PG 48", 59.30, 57.78, 16),
        ]

        internal_pg_data = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.001643349639,0.003298562962,0.004953776285,0.006608989608,0.008264202931,0.009919416255,0.011574629578,0.013229842901,0.014885056224,0.016540269547,0.01819548287,0.019850696193,0.021505909516,0.023161122839,0.024816336162,0.026471549485,0.028126762808,0.029781976131,0.031437189454,0.033092402777,0.0347476161,0.036402829423,0.038058042746,0.039713256069,0.041368469392,0.043023682715,0.044678896039,0.046334109362,0.047989322685,0.049644536008,0.051299749331,0.052954962654,0.054610175977,0.0562653893,0.057920602623,0.059575815946,0.061231029269,0.062886242592,0.064541455915,0.066196669238,0.067851882561,0.069507095884,0.071162309207,0.07281752253,0.074472735853,0.076127949176,0.077783162499,0.079438375823,0.081093589146,0.082748802469,0.084404015792,0.086059229115,0.087714442438,0.089369655761,0.091024869084,0.092680082407,0.09433529573,0.095990509053,0.097645722376,0.099300935699,0.100956149022,0.102611362345,0.104266575668,0.105921788991,0.107577002314,0.109232215637,0.11088742896,0.112542642283,0.114197855606,0.11585306893,0.117508282253,0.119163495576,0.120818708899,0.122473922222,0.124129135545,0.125784348868,0.127439562191,0.129094775514,0.130749988837,0.13240520216,0.134060415483,0.135715628806,0.137370842129,0.139026055452,0.140681268775,0.142336482098,0.143991695421,0.145646908744,0.147302122067,0.14895733539,0.150612548714,0.152267762037,0.15392297536,0.155578188683,0.157233402006,0.158888615329,0.160543828652,0.162199041975,0.163854255298,0.165509468621,0.167164681944,0.168819895267,0.17047510859,0.172130321913,0.173785535236,0.175440748559,0.177095961882,0.178751175205,0.180406388528,0.182061601851,0.183716815174,0.185372028498,0.187027241821,0.188682455144,0.190337668467,0.19199288179,0.193648095113,0.195303308436,0.196958521759,0.198613735082,0.200268948405,0.201924161728,0.203579375051,0.205234588374,0.206889801697,0.20854501502,0.210200228343,0.211855441666,0.213510654989,0.215165868312,0.216821081635,0.218476294958,0.220131508282,0.221786721605,0.223441934928,0.225097148251,0.226752361574,0.228407574897,0.23006278822,0.231718001543,0.233373214866,0.235028428189,0.236683641512,0.238338854835,0.239994068158,0.241649281481,0.243304494804,0.244959708127,0.24661492145,0.248270134773,0.249925348096,0.251580561419,0.253235774742,0.254890988066,0.256546201389,0.258201414712,0.259856628035,0.261511841358,0.263167054681,0.264822268004,0.266477481327,0.26813269465,0.269787907973,0.271443121296,0.273098334619,0.274753547942,0.276408761265,0.278063974588,0.279719187911,0.281374401234,0.283029614557,0.28468482788,0.286340041203,0.287995254526,0.28965046785,0.291305681173,0.292960894496,0.294616107819,0.296271321142,0.297926534465,0.299581747788,0.301236961111,0.302892174434,0.304547387757,0.30620260108,0.307857814403,0.309513027726,0.311168241049,0.312823454372,0.314478667695,0.316133881018,0.317789094341,0.319444307664,0.321099520987,0.32275473431,0.324409947634,0.326065160957,0.32772037428,0.329375587603,0.331030800926,0.332686014249,0.334341227572,0.335996440895,0.337651654218,0.339306867541,0.340962080864,0.342617294187,0.34427250751,0.345927720833,0.347582934156,0.349238147479,0.350893360802,0.352548574125,0.354203787448,0.355859000771,0.357514214094,0.359169427418,0.360824640741,0.362479854064,0.364135067387,0.36579028071,0.367445494033,0.369100707356,0.370755920679,0.372411134002,0.374066347325,0.375721560648,0.377376773971,0.379031987294,0.380687200617,0.38234241394,0.383997627263,0.385652840586,0.387308053909,0.388963267232,0.390618480555,0.392273693878,0.393928907202,0.395584120525,0.397239333848,0.398894547171,0.400549760494,0.402204973817,0.40386018714,0.405515400463,0.407170613786,0.408825827109,0.410481040432,0.412136253755,0.413791467078,0.415446680401,0.417101893724,0.418757107047,0.42041232037,0.422067533693,0.423722747016,0.425377960339,0.427033173662,0.428688386986,0.430343600309,0.431998813632,0.433654026955,0.435309240278,0.436964453601,0.438619666924,0.440274880247,0.44193009357,0.443585306893,0.445240520216,0.446895733539,0.448550946862,0.450206160185,0.451861373508,0.453516586831,0.455171800154,0.456827013477,0.4584822268,0.460137440123,0.461792653446,0.46344786677,0.465103080093,0.466758293416,0.468413506739,0.470068720062,0.471723933385,0.473379146708,0.475034360031,0.476689573354,0.478344786677,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.478356650361,0.476701437038,0.475046223715,0.473391010392,0.471735797069,0.470080583745,0.468425370422,0.466770157099,0.465114943776,0.463459730453,0.46180451713,0.460149303807,0.458494090484,0.456838877161,0.455183663838,0.453528450515,0.451873237192,0.450218023869,0.448562810546,0.446907597223,0.4452523839,0.443597170577,0.441941957254,0.440286743931,0.438631530608,0.436976317285,0.435321103961,0.433665890638,0.432010677315,0.430355463992,0.428700250669,0.427045037346,0.425389824023,0.4237346107,0.422079397377,0.420424184054,0.418768970731,0.417113757408,0.415458544085,0.413803330762,0.412148117439,0.410492904116,0.408837690793,0.40718247747,0.405527264147,0.403872050824,0.402216837501,0.400561624177,0.398906410854,0.397251197531,0.395595984208,0.393940770885,0.392285557562,0.390630344239,0.388975130916,0.387319917593,0.38566470427,0.384009490947,0.382354277624,0.380699064301,0.379043850978,0.377388637655,0.375733424332,0.374078211009,0.372422997686,0.370767784363,0.36911257104,0.367457357717,0.365802144394,0.36414693107,0.362491717747,0.360836504424,0.359181291101,0.357526077778,0.355870864455,0.354215651132,0.352560437809,0.350905224486,0.349250011163,0.34759479784,0.345939584517,0.344284371194,0.342629157871,0.340973944548,0.339318731225,0.337663517902,0.336008304579,0.334353091256,0.332697877933,0.33104266461,0.329387451286,0.327732237963,0.32607702464,0.324421811317,0.322766597994,0.321111384671,0.319456171348,0.317800958025,0.316145744702,0.314490531379,0.312835318056,0.311180104733,0.30952489141,0.307869678087,0.306214464764,0.304559251441,0.302904038118,0.301248824795,0.299593611472,0.297938398149,0.296283184826,0.294627971502,0.292972758179,0.291317544856,0.289662331533,0.28800711821,0.286351904887,0.284696691564,0.283041478241,0.281386264918,0.279731051595,0.278075838272,0.276420624949,0.274765411626,0.273110198303,0.27145498498,0.269799771657,0.268144558334,0.266489345011,0.264834131688,0.263178918365,0.261523705042,0.259868491718,0.258213278395,0.256558065072,0.254902851749,0.253247638426,0.251592425103,0.24993721178,0.248281998457,0.246626785134,0.244971571811,0.243316358488,0.241661145165,0.240005931842,0.238350718519,0.236695505196,0.235040291873,0.23338507855,0.231729865227,0.230074651904,0.228419438581,0.226764225258,0.225109011934,0.223453798611,0.221798585288,0.220143371965,0.218488158642,0.216832945319,0.215177731996,0.213522518673,0.21186730535,0.210212092027,0.208556878704,0.206901665381,0.205246452058,0.203591238735,0.201936025412,0.200280812089,0.198625598766,0.196970385443,0.19531517212,0.193659958797,0.192004745474,0.19034953215,0.188694318827,0.187039105504,0.185383892181,0.183728678858,0.182073465535,0.180418252212,0.178763038889,0.177107825566,0.175452612243,0.17379739892,0.172142185597,0.170486972274,0.168831758951,0.167176545628,0.165521332305,0.163866118982,0.162210905659,0.160555692336,0.158900479013,0.15724526569,0.155590052366,0.153934839043,0.15227962572,0.150624412397,0.148969199074,0.147313985751,0.145658772428,0.144003559105,0.142348345782,0.140693132459,0.139037919136,0.137382705813,0.13572749249,0.134072279167,0.132417065844,0.130761852521,0.129106639198,0.127451425875,0.125796212552,0.124140999229,0.122485785906,0.120830572582,0.119175359259,0.117520145936,0.115864932613,0.11420971929,0.112554505967,0.110899292644,0.109244079321,0.107588865998,0.105933652675,0.104278439352,0.102623226029,0.100968012706,0.099312799383,0.09765758606,0.096002372737,0.094347159414,0.092691946091,0.091036732768,0.089381519445,0.087726306122,0.086071092798,0.084415879475,0.082760666152,0.081105452829,0.079450239506,0.077795026183,0.07613981286,0.074484599537,0.072829386214,0.071174172891,0.069518959568,0.067863746245,0.066208532922,0.064553319599,0.062898106276,0.061242892953,0.05958767963,0.057932466307,0.056277252984,0.054622039661,0.052966826338,0.051311613014,0.049656399691,0.048001186368,0.046345973045,0.044690759722,0.043035546399,0.041380333076,0.039725119753,0.03806990643,0.036414693107,0.034759479784,0.033104266461,0.031449053138,0.029793839815,0.028138626492,0.026483413169,0.024828199846,0.023172986523,0.0215177732,0.019862559877,0.018207346554,0.01655213323,0.014896919907,0.013241706584,0.011586493261,0.009931279938,0.008276066615,0.006620853292,0.004965639969,0.003310426646,0.001655213323]
        external_pg_data = [-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.018,-0.016295024749,-0.014577740927,-0.012860457104,-0.011143173281,-0.009425889459,-0.007708605636,-0.005991321813,-0.004274037991,-0.002556754168,-0.000839470345,0.000877813477,0.0025950973,0.004312381123,0.006029664945,0.007746948768,0.009464232591,0.011181516413,0.012898800236,0.014616084059,0.016333367881,0.018050651704,0.019767935527,0.021485219349,0.023202503172,0.024919786995,0.026637070817,0.02835435464,0.030071638463,0.031788922285,0.033506206108,0.035223489931,0.036940773753,0.038658057576,0.040375341399,0.042092625221,0.043809909044,0.045527192867,0.047244476689,0.048961760512,0.050679044335,0.052396328157,0.05411361198,0.055830895803,0.057548179625,0.059265463448,0.060982747271,0.062700031093,0.064417314916,0.066134598739,0.067851882561,0.069569166384,0.071286450206,0.073003734029,0.074721017852,0.076438301674,0.078155585497,0.07987286932,0.081590153142,0.083307436965,0.085024720788,0.08674200461,0.088459288433,0.090176572256,0.091893856078,0.093611139901,0.095328423724,0.097045707546,0.098762991369,0.100480275192,0.102197559014,0.103914842837,0.10563212666,0.107349410482,0.109066694305,0.110783978128,0.11250126195,0.114218545773,0.115935829596,0.117653113418,0.119370397241,0.121087681064,0.122804964886,0.124522248709,0.126239532532,0.127956816354,0.129674100177,0.131391384,0.133108667822,0.134825951645,0.136543235468,0.13826051929,0.139977803113,0.141695086936,0.143412370758,0.145129654581,0.146846938404,0.148564222226,0.150281506049,0.151998789872,0.153716073694,0.155433357517,0.15715064134,0.158867925162,0.160585208985,0.162302492808,0.16401977663,0.165737060453,0.167454344276,0.169171628098,0.170888911921,0.172606195744,0.174323479566,0.176040763389,0.177758047212,0.179475331034,0.181192614857,0.18290989868,0.184627182502,0.186344466325,0.188061750147,0.18977903397,0.191496317793,0.193213601615,0.194930885438,0.196648169261,0.198365453083,0.200082736906,0.201800020729,0.203517304551,0.205234588374,0.206951872197,0.208669156019,0.210386439842,0.212103723665,0.213821007487,0.21553829131,0.217255575133,0.218972858955,0.220690142778,0.222407426601,0.224124710423,0.225841994246,0.227559278069,0.229276561891,0.230993845714,0.232711129537,0.234428413359,0.236145697182,0.237862981005,0.239580264827,0.24129754865,0.243014832473,0.244732116295,0.246449400118,0.248166683941,0.249883967763,0.251601251586,0.253318535409,0.255035819231,0.256753103054,0.258470386877,0.260187670699,0.261904954522,0.263622238345,0.265339522167,0.26705680599,0.268774089813,0.270491373635,0.272208657458,0.273925941281,0.275643225103,0.277360508926,0.279077792749,0.280795076571,0.282512360394,0.284229644217,0.285946928039,0.287664211862,0.289381495685,0.291098779507,0.29281606333,0.294533347153,0.296250630975,0.297967914798,0.299685198621,0.301402482443,0.303119766266,0.304837050088,0.306554333911,0.308271617734,0.309988901556,0.311706185379,0.313423469202,0.315140753024,0.316858036847,0.31857532067,0.320292604492,0.322009888315,0.323727172138,0.32544445596,0.327161739783,0.328879023606,0.330596307428,0.332313591251,0.334030875074,0.335748158896,0.337465442719,0.339182726542,0.340900010364,0.342617294187,0.34433457801,0.346051861832,0.347769145655,0.349486429478,0.3512037133,0.352920997123,0.354638280946,0.356355564768,0.358072848591,0.359790132414,0.361507416236,0.363224700059,0.364941983882,0.366659267704,0.368376551527,0.37009383535,0.371811119172,0.373528402995,0.375245686818,0.37696297064,0.378680254463,0.380397538286,0.382114822108,0.383832105931,0.385549389754,0.387266673576,0.388983957399,0.390701241222,0.392418525044,0.394135808867,0.39585309269,0.397570376512,0.399287660335,0.401004944158,0.40272222798,0.404439511803,0.406156795626,0.407874079448,0.409591363271,0.411308647094,0.413025930916,0.414743214739,0.416460498562,0.418177782384,0.419895066207,0.421612350029,0.423329633852,0.425046917675,0.426764201497,0.42848148532,0.430198769143,0.431916052965,0.433633336788,0.435350620611,0.437067904433,0.438785188256,0.440502472079,0.442219755901,0.443937039724,0.445654323547,0.447371607369,0.449088891192,0.450806175015,0.452523458837,0.45424074266,0.455958026483,0.457675310305,0.459392594128,0.461109877951,0.462827161773,0.464544445596,0.466261729419,0.467979013241,0.469696297064,0.471413580887,0.473130864709,0.474848148532,0.476565432355,0.478282716177,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.48,0.478295024749,0.476577740927,0.474860457104,0.473143173281,0.471425889459,0.469708605636,0.467991321813,0.466274037991,0.464556754168,0.462839470345,0.461122186523,0.4594049027,0.457687618877,0.455970335055,0.454253051232,0.452535767409,0.450818483587,0.449101199764,0.447383915941,0.445666632119,0.443949348296,0.442232064473,0.440514780651,0.438797496828,0.437080213005,0.435362929183,0.43364564536,0.431928361537,0.430211077715,0.428493793892,0.426776510069,0.425059226247,0.423341942424,0.421624658601,0.419907374779,0.418190090956,0.416472807133,0.414755523311,0.413038239488,0.411320955665,0.409603671843,0.40788638802,0.406169104197,0.404451820375,0.402734536552,0.401017252729,0.399299968907,0.397582685084,0.395865401261,0.394148117439,0.392430833616,0.390713549794,0.388996265971,0.387278982148,0.385561698326,0.383844414503,0.38212713068,0.380409846858,0.378692563035,0.376975279212,0.37525799539,0.373540711567,0.371823427744,0.370106143922,0.368388860099,0.366671576276,0.364954292454,0.363237008631,0.361519724808,0.359802440986,0.358085157163,0.35636787334,0.354650589518,0.352933305695,0.351216021872,0.34949873805,0.347781454227,0.346064170404,0.344346886582,0.342629602759,0.340912318936,0.339195035114,0.337477751291,0.335760467468,0.334043183646,0.332325899823,0.330608616,0.328891332178,0.327174048355,0.325456764532,0.32373948071,0.322022196887,0.320304913064,0.318587629242,0.316870345419,0.315153061596,0.313435777774,0.311718493951,0.310001210128,0.308283926306,0.306566642483,0.30484935866,0.303132074838,0.301414791015,0.299697507192,0.29798022337,0.296262939547,0.294545655724,0.292828371902,0.291111088079,0.289393804256,0.287676520434,0.285959236611,0.284241952788,0.282524668966,0.280807385143,0.27909010132,0.277372817498,0.275655533675,0.273938249853,0.27222096603,0.270503682207,0.268786398385,0.267069114562,0.265351830739,0.263634546917,0.261917263094,0.260199979271,0.258482695449,0.256765411626,0.255048127803,0.253330843981,0.251613560158,0.249896276335,0.248178992513,0.24646170869,0.244744424867,0.243027141045,0.241309857222,0.239592573399,0.237875289577,0.236158005754,0.234440721931,0.232723438109,0.231006154286,0.229288870463,0.227571586641,0.225854302818,0.224137018995,0.222419735173,0.22070245135,0.218985167527,0.217267883705,0.215550599882,0.213833316059,0.212116032237,0.210398748414,0.208681464591,0.206964180769,0.205246896946,0.203529613123,0.201812329301,0.200095045478,0.198377761655,0.196660477833,0.19494319401,0.193225910187,0.191508626365,0.189791342542,0.188074058719,0.186356774897,0.184639491074,0.182922207251,0.181204923429,0.179487639606,0.177770355783,0.176053071961,0.174335788138,0.172618504315,0.170901220493,0.16918393667,0.167466652847,0.165749369025,0.164032085202,0.162314801379,0.160597517557,0.158880233734,0.157162949912,0.155445666089,0.153728382266,0.152011098444,0.150293814621,0.148576530798,0.146859246976,0.145141963153,0.14342467933,0.141707395508,0.139990111685,0.138272827862,0.13655554404,0.134838260217,0.133120976394,0.131403692572,0.129686408749,0.127969124926,0.126251841104,0.124534557281,0.122817273458,0.121099989636,0.119382705813,0.11766542199,0.115948138168,0.114230854345,0.112513570522,0.1107962867,0.109079002877,0.107361719054,0.105644435232,0.103927151409,0.102209867586,0.100492583764,0.098775299941,0.097058016118,0.095340732296,0.093623448473,0.09190616465,0.090188880828,0.088471597005,0.086754313182,0.08503702936,0.083319745537,0.081602461714,0.079885177892,0.078167894069,0.076450610246,0.074733326424,0.073016042601,0.071298758778,0.069581474956,0.067864191133,0.06614690731,0.064429623488,0.062712339665,0.060995055842,0.05927777202,0.057560488197,0.055843204374,0.054125920552,0.052408636729,0.050691352906,0.048974069084,0.047256785261,0.045539501438,0.043822217616,0.042104933793,0.040387649971,0.038670366148,0.036953082325,0.035235798503,0.03351851468,0.031801230857,0.030083947035,0.028366663212,0.026649379389,0.024932095567,0.023214811744,0.021497527921,0.019780244099,0.018062960276,0.016345676453,0.014628392631,0.012911108808,0.011193824985,0.009476541163,0.00775925734,0.006041973517,0.004324689695,0.002607405872,0.000890122049,-0.000827161773,-0.002544445596,-0.004261729419,-0.005979013241,-0.007696297064,-0.009413580887,-0.011130864709,-0.012848148532,-0.014565432355,-0.016282716177]

        # Default: PG 13.5 (common sensor / cable-gland size) -> index 4
        default = pg_presets_data[4]
        obj = super(ThreadProfileCreatePGObjectCommandClass, self).makeThreadProfile(
            name="PGThreadProfile",
            internal_data=internal_pg_data,
            external_data=external_pg_data,
            presets=pg_presets_data,
            minor_diameter=default[2],
            pitch=default[1],
            internal_or_external="External",
            thread_count=6,
            Quality=6,
        )
        if obj:
            obj.Presets = default[0]
            obj.Pitch = default[1]
            obj.MinorDiameter = default[2]
        return obj

#Gui.addCommand("ThreadProfileCreatePGObject", ThreadProfileCreatePGObjectCommandClass())

####################################################################################
# Create Whitworth (BSW/BSF) 55 degree rounded thread profile object

class ThreadProfileCreateBSWObjectCommandClass(ThreadProfileCreateObjectCommandClass):
    """Create Whitworth (BSW coarse / BSF fine) thread profile command"""

    def GetResources(self):
        return {'Pixmap'  : os.path.join( iconPath , 'CreateBSWObject.svg') ,
            'MenuText': "&Create Whitworth (BSW/BSF) thread profile" ,
            'ToolTip' : "Create Whitworth 55 degree rounded ThreadProfile (BSW + BSF presets)"}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        doc.openTransaction("Create Whitworth ThreadProfile")
        try:
            self.makeBSWThreadProfile()
        except Exception as e:
            FreeCAD.Console.PrintError(
                "ThreadProfile Error: Exception creating Whitworth thread profile object.\n\n" +
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
                "This is a Whitworth 55 degree rounded thread profile (BSW/BSF)",
                "for sweeping along a helix in either the",
                "Part or Part Design workbench.",
                "installation of the ThreadProfile workbench is required.",
]

    def makeBSWThreadProfile(self):
        # Preset format: [name, pitch_mm, external_minor_mm, internal_minor_mm]
        # Same Whitworth form for BSW (coarse) and BSF (fine):
        # minor = major - 2*h, h = (2/3)*H, H = P/(2*tan(27.5 deg)), h/P = 0.640327.
        # External minus 0.15 mm print clearance (cf. PG/Bottle).
        def whitworth_preset(name, major_in, tpi, print_clearance=0.15):
            major = float(major_in) * 25.4
            pitch = 25.4 / float(tpi)
            internal_minor = major - 2.0 * 0.640327375657 * pitch
            external_minor = internal_minor - float(print_clearance)
            return [name, pitch, external_minor, internal_minor]

        bsw_presets_data = [
            ["BSW Whitworth presets", 0, 0, 0],
            whitworth_preset("1/16 in - 60 BSW", Fraction(1, 16), 60),
            whitworth_preset("3/32 in - 48 BSW", Fraction(3, 32), 48),
            whitworth_preset("1/8 in - 40 BSW", Fraction(1, 8), 40),
            whitworth_preset("5/32 in - 32 BSW", Fraction(5, 32), 32),
            whitworth_preset("3/16 in - 24 BSW", Fraction(3, 16), 24),
            whitworth_preset("7/32 in - 24 BSW", Fraction(7, 32), 24),
            whitworth_preset("1/4 in - 20 BSW", Fraction(1, 4), 20),
            whitworth_preset("5/16 in - 18 BSW", Fraction(5, 16), 18),
            whitworth_preset("3/8 in - 16 BSW", Fraction(3, 8), 16),
            whitworth_preset("7/16 in - 14 BSW", Fraction(7, 16), 14),
            whitworth_preset("1/2 in - 12 BSW", Fraction(1, 2), 12),
            whitworth_preset("9/16 in - 12 BSW", Fraction(9, 16), 12),
            whitworth_preset("5/8 in - 11 BSW", Fraction(5, 8), 11),
            whitworth_preset("3/4 in - 10 BSW", Fraction(3, 4), 10),
            whitworth_preset("7/8 in - 9 BSW", Fraction(7, 8), 9),
            whitworth_preset("1 in - 8 BSW", Fraction(1, 1), 8),
            whitworth_preset("1 1/8 in - 7 BSW", Fraction(9, 8), 7),
            whitworth_preset("1 1/4 in - 7 BSW", Fraction(5, 4), 7),
            whitworth_preset("1 3/8 in - 6 BSW", Fraction(11, 8), 6),
            whitworth_preset("1 1/2 in - 6 BSW", Fraction(3, 2), 6),
            whitworth_preset("1 5/8 in - 5 BSW", Fraction(13, 8), 5),
            whitworth_preset("1 3/4 in - 5 BSW", Fraction(7, 4), 5),
            whitworth_preset("1 7/8 in - 4.5 BSW", Fraction(15, 8), 4.5),
            whitworth_preset("2 in - 4.5 BSW", Fraction(2, 1), 4.5),
            whitworth_preset("2 1/4 in - 4 BSW", Fraction(9, 4), 4),
            whitworth_preset("2 1/2 in - 4 BSW", Fraction(5, 2), 4),
            whitworth_preset("2 3/4 in - 3.5 BSW", Fraction(11, 4), 3.5),
            whitworth_preset("3 in - 3.5 BSW", Fraction(3, 1), 3.5),
            whitworth_preset("3 1/4 in - 3.5 BSW", Fraction(13, 4), 3.5),
            whitworth_preset("3 1/2 in - 3.5 BSW", Fraction(7, 2), 3.5),
            whitworth_preset("3 3/4 in - 3 BSW", Fraction(15, 4), 3),
            whitworth_preset("4 in - 3 BSW", Fraction(4, 1), 3),
            whitworth_preset("4 1/4 in - 2.875 BSW", Fraction(17, 4), 2.875),
            whitworth_preset("4 1/2 in - 2.875 BSW", Fraction(9, 2), 2.875),
            whitworth_preset("4 3/4 in - 2.75 BSW", Fraction(19, 4), 2.75),
            whitworth_preset("5 in - 2.75 BSW", Fraction(5, 1), 2.75),
            whitworth_preset("5 1/4 in - 2.625 BSW", Fraction(21, 4), 2.625),
            whitworth_preset("5 1/2 in - 2.625 BSW", Fraction(11, 2), 2.625),
            whitworth_preset("5 3/4 in - 2.5 BSW", Fraction(23, 4), 2.5),
            whitworth_preset("6 in - 2.5 BSW", Fraction(6, 1), 2.5),
            ["BSF Fine Whitworth presets", 0, 0, 0],
            whitworth_preset("3/16 in - 32 BSF", Fraction(3, 16), 32),
            whitworth_preset("7/32 in - 28 BSF", Fraction(7, 32), 28),
            whitworth_preset("1/4 in - 26 BSF", Fraction(1, 4), 26),
            whitworth_preset("9/32 in - 26 BSF", Fraction(9, 32), 26),
            whitworth_preset("5/16 in - 22 BSF", Fraction(5, 16), 22),
            whitworth_preset("3/8 in - 20 BSF", Fraction(3, 8), 20),
            whitworth_preset("7/16 in - 18 BSF", Fraction(7, 16), 18),
            whitworth_preset("1/2 in - 16 BSF", Fraction(1, 2), 16),
            whitworth_preset("9/16 in - 16 BSF", Fraction(9, 16), 16),
            whitworth_preset("5/8 in - 14 BSF", Fraction(5, 8), 14),
            whitworth_preset("11/16 in - 14 BSF", Fraction(11, 16), 14),
            whitworth_preset("3/4 in - 12 BSF", Fraction(3, 4), 12),
            whitworth_preset("13/16 in - 12 BSF", Fraction(13, 16), 12),
            whitworth_preset("7/8 in - 11 BSF", Fraction(7, 8), 11),
            whitworth_preset("1 in - 10 BSF", Fraction(1, 1), 10),
            whitworth_preset("1 1/8 in - 9 BSF", Fraction(9, 8), 9),
            whitworth_preset("1 1/4 in - 9 BSF", Fraction(5, 4), 9),
            whitworth_preset("1 3/8 in - 8 BSF", Fraction(11, 8), 8),
            whitworth_preset("1 1/2 in - 8 BSF", Fraction(3, 2), 8),
            whitworth_preset("1 5/8 in - 8 BSF", Fraction(13, 8), 8),
            whitworth_preset("1 3/4 in - 7 BSF", Fraction(7, 4), 7),
            whitworth_preset("2 in - 7 BSF", Fraction(2, 1), 7),
            whitworth_preset("2 1/4 in - 6 BSF", Fraction(9, 4), 6),
            whitworth_preset("2 1/2 in - 6 BSF", Fraction(5, 2), 6),
            whitworth_preset("2 3/4 in - 6 BSF", Fraction(11, 4), 6),
            whitworth_preset("3 in - 5 BSF", Fraction(3, 1), 5),
            whitworth_preset("3 1/4 in - 5 BSF", Fraction(13, 4), 5),
            whitworth_preset("3 1/2 in - 4.5 BSF", Fraction(7, 2), 4.5),
            whitworth_preset("3 3/4 in - 4.5 BSF", Fraction(15, 4), 4.5),
            whitworth_preset("4 in - 4.5 BSF", Fraction(4, 1), 4.5),
        ]

        internal_bsw_data = [7.0235e-06,2.8096156e-05,6.3224439e-05,0.000112419143,0.000175695404,0.000253072724,0.000344574997,0.000450230551,0.000570072189,0.000704137242,0.000852467625,0.001015109907,0.001192115384,0.001383540158,0.001589445235,0.001809896617,0.002044965415,0.002294727969,0.002559265971,0.00283866661,0.00313302272,0.003442432941,0.003767001897,0.004106840381,0.004462065559,0.004832801187,0.005219177845,0.005621333185,0.006039412204,0.006473567528,0.006923959724,0.007390757633,0.007874138727,0.008374289487,0.008891405824,0.009425693514,0.009977368677,0.01054665829,0.011133800739,0.011739046413,0.012362658348,0.013004912921,0.013666100597,0.014346526745,0.015046512514,0.015766395791,0.016506532234,0.017267296402,0.018049082983,0.018852308136,0.019677410952,0.020524855061,0.021395130387,0.02228875508,0.023206277642,0.024148279271,0.025115376448,0.02610822381,0.027127517335,0.028173997886,0.029248455166,0.03035173215,0.031484730046,0.032648413892,0.033843818866,0.035072057441,0.036334327518,0.037631921713,0.038966237992,0.040338791926,0.041751230845,0.043205350298,0.044703113271,0.046246672765,0.047838398482,0.049480908562,0.051177107608,0.052930232586,0.054743908702,0.05662221804,0.058569784724,0.060591881764,0.062694566739,0.064884856475,0.067170955378,0.069562559101,0.072071266405,0.074704860359,0.077372891091,0.080040921823,0.082708952555,0.085376983287,0.088045014019,0.090713044751,0.093381075483,0.096049106215,0.098717136947,0.101385167679,0.10405319841,0.106721229142,0.109389259874,0.112057290606,0.114725321338,0.11739335207,0.120061382802,0.122729413534,0.125397444266,0.128065474998,0.130733505729,0.133401536461,0.136069567193,0.138737597925,0.141405628657,0.144073659389,0.146741690121,0.149409720853,0.152077751585,0.154745782317,0.157413813049,0.16008184378,0.162749874512,0.165417905244,0.168085935976,0.170753966708,0.17342199744,0.176090028172,0.178758058904,0.181426089636,0.184094120368,0.186762151099,0.189430181831,0.192098212563,0.194766243295,0.197434274027,0.200102304759,0.202770335491,0.205438366223,0.208106396955,0.210774427687,0.213442458419,0.21611048915,0.218778519882,0.221446550614,0.224114581346,0.226782612078,0.22945064281,0.232118673542,0.234786704274,0.237454735006,0.240122765738,0.242790796469,0.245458827201,0.248126857933,0.250794888665,0.253462919397,0.256130950129,0.258798980861,0.261467011593,0.264135042325,0.266803073057,0.269471103788,0.27213913452,0.274807165252,0.277475195984,0.280143226716,0.282811257448,0.28547928818,0.288147318912,0.290815349644,0.293483380376,0.296151411108,0.298819441839,0.301487472571,0.304155503303,0.306823534035,0.309491564767,0.312159595499,0.314827626231,0.317495656963,0.320163687695,0.322831718427,0.325499749158,0.32816777989,0.330835810622,0.333503841354,0.336171872086,0.338839902818,0.34150793355,0.344175964282,0.346843995014,0.349512025746,0.352180056478,0.354848087209,0.357516117941,0.360184148673,0.362852179405,0.365520210137,0.368188240869,0.370856271601,0.373524302333,0.376192333065,0.378860363797,0.381528394528,0.38419642526,0.386864455992,0.389532486724,0.392200517456,0.394868548188,0.39753657892,0.400204609652,0.402872640384,0.405540671116,0.408208701848,0.410876732579,0.413544763311,0.416212794043,0.418880824775,0.421548855507,0.424216886239,0.426884916971,0.429552947703,0.432220978435,0.434889009167,0.437557039898,0.44022507063,0.442893101362,0.445561132094,0.448229162826,0.450897193558,0.45356522429,0.456233255022,0.458901285754,0.461569316486,0.464237347218,0.466905377949,0.469573408681,0.472241439413,0.474909470145,0.477577500877,0.480245531609,0.482913562341,0.485581593073,0.488249623805,0.490917654537,0.493585685268,0.496253716,0.498921746732,0.501589777464,0.504257808196,0.506925838928,0.50959386966,0.512261900392,0.514929931124,0.517597961856,0.520265992588,0.522934023319,0.525602054051,0.528270084783,0.530938115515,0.533606146247,0.536274176979,0.538942207711,0.541610238443,0.544278269175,0.546946299907,0.549614330638,0.55228236137,0.554950392102,0.557618422834,0.560286453566,0.562954484298,0.56562251503,0.568256109252,0.570764816556,0.573156420279,0.575442519182,0.577632808918,0.579735493893,0.581757590933,0.583705157617,0.585583466955,0.587397143071,0.589150268049,0.590846467095,0.592488977175,0.594080702892,0.595624262387,0.597122025359,0.598576144812,0.599988583731,0.601361137665,0.602695453944,0.603993048139,0.605255318216,0.606483556791,0.607678961765,0.608842645611,0.609975643507,0.611078920491,0.612153377771,0.613199858322,0.614219151847,0.615211999209,0.616179096386,0.617121098015,0.618038620577,0.618932245271,0.619802520596,0.620649964705,0.621475067521,0.622278292674,0.623060079256,0.623820843423,0.624560979866,0.625280863143,0.625980848912,0.62666127506,0.627322462736,0.627964717309,0.628588329244,0.629193574918,0.629780717367,0.63035000698,0.630901682143,0.631435969833,0.63195308617,0.632453236931,0.632936618024,0.633403415933,0.633853808129,0.634287963453,0.634706042472,0.635108197812,0.63549457447,0.635865310098,0.636220535276,0.63656037376,0.636884942716,0.637194352937,0.637488709047,0.637768109686,0.638032647688,0.638282410242,0.63851747904,0.638737930422,0.638943835499,0.639135260273,0.63931226575,0.639474908032,0.639623238415,0.639757303468,0.639877145106,0.63998280066,0.640074302933,0.640151680253,0.640214956514,0.640264151218,0.640299279501,0.640320352157,0.640327375657,0.640320352157,0.640299279501,0.640264151218,0.640214956514,0.640151680253,0.640074302933,0.63998280066,0.639877145106,0.639757303468,0.639623238415,0.639474908032,0.63931226575,0.639135260273,0.638943835499,0.638737930422,0.63851747904,0.638282410242,0.638032647688,0.637768109686,0.637488709047,0.637194352937,0.636884942716,0.63656037376,0.636220535276,0.635865310098,0.63549457447,0.635108197812,0.634706042472,0.634287963453,0.633853808129,0.633403415933,0.632936618024,0.632453236931,0.63195308617,0.631435969833,0.630901682143,0.63035000698,0.629780717367,0.629193574918,0.628588329244,0.627964717309,0.627322462736,0.62666127506,0.625980848912,0.625280863143,0.624560979866,0.623820843423,0.623060079256,0.622278292674,0.621475067521,0.620649964705,0.619802520596,0.618932245271,0.618038620577,0.617121098015,0.616179096386,0.615211999209,0.614219151847,0.613199858322,0.612153377771,0.611078920491,0.609975643507,0.608842645611,0.607678961765,0.606483556791,0.605255318216,0.603993048139,0.602695453944,0.601361137665,0.599988583731,0.598576144812,0.597122025359,0.595624262387,0.594080702892,0.592488977175,0.590846467095,0.589150268049,0.587397143071,0.585583466955,0.583705157617,0.581757590933,0.579735493893,0.577632808918,0.575442519182,0.573156420279,0.570764816556,0.568256109252,0.56562251503,0.562954484298,0.560286453566,0.557618422834,0.554950392102,0.55228236137,0.549614330638,0.546946299907,0.544278269175,0.541610238443,0.538942207711,0.536274176979,0.533606146247,0.530938115515,0.528270084783,0.525602054051,0.522934023319,0.520265992588,0.517597961856,0.514929931124,0.512261900392,0.50959386966,0.506925838928,0.504257808196,0.501589777464,0.498921746732,0.496253716,0.493585685268,0.490917654537,0.488249623805,0.485581593073,0.482913562341,0.480245531609,0.477577500877,0.474909470145,0.472241439413,0.469573408681,0.466905377949,0.464237347218,0.461569316486,0.458901285754,0.456233255022,0.45356522429,0.450897193558,0.448229162826,0.445561132094,0.442893101362,0.44022507063,0.437557039898,0.434889009167,0.432220978435,0.429552947703,0.426884916971,0.424216886239,0.421548855507,0.418880824775,0.416212794043,0.413544763311,0.410876732579,0.408208701848,0.405540671116,0.402872640384,0.400204609652,0.39753657892,0.394868548188,0.392200517456,0.389532486724,0.386864455992,0.38419642526,0.381528394528,0.378860363797,0.376192333065,0.373524302333,0.370856271601,0.368188240869,0.365520210137,0.362852179405,0.360184148673,0.357516117941,0.354848087209,0.352180056478,0.349512025746,0.346843995014,0.344175964282,0.34150793355,0.338839902818,0.336171872086,0.333503841354,0.330835810622,0.32816777989,0.325499749158,0.322831718427,0.320163687695,0.317495656963,0.314827626231,0.312159595499,0.309491564767,0.306823534035,0.304155503303,0.301487472571,0.298819441839,0.296151411108,0.293483380376,0.290815349644,0.288147318912,0.28547928818,0.282811257448,0.280143226716,0.277475195984,0.274807165252,0.27213913452,0.269471103788,0.266803073057,0.264135042325,0.261467011593,0.258798980861,0.256130950129,0.253462919397,0.250794888665,0.248126857933,0.245458827201,0.242790796469,0.240122765738,0.237454735006,0.234786704274,0.232118673542,0.22945064281,0.226782612078,0.224114581346,0.221446550614,0.218778519882,0.21611048915,0.213442458419,0.210774427687,0.208106396955,0.205438366223,0.202770335491,0.200102304759,0.197434274027,0.194766243295,0.192098212563,0.189430181831,0.186762151099,0.184094120368,0.181426089636,0.178758058904,0.176090028172,0.17342199744,0.170753966708,0.168085935976,0.165417905244,0.162749874512,0.16008184378,0.157413813049,0.154745782317,0.152077751585,0.149409720853,0.146741690121,0.144073659389,0.141405628657,0.138737597925,0.136069567193,0.133401536461,0.130733505729,0.128065474998,0.125397444266,0.122729413534,0.120061382802,0.11739335207,0.114725321338,0.112057290606,0.109389259874,0.106721229142,0.10405319841,0.101385167679,0.098717136947,0.096049106215,0.093381075483,0.090713044751,0.088045014019,0.085376983287,0.082708952555,0.080040921823,0.077372891091,0.074704860359,0.072071266405,0.069562559101,0.067170955378,0.064884856475,0.062694566739,0.060591881764,0.058569784724,0.05662221804,0.054743908702,0.052930232586,0.051177107608,0.049480908562,0.047838398482,0.046246672765,0.044703113271,0.043205350298,0.041751230845,0.040338791926,0.038966237992,0.037631921713,0.036334327518,0.035072057441,0.033843818866,0.032648413892,0.031484730046,0.03035173215,0.029248455166,0.028173997886,0.027127517335,0.02610822381,0.025115376448,0.024148279271,0.023206277642,0.02228875508,0.021395130387,0.020524855061,0.019677410952,0.018852308136,0.018049082983,0.017267296402,0.016506532234,0.015766395791,0.015046512514,0.014346526745,0.013666100597,0.013004912921,0.012362658348,0.011739046413,0.011133800739,0.01054665829,0.009977368677,0.009425693514,0.008891405824,0.008374289487,0.007874138727,0.007390757633,0.006923959724,0.006473567528,0.006039412204,0.005621333185,0.005219177845,0.004832801187,0.004462065559,0.004106840381,0.003767001897,0.003442432941,0.00313302272,0.00283866661,0.002559265971,0.002294727969,0.002044965415,0.001809896617,0.001589445235,0.001383540158,0.001192115384,0.001015109907,0.000852467625,0.000704137242,0.000570072189,0.000450230551,0.000344574997,0.000253072724,0.000175695404,0.000112419143,6.3224439e-05,2.8096156e-05,7.0235e-06]
        external_bsw_data = [-0.018,-0.017978334741,-0.017942218584,-0.017891640431,-0.017826584722,-0.017747031405,-0.017652955914,-0.017544329126,-0.017421117313,-0.017283282097,-0.017130780382,-0.01696356429,-0.016781581083,-0.016584773081,-0.016373077563,-0.016146426669,-0.015904747291,-0.01564796094,-0.015375983627,-0.015088725712,-0.014786091749,-0.014467980326,-0.014134283875,-0.013784888488,-0.013419673704,-0.013038512286,-0.012641269983,-0.012227805272,-0.011797969077,-0.011351604482,-0.010888546402,-0.01040862125,-0.009911646563,-0.009397430614,-0.008865771984,-0.00831645911,-0.007749269795,-0.007163970678,-0.006560316669,-0.005938050338,-0.005296901252,-0.004636585261,-0.003956803733,-0.00325724271,-0.002537572013,-0.001797444252,-0.001036493768,-0.000254335468,0.000549436436,0.001375249804,0.002223556078,0.003094831923,0.003989581043,0.004908336158,0.005851661196,0.006820153698,0.007814447483,0.008835215597,0.009883173591,0.010959083161,0.012063756219,0.013198059445,0.014362919392,0.015559328237,0.016788350267,0.018051129242,0.019348896749,0.020682981755,0.02205482154,0.023465974296,0.024918133678,0.026413145729,0.027953028639,0.029539995956,0.031176484021,0.032865184601,0.034609083983,0.036411510163,0.038276190293,0.040207321255,0.04220965721,0.044288619456,0.046450435923,0.048702320763,0.051052709106,0.053511569264,0.056090826179,0.058798481793,0.061541542612,0.064284603432,0.067027664251,0.069770725071,0.072513785891,0.07525684671,0.07799990753,0.080742968349,0.083486029169,0.086229089988,0.088972150807,0.091715211626,0.094458272446,0.097201333266,0.099944394085,0.102687454905,0.105430515724,0.108173576544,0.110916637363,0.113659698183,0.116402759001,0.119145819821,0.121888880641,0.12463194146,0.12737500228,0.130118063099,0.132861123919,0.135604184738,0.138347245558,0.141090306378,0.143833367197,0.146576428016,0.149319488835,0.152062549655,0.154805610474,0.157548671294,0.160291732113,0.163034792933,0.165777853753,0.168520914572,0.171263975392,0.17400703621,0.17675009703,0.179493157849,0.182236218669,0.184979279488,0.187722340308,0.190465401128,0.193208461947,0.195951522767,0.198694583586,0.201437644406,0.204180705224,0.206923766044,0.209666826863,0.212409887683,0.215152948503,0.217896009322,0.220639070142,0.223382130961,0.226125191781,0.2288682526,0.231611313419,0.234354374239,0.237097435058,0.239840495878,0.242583556697,0.245326617517,0.248069678336,0.250812739156,0.253555799975,0.256298860795,0.259041921614,0.261784982433,0.264528043253,0.267271104072,0.270014164892,0.272757225711,0.275500286531,0.27824334735,0.28098640817,0.28372946899,0.286472529809,0.289215590628,0.291958651447,0.294701712267,0.297444773086,0.300187833906,0.302930894725,0.305673955545,0.308417016365,0.311160077184,0.313903138004,0.316646198822,0.319389259642,0.322132320461,0.324875381281,0.327618442101,0.33036150292,0.33310456374,0.335847624559,0.338590685379,0.341333746198,0.344076807018,0.346819867836,0.349562928656,0.352305989476,0.355049050295,0.357792111115,0.360535171934,0.363278232754,0.366021293573,0.368764354393,0.371507415212,0.374250476031,0.376993536851,0.37973659767,0.38247965849,0.385222719309,0.387965780129,0.390708840948,0.393451901768,0.396194962587,0.398938023407,0.401681084227,0.404424145045,0.407167205865,0.409910266684,0.412653327504,0.415396388323,0.418139449143,0.420882509963,0.423625570782,0.426368631602,0.429111692421,0.43185475324,0.434597814059,0.437340874879,0.440083935698,0.442826996518,0.445570057338,0.448313118157,0.451056178977,0.453799239796,0.456542300616,0.459285361435,0.462028422254,0.464771483073,0.467514543893,0.470257604713,0.473000665532,0.475743726352,0.478486787171,0.481229847991,0.48397290881,0.48671596963,0.489459030448,0.492202091268,0.494945152088,0.497688212907,0.500431273727,0.503174334546,0.505917395366,0.508660456185,0.511403517005,0.514146577825,0.516889638644,0.519632699463,0.522375760282,0.525118821102,0.527861881921,0.530604942741,0.53334800356,0.53609106438,0.5388341252,0.541577186019,0.544320246839,0.547063307657,0.549806368477,0.552549429296,0.555292490116,0.558035550935,0.560778611755,0.563521672575,0.566229328464,0.568808585379,0.571267445537,0.57361783388,0.57586971872,0.578031535187,0.580110497433,0.582112833388,0.58404396435,0.58590864448,0.587711070659,0.589454970042,0.591143670622,0.592780158687,0.594367126004,0.595907008914,0.597402020965,0.598854180347,0.600265333103,0.601637172888,0.602971257894,0.604269025401,0.605531804376,0.606760826406,0.607957235251,0.609122095198,0.610256398424,0.611361071482,0.612436981052,0.613484939045,0.614505707159,0.615500000944,0.616468493447,0.617411818485,0.618330573601,0.61922532272,0.620096598565,0.620944904838,0.621770718207,0.622574490111,0.623356648411,0.624117598895,0.624857726656,0.625577397353,0.626276958376,0.626956739904,0.627617055894,0.628258204981,0.628880471312,0.62948412532,0.630069424438,0.630636613753,0.631185926627,0.631717585257,0.632231801207,0.632728775893,0.633208701045,0.633671759125,0.63411812372,0.634547959915,0.634961424626,0.635358666929,0.635739828346,0.636105043131,0.636454438518,0.636788134969,0.637106246392,0.637408880355,0.63769613827,0.637968115583,0.638224901934,0.638466581312,0.638693232206,0.638904927724,0.639101735726,0.639283718933,0.639450935025,0.639603436739,0.639741271956,0.639864483768,0.639973110557,0.640067186048,0.640146739365,0.640211795074,0.640262373227,0.640298489384,0.640320154643,0.640327375657,0.640320154643,0.640298489384,0.640262373227,0.640211795074,0.640146739365,0.640067186048,0.639973110557,0.639864483768,0.639741271956,0.639603436739,0.639450935025,0.639283718933,0.639101735726,0.638904927724,0.638693232206,0.638466581312,0.638224901934,0.637968115583,0.63769613827,0.637408880355,0.637106246392,0.636788134969,0.636454438518,0.636105043131,0.635739828346,0.635358666929,0.634961424626,0.634547959915,0.63411812372,0.633671759125,0.633208701045,0.632728775893,0.632231801207,0.631717585257,0.631185926627,0.630636613753,0.630069424438,0.62948412532,0.628880471312,0.628258204981,0.627617055894,0.626956739904,0.626276958376,0.625577397353,0.624857726656,0.624117598895,0.623356648411,0.622574490111,0.621770718207,0.620944904838,0.620096598565,0.61922532272,0.618330573601,0.617411818485,0.616468493447,0.615500000944,0.614505707159,0.613484939045,0.612436981052,0.611361071482,0.610256398424,0.609122095198,0.607957235251,0.606760826406,0.605531804376,0.604269025401,0.602971257894,0.601637172888,0.600265333103,0.598854180347,0.597402020965,0.595907008914,0.594367126004,0.592780158687,0.591143670622,0.589454970042,0.587711070659,0.58590864448,0.58404396435,0.582112833388,0.580110497433,0.578031535187,0.57586971872,0.57361783388,0.571267445537,0.568808585379,0.566229328464,0.563521672575,0.560778611755,0.558035550935,0.555292490116,0.552549429296,0.549806368477,0.547063307657,0.544320246839,0.541577186019,0.5388341252,0.53609106438,0.53334800356,0.530604942741,0.527861881921,0.525118821102,0.522375760282,0.519632699463,0.516889638644,0.514146577825,0.511403517005,0.508660456185,0.505917395366,0.503174334546,0.500431273727,0.497688212907,0.494945152088,0.492202091268,0.489459030448,0.48671596963,0.48397290881,0.481229847991,0.478486787171,0.475743726352,0.473000665532,0.470257604713,0.467514543893,0.464771483073,0.462028422254,0.459285361435,0.456542300616,0.453799239796,0.451056178977,0.448313118157,0.445570057338,0.442826996518,0.440083935698,0.437340874879,0.434597814059,0.43185475324,0.429111692421,0.426368631602,0.423625570782,0.420882509963,0.418139449143,0.415396388323,0.412653327504,0.409910266684,0.407167205865,0.404424145045,0.401681084227,0.398938023407,0.396194962587,0.393451901768,0.390708840948,0.387965780129,0.385222719309,0.38247965849,0.37973659767,0.376993536851,0.374250476031,0.371507415212,0.368764354393,0.366021293573,0.363278232754,0.360535171934,0.357792111115,0.355049050295,0.352305989476,0.349562928656,0.346819867836,0.344076807018,0.341333746198,0.338590685379,0.335847624559,0.33310456374,0.33036150292,0.327618442101,0.324875381281,0.322132320461,0.319389259642,0.316646198822,0.313903138004,0.311160077184,0.308417016365,0.305673955545,0.302930894725,0.300187833906,0.297444773086,0.294701712267,0.291958651447,0.289215590628,0.286472529809,0.28372946899,0.28098640817,0.27824334735,0.275500286531,0.272757225711,0.270014164892,0.267271104072,0.264528043253,0.261784982433,0.259041921614,0.256298860795,0.253555799975,0.250812739156,0.248069678336,0.245326617517,0.242583556697,0.239840495878,0.237097435058,0.234354374239,0.231611313419,0.2288682526,0.226125191781,0.223382130961,0.220639070142,0.217896009322,0.215152948503,0.212409887683,0.209666826863,0.206923766044,0.204180705224,0.201437644406,0.198694583586,0.195951522767,0.193208461947,0.190465401128,0.187722340308,0.184979279488,0.182236218669,0.179493157849,0.17675009703,0.17400703621,0.171263975392,0.168520914572,0.165777853753,0.163034792933,0.160291732113,0.157548671294,0.154805610474,0.152062549655,0.149319488835,0.146576428016,0.143833367197,0.141090306378,0.138347245558,0.135604184738,0.132861123919,0.130118063099,0.12737500228,0.12463194146,0.121888880641,0.119145819821,0.116402759001,0.113659698183,0.110916637363,0.108173576544,0.105430515724,0.102687454905,0.099944394085,0.097201333266,0.094458272446,0.091715211626,0.088972150807,0.086229089988,0.083486029169,0.080742968349,0.07799990753,0.07525684671,0.072513785891,0.069770725071,0.067027664251,0.064284603432,0.061541542612,0.058798481793,0.056090826179,0.053511569264,0.051052709106,0.048702320763,0.046450435923,0.044288619456,0.04220965721,0.040207321255,0.038276190293,0.036411510163,0.034609083983,0.032865184601,0.031176484021,0.029539995956,0.027953028639,0.026413145729,0.024918133678,0.023465974296,0.02205482154,0.020682981755,0.019348896749,0.018051129242,0.016788350267,0.015559328237,0.014362919392,0.013198059445,0.012063756219,0.010959083161,0.009883173591,0.008835215597,0.007814447483,0.006820153698,0.005851661196,0.004908336158,0.003989581043,0.003094831923,0.002223556078,0.001375249804,0.000549436436,-0.000254335468,-0.001036493768,-0.001797444252,-0.002537572013,-0.00325724271,-0.003956803733,-0.004636585261,-0.005296901252,-0.005938050338,-0.006560316669,-0.007163970678,-0.007749269795,-0.00831645911,-0.008865771984,-0.009397430614,-0.009911646563,-0.01040862125,-0.010888546402,-0.011351604482,-0.011797969077,-0.012227805272,-0.012641269983,-0.013038512286,-0.013419673704,-0.013784888488,-0.014134283875,-0.014467980326,-0.014786091749,-0.015088725712,-0.015375983627,-0.01564796094,-0.015904747291,-0.016146426669,-0.016373077563,-0.016584773081,-0.016781581083,-0.01696356429,-0.017130780382,-0.017283282097,-0.017421117313,-0.017544329126,-0.017652955914,-0.017747031405,-0.017826584722,-0.017891640431,-0.017942218584,-0.017978334741,-0.018]

        # Default: 1/4-20 BSW (common size; basic minor ~4.72 mm)
        default = bsw_presets_data[7]
        obj = super(ThreadProfileCreateBSWObjectCommandClass, self).makeThreadProfile(
            name="WhitworthThreadProfile",
            internal_data=internal_bsw_data,
            external_data=external_bsw_data,
            presets=bsw_presets_data,
            minor_diameter=default[2],
            pitch=default[1],
            internal_or_external="External",
            thread_count=6,
            Quality=6,
        )
        if obj:
            obj.Presets = default[0]
            obj.Pitch = default[1]
            obj.MinorDiameter = default[2]
        return obj

#Gui.addCommand("ThreadProfileCreateBSWObject", ThreadProfileCreateBSWObjectCommandClass())

####################################################################################
def initialize():
    if FreeCAD.GuiUp:
        Gui.addCommand("ThreadProfileCreateObject", ThreadProfileCreateObjectCommandClass())
        Gui.addCommand("ThreadProfileMakeHelix", ThreadProfileMakeHelixCommandClass())
        Gui.addCommand("ThreadProfileOpenOnlineCalculator", ThreadProfileOpenOnlineCalculatorCommandClass())
        Gui.addCommand("ThreadProfileCreateButtressObject", ThreadProfileCreateButtressObjectCommandClass())
        Gui.addCommand("ThreadProfileCreateBottleObject", ThreadProfileCreateBottleObjectCommandClass())
        Gui.addCommand("ThreadProfileCreatePGObject", ThreadProfileCreatePGObjectCommandClass())
        Gui.addCommand("ThreadProfileCreateBSWObject", ThreadProfileCreateBSWObjectCommandClass())
        Gui.addCommand("ThreadProfileDoSweep", ThreadProfileDoSweepCommandClass())
        Gui.addCommand("ThreadProfileSettings", ThreadProfileSettingsCommandClass())


initialize()
