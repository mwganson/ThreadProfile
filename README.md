# ThreadProfile Workbench
<img src="Resources/icons/ThreadProfileLogo.png" alt="icon">

## Toolbar Icon
Download the <a href = "https://github.com/mwganson/ThreadProfile/blob/master/Resources/icons/ThreadProfileSVGLogo.svg">SVG Toolbar Icon</a><br/>

## Installation
Can be installed via the AddonManager in Tools menu -> AddonManager if you have a very recent build.  Open the AddonManger.  Click the Configure icon.  Add this to the custom repositories section: https://github.com/mwganson/ThreadProfile  Close and restart the AddonManager.  You should now see ThreadProfile listed in the Workbench tab.
<br/>
## Overview
Use the 2d profile object created with this workbench to create threads by sweeping it along a helix of the appropriate height and pitch.  It is compatible for use in both the Part and Part Design workbenches in FreeCAD.  To use in Part Design if there is an active body the ThreadProfile object will be created inside the body.  Then select the ThreadProfile object and click the Make Helix toolbar icon to create a helix.  A new shapebinder will be created linking the helix, and the helix will be hidden.  You can then sweep it as you would a sketch using either the Additive Pipe (for external threads) or the Subtractive Pipe (for internal threads).  In Part workbench you would use the Sweep tool, which would then need to be cut (if an internal thread) from a suitable object, such as an extruded hexagon.<br/>
<br/>
## Advantages
There are a number of advantages to using ThreadProfile objects in your threads:<br/>
<br/>
* It's quicker and easier than sketching your own traditional thread profile.<br/>
* It's possible to make custom threads of any desired diameter and pitch, including ANSI, such as 1/4" 20 TPI.<br/>
* All of the threads I've made so far in testing have passed Check Geometry with BOP Check enabled.<br/>

## Details
The ThreadProfile object is really just a glorified rebranded Draft BSpline object.  In fact, the template code for producing it was unabashedly copied directly from the Draft workbench for use as a starting point, which I then modified to meet my needs.  In particular, the necessary properties, such as Pitch and Minor Diameter were added, along with the code necessary to produce the desired BSpline object.<br/>

## Create Object Command
<img src="https://github.com/mwganson/ThreadProfile/blob/master/Resources/icons/CreateObject.png" alt="create object"><br/>
This creates the ThreadProfile object with default properties.  Create it first, and then set the desired properties in the data tab of the combo view.  If there is an active Part Design Body, the object will be placed inside it.  Failing that, if there is an active Part container the object will be placed into that.

## Make Helix Command
<img src="https://github.com/mwganson/ThreadProfile/blob/master/Resources/icons/MakeHelix.png" alt="make helix"><br/>
The Make Helix command creates a Helix and sets its Pitch property to match the Pitch property of the ThreadProfile object.  This property is linked parametrically, thus any change to the ThreadProfile.Pitch property will also cause the Helix.Pitch property to update itself.  We also set the Helix.Height property to ThreadProfile.Pitch * ThreadProfile.ThreadCount, thus ensuring the Helix.Height property is such that the thread produced in the sweep will have Thread Count threads.  This is also parametrically linked.  Another thing that is done is the Helix.Placement property is copied from the ThreadProfile.Placement, thus the Helix, when created, will be positioned with the ThreadProfile object.  As of version 1.31 this placement property is now parametrically linked.  There is a settings option to change this to only put the Helix where the ThreadProfile is on creation of the helix.<br/>
<br/>
If there exists an active Part Design body when the helix is created, then a shapebinder will be created and placed in the active body, and the helix will be hidden.<br/>

## Open Online Calculator Command
<img src="https://github.com/mwganson/ThreadProfile/blob/master/Resources/icons/OpenOnlineCalculator.png" alt="open online calculator"><br/>
Opens on online calculator either for the metric sizes or for the ANSI UN and UNR inch sizes in the default browser.  It is possible (I think) that FreeCAD might not have permission to do this.  If so, then it will likely fail.  Use the calculator to get the minor diameter for the thread you wish to make.  For inch sizes, the 2A and 2B tolerances are for the normal fit.  For metric sizes the 6g tolerance is for normal fit.  Typically there will be 2 minor diameters to select from: a minimum and a maximum.  If you make the internal thread a little bit smaller the fit will be tighter.  If you make the external thread a little bit smaller the fit will be looser.  A good way to check the fit is to make the nut and the screw at the same time, then use the Part workbench cross-section tool to check the fit.

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
This is the version of the ThreadProfile workbench used to create the ThreadProfile object, not the version of the ThreadProfile workbench currently installed.<br/>
## Thread Count
When a Helix is created using the Make Helix command the Height property of the Helix is set to a height such that Thread Count number of threads will be created.
## Presets
These are some presets I added to version 1.30 (likely to be expanded some in future versions).  I'm not entirely sure how accurate the data is.  Do not blindly rely on it.  You should still lookup the minimum and maximum minor diamters for your desired fit tolerance.  If you are
modeling both the internal and the external threads for a project it is a good idea to take cross sections of both so you can inspect the fit on the screen.<br/>

## FAQ
* Why is there a line running up the thread?<br/>
** There are actually 2 lines.  One is is the BSpline's seamline.  If you Pad / Extrude the profile you can see this seamline as a straight edge, similar to what you see in cylinders and extruded / padded circles.
The other is a set of concentric rings and I have no idea what they are or how they got there.<br/>
* Is it possible to access this via Python scripting?<br/>
** Yes.  Use:<br/>
<br/>
import ThreadProfileCmd<br/>
ThreadProfileCmd.makeThreadProfile()<br/>
<br/>
These parameters are currently (subject to change) supported: minor_diameter=4.891,pitch=1,closed=True,placement=None,face=None,support=None,internal_or_external="External",internal_data=[],external_data=[], thread_count=10.  (But I think face will always be true.)<br/>
<br/>
The internal_data and external_data list properties define the radius of the ThreadProfile object at the various angles around the circumference.  There are 720 points.  Each point is the x-coordinate of a thread profile sketched on the xz plane. The first element in the list is the x-coordinate at z=1/720 degrees, then z=2/720 degrees, etc.  Don't worry, you don't need to include these parameters.  The default used is for the standard Metric M profile.  When the ThreadProfile is created the data points are used as such: each element is taken, then added to it the minor radius + pitch * element value for the x-coordinate.  To get the y-coordinate we use the current element index / 720.  We use the math.cos() and math.sin() functions, but let's not get too bogged down here.  You can view the source code for more details.<br/>

#### Release notes:<br/>
* 2019.07.27 (version 1.31)<br/>
** Helix placement now linked parametrically to ThreadProfile placement, can be disabled in settings.
* 2019.07.25 (version 1.30)<br/>
** Added presets
** Changed variable to reflect there are 719 (not 720) points used to make the ThreadProfile BSpline
* 2019.07.23 (version 1.23)<br/>
** If there is an active part design body when the helix is created, make a shapebinder for it and hide the helix
** Put the helix into the active Part container if one exists
* 2019.07.23 (version 1.22)<br/>
** If there is an active part design body or Part object, add the thread profile to it.
* 2019.07.23 (version 1.21)<br/>
** Change Pitch type from Float to Length
** Check if Gui is up before creating view object
** Recompute document before returning object from makeThreadProfile()
** Fix bug where if more than one helix is made we set the correct helix properties
* 2019.07.22 (version 1.20)<br/>
** Add link to online calculators<br/>
* 2019.07.22 (version 1.10)<br/>
** Add Make Helix command<br/>
** Add Thread Count property<br/>
* 2019.07.22 (version 1.0)<br/>
** initial release<br/>
