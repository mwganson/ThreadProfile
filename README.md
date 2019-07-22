# ThreadProfile Workbench
<img src="Resources/icons/ThreadProfileLogo.png" alt="icon">

## Toolbar Icon
Download the <a href = "https://github.com/mwganson/ThreadProfile/blob/master/Resources/icons/ThreadProfileSVGLogo.svg">SVG Toolbar Icon</a><br/>

## Installation
Install via the Addon Manager in the Tools menu in FreeCAD version 0.17 and later.<br/>
<br/>
## Overview
Use the 2d profile object created with this workbench to create threads by sweeping it along a helix of the appropriate height and pitch.  It is compatible for use in both the Part and Part Design workbenches in FreeCAD.  To use in Part Design, simply drag and drop the ThreadProfile object into your Body object just as you would a sketch.  You can then sweep it as you would a sketch using either the Additive Pipe (for external threads) or the Subtractive Pipe (for internal threads).  In Part workbench you would use the Sweep tool, which would then need to be cut (if an internal thread) from a suitable object, such as an extruded hexagon.<br/>
<br/>
## Advantages
There are a number of advantages to using ThreadProfile objects in your threads:<br/>
<br/>
* It's quicker and easier than sketching your own traditional thread profile.<br/>
* It's possible to make custom threads of any desired diameter and pitch, including ANSI, such as 1/4" 20 TPI.<br/>
* All of the threads I've made so far in testing have passed Check Geometry with BOP Check enabled.<br/>

## Details
The ThreadProfile object is really just a glorified rebranded Draft BSpline object.  In fact, the template code for producing it was unabashedly copied directly from the Draft workbench for use as a starting point, which I then modified to meet my needs.  In particular, the necessary properties, such as Pitch and Minor Diameter were added, along with the code necessary to produce the desired BSpline object.<br/>

## Quality Property
The ThreadProfile object appears at first glance to be a simple circle, but it's not.  As mentioned above, it's a BSpline.  Think of it as a circle with a varying radius around the circumference.  For every degree there are 2 points used to define the curve, 720 points in all.  This is for Quality 1 profiles.  You can select a different Quality property for improved performance, but at the expense of lower quality profiles.  Quality 2 profiles use only every other point, in other words 360 points or 1 point per degree.  Quality 3 uses only every 3rd point, and so on, up to 12 Quality settings at this time (subject to change).<br/>
<br/>

## Pitch Property
This is the pitch for the thread.  You also need to set this in the Helix Pitch property.  If you wish to make ANSI threads, such as 1/4-20, for example, you would set this value to 25.4/20 if you are in mm units or 1/20 if you are using inch units.  I keep FreeCAD in mm units, so I would use 25.4/20 for the Pitch for that thread.<br/>

## Minor Diameter
This is the minor diameter of your thread.  This is *NOT* the nominal diameter.  You need to look this value up and use the one for your desired nominal diameter, pitch, and fit tolerance.  Here are links to online calculators for <a href="https://www.amesweb.info/Screws/AsmeUnifiedInchScrewThread.aspx">Unified Inch Screwthreads</a> and for <a href="https://www.amesweb.info/Screws/IsoMetricScrewThread.aspx">Metric</a>.<br/>  Note: the profile is for metric threads, but it's basically the same as the one for ANSI threads, only difference being the root is rounded in metric threads, which IMO is not a concern.<br/>
## Continuity
What is this?  This is a property of the underlying BSpline object.  This is readonly and is only included for informational purposes.  Normally, this should be C2 continuity.  You can read more about smoothness <a href="https://en.wikipedia.org/wiki/Smoothness">here</a>.<br/>
## Version
This is the version of the ThreadProfile workbench used to create the ThreadProfile object, not the version of the ThreadProfile workbench currently installed.

## FAQ
* Why is there a line running up the thread?<br/>
** This is the BSpline's seamline.  If you Pad / Extrude the profile you can see this seamline as a straight edge, similar to what you see in cylinders and extruded / padded circles.<br/>
* Is it possible to access this via Python scripting?<br/>
** Yes.  Use import ThreadProfileCmd, then ThreadProfileCmd.makeThreadProfile().  These parameters are currently (subject to change) supported: minor_diameter=4.891,pitch=1,closed=True,placement=None,face=None,support=None,internal_or_external="External",internal_data=[],external_data=[].  (But I think face will always be true.)<br/>
The internal_data and external_data list properties define the radius of the ThreadProfile object at the various angles around the circumference.  There are 720 points.  Each point is the x-coordinate of a thread profile sketched on the xz plane. The first element in the list is the x-coordinate at z=1/720 degrees, then z=2/720 degrees, etc.  Don't worry, you don't need to include these parameters.  The default used is for the standard Metric M profile.  When the ThreadProfile is created the data points are used as such: each element is taken, then added to it the minor radius + pitch * element value for the x-coordinate.  To get the y-coordinate we use the current element index / 720.  We use the math.cos() and math.sin() functions, but let's not get too bogged down here.  You can view the source code for more details.<br/>

#### Release notes:<br/>
* 2019.07.22 (version 1.0)<br/>
** initial release<br/>
