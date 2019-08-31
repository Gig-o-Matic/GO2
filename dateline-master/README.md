Dateline
========

**Dateline** is a jQuery UI widget for date-related data. You can create interactive timelines, which can be dragged by mouse, touch or keyboard, and displays events. The movements of two or more timelines ('bands') are synchronized. Clicking on an event displays more information or redirects you to another page.

A demo of **Dateline** is [here](http://www.sjaakpriester.nl/software/dateline).

Here is **Dateline**'s  [GitHub page](https://github.com/sjaakp/dateline).

## Installing ##

Install **Dateline** with [Bower](http://bower.io/):

	bower install dateline

You can also manually install **Dateline** by [downloading the source in ZIP-format](https://github.com/sjaakp/dateline/archive/master.zip).

## Dependencies ##

**Dateline** depends on:

- jQuery 1.8
- jQuery UI 1.1
- Underscore.js 1.7

## Usage ##

- Be sure `/css/jquery.dateline.css` is loaded as a stylesheet.
- Load the Javascript libraries `underscore.js`, `jquery.js`, `jquery-ui.js` (you probably need some of them on the page anyway).
- Load `/js/jquery.dateline.js`.
- Create a `<div>` with an `id`. 
- In the document-ready function, encapsulate the `<div>` in a jQuery object, and call the `dateline()` method.

A minimum HTML page with a **Dateline** would look like this:

	<html>
	<head>
		<link href="/css/jquery.dateline.css" rel="stylesheet">

	</head>
	<body>

		<div id="dl"></div>

		<script src=".../underscore.js"></script>
		<script src=".../jquery.js"></script>
		<script src=".../jquery-ui.js"></script>
		<script src="/js/jquery.dateline.js"></script>

		<script type="text/javascript">$(document).ready(function () {
			$('#dl').dateline(/* options */);
		</script>
	</body>
	</html>

## Bands ##

At this point, Dateline displays nothing, because there are no bands defined. This is done by setting the option `bands`, like so:

	$('#dl').dateline({
		bands: [
			{
            	size: '60%',
            	scale: Dateline.MONTH,
            	interval: 60
			},
			{
            	size: '40%',
            	scale: Dateline.YEAR,
            	interval: 80,
				layout: 'overview'
			}
		],
		/* more options... */
		});

`bands` is an array of objects, each representing a timeline, with the following properties:

#### interval ####

The length of a scale division in pixels.

#### scale ####

This sets the scale division of the band. It can have one of the following values:

- `Dateline.MILLISECOND`
- `Dateline.SECOND`
- `Dateline.MINUTE`
- `Dateline.HOUR`
- `Dateline.DAY`
- `Dateline.WEEK`
- `Dateline.MONTH`
- `Dateline.YEAR`
- `Dateline.DECADE`
- `Dateline.CENTURY`
- `Dateline.MILLENNIUM`

(Yes, **Dateline**'s range is truly astonishing: from milliseconds to millennia.)

#### size ####

The height of the band as a CSS height-property. Pixels work, but percentages are probably easier. Take care that the band sizes add up to something sensible (like 100%).

#### layout ####

*Optional*. Can be one two values:

- `"normal"` (or `undefined`): events are displayed with icons and text, and are clickable. This is the default value.
- `"overview"`: events are displayed in a compact ribbon, and are not clickable.
 
In most cases, you would have one normal band at the top with several overview bands below it.

#### multiple ####

*Optional*. This value determines which scale divisions are displayed. If it is 2, every other division is displayed. Default value is 1, meaning that every division is displayed.

## Events ##

*Note that we're not talking about Javascript events here!*

Events are objects which are placed on **Dateline**'s timelines. They are defined in Dateline's property `events`, like so:

	$('#dl').dateline({
		bands: [ /* several band definitions... */ ],
		events: [
			{id: "49", start: "2009-07-22", text: "Windows 7 released"},
			{id: "55", start: "1997-09-15", text: "Domain google.com registered"}),
			/* more events... */
		],
		/* more options... */
		});

Events have the following properties:

#### id ####

A unique identifier, probably (but not necessarily) a number.

#### start ####

The point in time the event takes place. This can be a Javascript [Date](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date "MDN network") object or a string that is recognized by [Date.parse()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/parse "MDN network").

#### text ####

The text (or actually, the HTML code) displayed on the timeline.

#### class ####

*Optional*. The HTML-class(es) set to the event when it's displayed in normal layout.

### Duration events ###

Apart from the normal, 'instant' events, **Dateline** also displays duration events. They have all the properties of normal events, plus the following:

#### stop ####

The point in time the event is over.

#### post_start ####

*Optional*. Indicates a degree of uncertainty in `start`.

#### pre_stop ####

*Optional*. Indicates a degree of uncertainty in `stop`.

Like `start`, these three properties can be a Javascript `Date` object or a string that is recognized by `Date.parse()`.

In any case, `start` < `post_start` < `pre_stop` < `stop`.

## Cursor ##

**Dateline**'s timelines are anchored at one point in time, called the *cursor*. By means of the option `cursor` the starting value can be set. Like the event time options, `cursor` can be a Javascript `Date` object or a string that is recognized by `Date.parse()`.

## Other options ##

**Dateline** has the following general options:

#### begin, end ####

*Optional*. The limits between where **Dateline** can be dragged. These options can be `null`, meaning no limit, or a Javascript `Date` object or a string that is recognized by `Date.parse()`. Default: `null`.

#### size ####

*Optional*. The CSS height of **Dateline**. Default is `"320px"`.

#### grid ####

*Optional*. Sets the way the timelines 'land' after certain operations, like swiping or keyboard operations. Can have the following values:

- `null`: no special handling;
- `Dateline.MIDDLE`: `cursor` will end up in the middle of a division (between division marks);
- `Dateline.EDGE`: `cursor` will end up on the edge of a division (on a division mark).

The default value is `Dateline.MIDDLE`.

#### url ####

*Optional*. The url **Dateline** uses when an event is clicked. The url is concatenated with the value of the `id` property of the clicked event.

If `false` (default), clicking on an event has no effect.

#### redirect ####

*Optional*. `boolean`.

- `true`: **Dateline** redirects the browser to the location set by `url`.
- `false`: an Ajax call is made to `url`. **Dateline** displays the returned HTML in a pop up 'bubble' near the event.

Default is `false`.

## Setting and getting options ##

**Dateline** is a [jQuery UI widget](http://wiki.jqueryui.com/w/page/12137708/How%20to%20use%20jQuery%20UI%20widgets "jQuery wiki"). The options can (and should) be set at create time or later by:

	$("#dl").dateline("option", "<optionName>", <newValue>);  

They can be read with:

	var value = $("#dl").dateline("option", "<optionName>");

## Methods ##

**Dateline** has two methods. They should be called in the jQuery UI-fashion, i.e:

	$("#dl").dateline("find", <idValue>);  

#### cursor() ####

Moves the timelines to a given point in time. The parameter can be a Javascript `Date` object or a string that is recognized by `Date.parse()`. If called without parameter, `cursor()` returns the current cursor as Javascript `Date` object.

#### find() ####

Moves the timelines to the event with the given `id` property value.

## Javascript event ##

#### datelinechange ####

This Javascript event is issued whenever the cursor value is changed. The current cursor is sent in the event data as a Javascript `Date` object.

One way to intercept the `datelinechange` event would be:

	$("#dl").on("datelinechange", function(evt, data) {
	    $("#somewhere").text(data.cursor.toLocaleDateString());
	});

## Using icon fonts ##

If you have [Font Awesome](http://fortawesome.github.io/Font-Awesome/) loaded (recommended), you can make **Dateline** use Font Awesome symbols by setting the class of the surrounding `<div>` to `"d-awesome"`.

	<div id="dl" class="d-awesome"></div>


Likewise, if [Glyphicons](http://getbootstrap.com/components/#glyphicons) are loaded, you can set the class to `"d-glyphicon"`. If Google [Material Icons](http://google.github.io/material-design-icons/) are used, set the class to `"d-material"`.

## Iconizing events ##

Normally, events are displayed as a big dot. They can also be displayed as an icon from [Font Awesome](http://fortawesome.github.io/Font-Awesome/). Just set the `class` property of the event to `"fa-xxx"` (`"fa"` is not needed).

For instance, this is the way to display an event with the `'fa-windows'` icon (provided that Font Awesome is loaded):

	$('#dl').dateline({
		bands: [ /* several band definitions... */ ],
		events: [
			{id: "49", start: "2009-07-22", class: "fa-windows", text: "Windows 7 released"},
			/* more events... */
		],
		/* more options... */
		});

Icons are not displayed with duration events.

## Colorizing events ##

By setting the `class` property of an event to `"col-xxx"`, the big dot or the icon is colored. Icon classes and color classes can be combined. Available color classes are listed in `jquery.dateline.less`. Basically, all [CSS3 named colors](http://dev.w3.org/csswg/css-color-3/#svg-color "w3.org") are available.

So this displays the event as a tomato red icon:

	$('#dl').dateline({
		bands: [ /* several band definitions... */ ],
		events: [
			{id: "49", start: "2009-07-22", class: "fa-windows col-tomato", text: "Windows 7 released"},
			/* more events... */
		],
		/* more options... */
		});



