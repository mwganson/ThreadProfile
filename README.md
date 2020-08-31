# ThreadProfile Workbench
<img src="Resources/icons/ThreadProfileLogo.svg" alt="icon">

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

## Create V thread profile Command
<img src="https://github.com/mwganson/ThreadProfile/blob/master/Resources/icons/CreateObject.svg" alt="create object"><br/>
This creates the V thread ThreadProfile object with default properties.  Create it first, and then set the desired properties in the data tab of the combo view.  There are a number of presets available, but you should double-check these by taking a cross-section of both parts to check the fit, then adjust the minor diameter accordingly.  If there is an active Part Design Body, the object will be placed inside it.  Failing that, if there is an active Part container the object will be placed into that.

## Create Buttress thread profile Command
<img src="https://github.com/mwganson/ThreadProfile/blob/master/Resources/icons/CreateButtressObject.svg" alt="create object"><br/>
This creates the Buttress thread ThreadProfile object with default properties.  Create it first, and then set the desired properties in the data tab of the combo view.  If there is an active Part Design Body, the object will be placed inside it.  Failing that, if there is an active Part container the object will be placed into that.<br/>
<br/>
These are ANSI B1.9-1973 (R2007), Class 2 -- Standard Grade,  7 degree / 45 degree flat-rooted buttress threads.  (Class 3 -- Precision Grade would have 2/3 the tolerance of these for a tighter fit.)  The tolerance is based on a thread length engagement of 10 threads.  Shorter engagements could use a tighter fit and still work, longer engagements might require more tolerance.  You can adjust the tolerance by adjusting the minor diameter after selecting one of the presets.  Make the external minor diameter larger and the internal minor diameter smaller if you want a tighter fit, and vice versa for a looser fit.<br/>
<br/>
There are other diameter / pitch combinations in the standard than are provided in the presets.  The ones provided are only the recommended combinations.  You can set the minor diameter and pitch to any values you want, but you'll need to work out the tolerances for yourself.<br/>

## Create Bottle thread profile Command
<img src="https://github.com/mwganson/ThreadProfile/blob/master/Resources/icons/CreateBottleObject.png" alt="create bottle object"><br/>
This creates a bottle thread object (SP4xx M type) 45 degree / 10 degree buttress thread.<br/>

## Make Helix Command
<img src="https://github.com/mwganson/ThreadProfile/blob/master/Resources/icons/MakeHelix.svg" alt="make helix"><br/>
The Make Helix command creates a Helix and sets its Pitch property to match the Pitch property of the ThreadProfile object.  This property is linked parametrically, thus any change to the ThreadProfile.Pitch property will also cause the Helix.Pitch property to update itself.  We also set the Helix.Height property to ThreadProfile.Pitch * ThreadProfile.ThreadCount, thus ensuring the Helix.Height property is such that the thread produced in the sweep will have Thread Count threads.  This is also parametrically linked.  Another thing that is done is the Helix.Placement property is copied from the ThreadProfile.Placement, thus the Helix, when created, will be positioned with the ThreadProfile object.  As of version 1.31 this placement property is now parametrically linked.  There is a settings option to change this to only put the Helix where the ThreadProfile is on creation of the helix.<br/>
<br/>
If there exists an active Part Design body when the helix is created, then a shapebinder will be created and placed in the active body, and the helix will be hidden.<br/>

## Do Sweep Command
<img src="https://github.com/mwganson/ThreadProfile/blob/master/Resources/icons/DoSweep.svg" alt="do sweep"><br/>
The Do Sweep command will perform the sweep for you.  To use it you must first select the ThreadProfile object to sweep and the helix (or ShapeBinder) to sweep it along, then activate the command either from the toolbar or menu.<br/>
<br/>
If a helix is selected, then the operation performed is a Part workbench Sweep, with solid = True and Frenet = True.  This happens even if there is an active body and even if the ThreadProfile object is in the active body.  If there is an active body and the ShapeBinder is selected, then an AdditivePipe is performed unless the InternalOrExternal property is set to "Internal", in which case the Part Design Subtractive Sweep is used.<br/>
<br/>
Be wary of coplanar issues when cutting internal threads out of existing material.  If the Cut (or SubtractivePipe) seems to have failed it could be because of the issues FreeCAD has with coplanar boolean operations.  The solution for this is to move either the base object or the cutting tool slightly.<br/>


## Open Online Calculator Command
<img src="https://github.com/mwganson/ThreadProfile/blob/master/Resources/icons/OpenOnlineCalculator.svg" alt="open online calculator"><br/>
Opens on online calculator for the metric sizes or for the ANSI UN and UNR inch sizes or for the ANSI Buttress sizes in the default browser.  It is possible (I think) that FreeCAD might not have permission to do this.  If so, then it will likely fail.  Use the calculator to get the minor diameter for the thread you wish to make.  For inch sizes, the 2A and 2B tolerances are for the normal fit.  For Buttress threads class 2 is normal, class 3 is tighter fit.  For metric size v threads the 6g tolerance is for normal fit.  Typically there will be 2 minor diameters to select from: a minimum and a maximum.  If you make the internal thread a little bit smaller the fit will be tighter.  If you make the external thread a little bit smaller the fit will be looser.  A good way to check the fit is to make the nut and the screw at the same time, then use the Part workbench cross-section tool to check the fit.

## Quality Property
The ThreadProfile object appears at first glance to be a simple circle, but it's not.  As mentioned above, it's a BSpline.  Think of it as a circle with a varying radius around the circumference.  For every degree there are 2 points used to define the curve, 720 points in all.  This is for Quality 1 profiles.  You can select a different Quality property for improved performance, but at the expense of lower quality profiles.  Quality 2 profiles use only every other point, in other words 360 points or 1 point per degree.  Quality 3 uses only every 3rd point, and so on, up to 12 Quality settings at this time (subject to change).<br/>
<br/>

## Pitch Property
This is the pitch for the thread.  You also need to set this in the Helix Pitch property.  If you wish to make ANSI threads, such as 1/4-20, for example, you would set this value to 25.4/20 if you are in mm units or 1/20 if you are using inch units.  I keep FreeCAD in mm units, so I would use 25.4/20 for the Pitch for that thread.<br/>

## Minor Diameter
This is the minor diameter of your thread.  This is *NOT* the nominal diameter.  You need to look this value up and use the one for your desired nominal diameter, pitch, and fit tolerance.  Here are links to online calculators for <a href="https://www.amesweb.info/Screws/AsmeUnifiedInchScrewThread.aspx">Unified Inch Screwthreads</a>, <a href="https://www.amesweb.info/Screws/IsoMetricScrewThread.aspx">Metric</a>, and for <a href="https://www.amesweb.info/Screws/ButtressInchScrewThreads.aspx">ANSI Buttress</a><br/>

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
** There are actually multiple lines.  One is is the BSpline's seamline.  If you Pad / Extrude the profile you can see this seamline as a straight edge, similar to what you see in cylinders and extruded / padded circles.  The others are the seamlines from the helix.
<br/>
* My internal threads are always external.  What am I doing wrong?<br/>
** Use subtractive pipe in Part design to cut the internal thread out of an existing shape, e.g. a Pad.  In Part workbench use the Sweep object as a cutting tool to cut it out of an existing shape, e.g. an extruded hexagon.  (Ensure you have selected "Internal" in the "Internal Or External" ThreadProfile property when making internal threads.)<br/>
* Is it possible to access this via Python scripting?<br/>
** Yes.  Use:<br/>
<br/>
<pre>
import ThreadProfileCmd
ThreadProfileCmd.ThreadProfileCreateObjectCommandClass().makeThreadProfile()
or
ThreadProfileCmd.ThreadProfileCreateButtressObjectCommandClass().makeButtressThreadProfile()
</pre>
<br/>
Parameters: <br/>
name="BThreadProfile",internal_data = internal_buttress_data, external_data = external_buttress_data, presets = buttress_presets_data,minor_diameter=buttress_presets_data[13][2],pitch=25.4/10,internal_or_external="External",thread_count=10<br/>
name is the name of the ThreadProfile object created.<br/>
internal_data, external_data, presets are lists that could be used to create a custom profile type.<br/>
minor_diameter is the minor diameter (we don't use nominal, only minor).  To calculate minor diameter this code is used:<br/>
<br/><pre>
        def cd(txt, tpi, nominal): #cd = calculate diameters
            pitch = 25.4/tpi
            length_of_engagement = 10 * pitch #10 * pitch, longer engagements should have more tolerance
            nom = nominal * 25.4
            minor = nom - 0.66271 * pitch
            tolerance = 0.002 * (nom)**(1/3) + .00278 * length_of_engagement**(1/2) + 0.00854 * pitch**(1/2)
            return[txt, pitch, minor - tolerance, minor + tolerance]
</pre>
<br/>
The internal_data and external_data list properties define the radius of the ThreadProfile object at the various angles around the circumference.  There are 720 points.  Each point is the x-coordinate of a thread profile sketched on the xz plane. The first element in the list is the x-coordinate at z=1/720 degrees, then z=2/720 degrees, etc.  Don't worry, you don't need to include these parameters.  The default used is for the standard Metric M profile.  When the ThreadProfile is created the data points are used as such: each element is taken, then added to it the minor radius + pitch * element value for the x-coordinate.  To get the y-coordinate we use the current element index / 720.  We use the math.cos() and math.sin() functions, but let's not get too bogged down here.  You can view the source code for more details.<br/>


#### Release notes:<br/>
* 2020.08.27 (version 1.66)<br/>
** fix bug in ThreadCount property not updating Sweep object
** fix bug in PartDesign where sometimes Part Sweep was used even if there was active body
* 2020.08.04 (version 1.65)<br/>
** switch to svg icons
* 2020.07.30 (version 1.64)<br/>
** make subtractive pipe visible in dialog for external threads
* 2020.07.16 (version 1.63)<br/>
** maintenance update to fix error related to recent FreeCAD update
* 2020.07.16 (version 1.62)<br/>
** fix bug where only shell was being created
** make external bottle threads 0.25mm smaller minor diameter
* 2020.07.16 (version 1.61)<br/>
** improve continuity of bspline to C3 (was C2)
** should improve quality of finished sweep object
* 2020.07.15 (version 1.60)<br/>
** add bottle thread buttress (SP4xx M type) 45/10 degree thread support
* 2019.08.22 (version 1.51)<br/>
** fix spelling errors
* 2019.08.02 (version 1.50)<br/>
** Add sweep tool
* 2019.08.01 (version 1.42)<br/>
** Fix python2 bug related to creating buttress threads
** Fix bug in presets
* 2019.08.01 (version 1.41)<br/>
** Fix bug where presets were not working after restarting and reloading file
* 2019.07.31 (version 1.41)<br/>
** Add online buttress calculator link<br/>
* 2019.07.31 (version 1.40)<br/>
** Add Buttress thread support
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
