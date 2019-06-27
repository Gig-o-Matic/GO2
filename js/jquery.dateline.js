/*global Math, jQuery, window, console, _, requestAnimationFrame */
/*jslint nomen: true, unparam: true, white: true, plusplus: true, todo: true */
/**
 * MIT licence
 * Version 1.2.4
 * Sjaak Priester, Amsterdam 13-06-2014 ... 12-01-2019.
 *
 */

var Dateline = {
    MILLISECOND: 0,
    SECOND: 1,
    MINUTE: 2,
    HOUR: 3,
    DAY: 4,
    WEEK: 5,
    MONTH: 6,
    YEAR: 7,
    DECADE: 8,
    CENTURY: 9,
    MILLENNIUM: 10,

    NONE: 20,       // modes for rounding
    EDGE: 21,
    MIDDLE: 22
};

(function ($, undefined) {
    'use strict';

    function createDate(date)   {
        return _.isDate(date) ? date : new Date(date);
    }

    /**
     * Markers contains zero or (often) more Marker's
     * @param content
     * @constructor
     */
    function Markers(content)    {
        var MT = [
            function(date)  {       // MILLISECOND
                var v = date.getMilliseconds();
                return {
                    plus: !v,
                    text: v
                };
            },
            function(date)  {       // SECOND
                var v = date.getSeconds();
                return {
                    plus: !v,
                    text: v
                };
            },
            function(date)  {       // MINUTE
                var v = date.getMinutes();
                return {
                    plus: !v,
                    text: v || date.getHours()
                };
            },
            function(date)  {       // HOUR
                var v = date.getHours();
                return {
                    plus: !v,
                    text: v || date.getDate()
                };
            },
            function(date)  {       // DAY
                var v = date.getDate();
                return {
                    plus: v === 1,
                    text: v === 1 ? date.toLocaleDateString(this.content.band.dateline.options.locale, {
                        month: 'short'
                    }) : v
                };
            },
            function(date)  {       // WEEK
                return {
                    plus: false,
                    text: date.toLocaleDateString(this.content.band.dateline.options.locale, {
                        month: 'short',
                        day: 'numeric'
                    })
                };
            },
            function(date)  {       // MONTH
                var v = date.getMonth();
                return v ? {
                    plus: false,
                    text: date.toLocaleDateString(this.content.band.dateline.options.locale, {
                        month: 'short'
                    })
                } : this.yearText(date, 1);
            },
            function(date)  {       // YEAR
                return this.yearText(date, 10);
            },
            function(date)  {       // DECADE
                return this.yearText(date, 100);
            },
            function(date)  {       // CENTURY
                return this.yearText(date, 1000);
            },
            function(date)  {       // MILLENNIUM
                return this.yearText(date, 10000);
            }
        ];
        this.content = content;
        this.element = $('<div>', { class: 'd-markers'}).appendTo(content.element);
        this.markerText = MT[content.band.scale];
    }

    Markers.prototype = {
        yearText: function(date, mod)   {
            var v = date.getFullYear(),
                p = ! (v % mod);
            return {
                plus: p,
                text: v
            };
        },

        render: function()  {
            var c = this.content,
                beginDate = c.range.begin,
                endDate = c.range.end,
                date = new Date(),
                nextDate = new Date(beginDate),
                mt;

            this.element.empty();
            c.band.ceilDate(nextDate);

            this.element.css('paddingLeft', c.band.calcPixels(nextDate - beginDate));

            while (nextDate < endDate)  {
                date.setTime(nextDate);             // make date = nextDate
                c.band.incrDate(nextDate);

                mt = this.markerText(date);

                this.element.append($('<div>', {
                    class: 'd-marker' + (mt.plus ? ' d-plus' : '')
                }).width(c.band.calcPixels(nextDate - date)).text(mt.text));
            }
        }
    };


    /**
     * Events contains zero or more Event's
     * @param content
     * @constructor
     */
    function Events(content)    {
        this.content = content;
        this.element = $('<div>', { class: 'd-events'}).appendTo(content.element);

        this.topMargin = 8;
        this.lineHeight = 24;
        this.renderEvent = content.band.layout === 'overview' ? this.renderOverviewEvent : this.renderNormalEvent;
    }

    Events.prototype = {
        renderNormalEvent: function(event)    {
            var band = this.content.band,
                index = band.index,
                range = this.content.range,
                pos = this.calcPos(event.start),
                elmt, locale, ttl, cls, strt, stp, tapeStyle;

            if (pos) {                          // skip if no position available
                if (event.elements[index])  {   // cached
                    elmt = event.elements[index];
                }
                else    {
                    locale = band.dateline.options.locale;
                    ttl = event.start.toLocaleDateString(locale);
                    cls = event.class || '';

                    if (event.stop)   {         // create new duration event
                        ttl += ' ... ' + event.stop.toLocaleDateString(locale);

                        elmt = $('<div>', {
                            class: 'd-tape-event ' + cls,
                            title: ttl
                        }).html(event.text).prepend($('<div>', {
                            class: 'd-tape'
                        }));
                    }
                    else    {                   // create new instant event
                        elmt = $('<div>', {
                            class: 'd-event ' + cls,
                            title: ttl
                        }).text(event.text);
                    }

                    elmt.data('id', event.id);
                    if (band.dateline.options.url) {
                        elmt.on('mousedown touchstart', function(e) {
                            var t = $(e.currentTarget),
                                dl = band.dateline,
                                bubble = dl._bubble,
                                post = t.position(),
                                contentPos = t.parent().parent().position(),
                                bubblePos = {
                                    top: post.top + contentPos.top,
                                    left: post.left + contentPos.left
                                },
                                id = t.data('id'),
                                url = dl.options.url + id;
//                                url = dl.options.url + '?' + $.param({id: id});

                            e.preventDefault();
                            e.stopPropagation();
                            e.stopImmediatePropagation();
                            
                            dl._highlight(t);
                            if (dl.options.redirect)   {
                                window.location = url;
                            }
                            else    {
                                bubble.show(bubblePos).setInfo(dl.options.loading);
                                $.get(
                                    url,
                                    {},
                                    function (d) {
                                        bubble.setInfo(d);
                                    }
                                );
                            }

                            return false;
                        }.bind(this));
                    }

                    event.elements[index] = elmt;   // cache
                }
                elmt.css(pos);


                if (event.stop) {       // duration event
                    strt = Math.max(event.start, range.begin);
                    stp = Math.min(event.stop, range.end);

                    tapeStyle = {
                        width: Math.max(band.calcPixels(stp - strt), 1)
                    };

                    if (event.post_start && event.post_start > strt)   {
                        tapeStyle['border-left-width'] = band.calcPixels(event.post_start - strt);
                    }
                    if (event.pre_stop && event.pre_stop < stp) {
                        tapeStyle['border-right-width'] = band.calcPixels(stp - event.pre_stop);
                    }
                    elmt.children().css(tapeStyle);
                }
                this.element.append(elmt);

                this.lines[(pos.top - this.topMargin) / this.lineHeight] = pos.left + elmt.outerWidth();    // update line
            }
        },

        renderOverviewEvent: function(event)    {

            var index = this.content.band.index,
                elmt, strt, stp;

            if (event.elements[index])  {   // cached
                elmt = event.elements[index];
            }
            else    {
                elmt = $('<div>', {
                    class: event.stop ? 'd-tape-pin' : 'd-pin'
                });
                event.elements[index] = elmt;   // cache
            }

            if (event.stop) {       // duration event
                strt = Math.max(event.start, this.content.range.begin);
                stp = Math.min(event.stop, this.content.range.end);

                elmt.css({
                    left: this.content.calcLeft(strt),
                    width: Math.max(this.content.band.calcPixels(stp - strt), 1)
                });
            }
            else    {               // instant event
                elmt.css({
                    left: this.content.calcLeft(event.start)
                });
            }

            this.element.append(elmt);
        },

        calcPos: function(date) {   // check for free line; if not available, return false
            var x = this.content.calcLeft(date), i;

            for (i = 0; i < this.nLines; i++)   {
                if (x >= this.lines[i]) {
                    break;
                }
            }
            return i >= this.nLines ? false : {
                left: x,
                top: this.topMargin + i * this.lineHeight
            };
        },

        render: function()  {
            var i, ev, events = this.content.band.dateline.options.events,
                range = this.content.range,
                iBegin = _.sortedIndex(events, { start: range.begin }, function(v) {
                    return v.start;
                }),
                iEnd = _.sortedIndex(events, { start: range.end }, function(v) {
                    return v.start;
                });

            this.element.children().detach();

            this.nLines = Math.floor((this.element.height() - this.topMargin) / this.lineHeight);
            this.lines = [];
            for (i = 0; i < this.nLines; i++)   { this.lines.push(0); }

            for (i = 0; i < iBegin; i++)    {       // render Duration Events if they stop after range.begin
                ev = events[i];
                if (ev.stop && ev.stop > range.begin)   {
                    this.renderEvent(ev);
                }
            }

            for (i = iBegin; i < iEnd; i++) {       // render all Events if start is within range
                this.renderEvent(events[i]);
            }
        }
    };


    /**
     * Content contains Markers and Events
     * @param band
     * @constructor
     */
    function Content(band) {
        var inertia = 500,     // if higher, kinetic effect is stronger
            slow = 0.1,         // if higher, higher velocity is needed for kinetic effect
            duration = 1500,    // duration of kinetic effect in ms
            animation = 0,
            touchId = null;

        this.band = band;
        this.element = $('<div>', {class: 'd-content'}).appendTo(band.element);
        this.center = new Date(band.dateline.options.cursor);

        this.range = {
            begin: new Date(),
            end: new Date()
        };
        this.safe = {
            begin: new Date(),
            end: new Date()
        };
        this.visible = {
            begin: new Date(),
            end: new Date()
        };

        this.markers = new Markers(this);
        this.events = new Events(this);

        this.startPos = 0;
        this.startMs = 0;
        this.prevPos = 0;
        this.prevTimeStamp = 0;
        this.velocity = 0;

        // touch
        this.element.on("touchstart", function(e) {
            e.preventDefault();
            e = e.originalEvent;

            if (touchId === null)   {   // skip if touch is ongoing (this must be a second or third finger)
                if (animation) {
                    animation.stop();
                    animation = 0;
                }

                touchId = e.changedTouches[0].identifier;
                this.initDrag(e, e.changedTouches[0]);
            }

        }.bind(this)).on("touchmove", function(e) {
            var i, t;

            e.preventDefault();
            e = e.originalEvent;

            for (i = 0; i < e.changedTouches.length; i++)   {
                t = e.changedTouches[i];
                if (t.identifier === touchId)   {
                    this.updateDrag(e, t);
                }
            }

        }.bind(this)).on("touchend", function(e) {
            var i, t, dl = band.dateline, animStart, target,
                stepFunc = function(x) { dl._place(x);},    // define functions outside loop to satisfy JsLint
                completeFunc = function() {
                    dl._triggerChange();
                    animation = 0;
                };

            e.preventDefault();
            e = e.originalEvent;

            for (i = 0; i < e.changedTouches.length; i++)   {
                t = e.changedTouches[i];
                if (t.identifier === touchId)   {
                    this.updateDrag(e, t);
                    touchId = null;

                    if (Math.abs(this.velocity) > slow)   {
                        animStart = dl._getCursorMs();          // inertia
                        target = new Date(animStart - band.calcMs(inertia * this.velocity));

                        band.roundDate(target);

                        animation = $({ x: animStart });
                        animation.animate({x: target.getTime() }, {
                            step: stepFunc,
                            duration: duration,
                            easing: 'easeOutExpo',
                            complete: completeFunc
                        });
                    }
                    else    {
                        if (Math.abs(this.prevPos - this.startPos) < 4) {   // we hardly moved, it's a tap, go to tap point
                            target = new Date(this.visible.begin.getTime() + band.calcMs(this.startPos - band.element.offset().left));
                            band.roundDate(target);
                            dl._animateTo(target.getTime());
                        }
                        else    {
                            dl._triggerChange();
                        }
                    }
                }
            }

            // mouse
        }.bind(this)).mousedown(function(evt)  {

            if (evt.which === 1)    {
                evt.preventDefault();

                if (animation) {
                    animation.stop();
                    animation = 0;
                }

                band.setFocus();

                this.initDrag(evt, evt);

                $(band.dateline.document).on('mousemove.dateline', function(evt)  {  // bind event to document, using namespace
                    evt.preventDefault();
                    this.updateDrag(evt, evt);

                }.bind(this)).on('mouseup.dateline', function(evt)  {
                    var dl = band.dateline, target;

                    evt.preventDefault();

                    $(dl.document).off('.dateline');    // unbind document events
                    this.updateDrag(evt, evt);

                    if (Math.abs(this.prevPos - this.startPos) < 4) {   // we hardly moved, it's a click, go to click point
                        target = new Date(this.visible.begin.getTime() + band.calcMs(this.startPos - band.element.offset().left));
                        band.roundDate(target);
                        dl._animateTo(target.getTime());
                    }
                    else    {
                        dl._triggerChange();
                    }
                }.bind(this));
            }
        }.bind(this));
    }

    Content.prototype = {

        initDrag: function(e, t)    {
            this.prevPos = this.startPos = t.pageX;
            this.startMs = this.band.dateline._getCursorMs();
            this.prevTimeStamp = e.timeStamp;
            this.velocity = 0;
        },

        updateDrag: function(e, t)  {
            var nervous = 0.6, // if higher, dependence of final velocity is higher
                x = t.pageX;

            this.band.dateline._place(this.startMs + this.band.calcMs(this.startPos - x));

            this.velocity *= 1 - nervous;
            this.velocity += nervous * ((x - this.prevPos) / (e.timeStamp - this.prevTimeStamp));
            this.prevPos = x;
            this.prevTimeStamp = e.timeStamp;
        },

        xPos: function(e)   {
            return (e.targetTouches && e.targetTouches.length >= 1) ? e.targetTouches[0].clientX : e.clientX;
        },

        render: function()  {
            var opts = this.band.dateline.options,
                beginDate = this.range.begin,
                endDate = this.range.end;

            this.markers.render();
            this.events.render();

            this.element.children('.d-limit').remove();

            if (opts.begin && opts.begin > beginDate && opts.begin < endDate) {
                this.element.append($('<div>', {
                    class: 'd-limit d-begin'
                }).css('right', this.calcRight(opts.begin)));
            }

            if (opts.end && opts.end > beginDate && opts.end < endDate) {
                this.element.append($('<div>', {
                    class: 'd-limit d-end'
                }).css('left', this.calcLeft(opts.end)));
            }
        },
        setWidth: function(w)    {
            this.width = w;
            this.calcRange();
            this.element.width(w);
            this.place();
            this.render();
        },

        calcLeft: function(date)    {
            return this.band.calcPixels(date - this.range.begin);
        },

        calcRight: function(date)    {
            return this.band.calcPixels(this.range.end - date);
        },

        calcRange: function()   {
            var c = this.center.getTime(),  // center date in millisecs
                tau = this.band.calcMs(this.width) / 2, // half range in pixels
                tauSafe = 2 * tau / 3;

            this.range.begin.setTime(c - tau);
            this.range.end.setTime(c + tau);
            this.safe.begin.setTime(c - tauSafe);
            this.safe.end.setTime(c + tauSafe);
        },

        place: function()   {
            var cursor = this.band.dateline.options.cursor,
                ww = this.band.dateline._width,
                c, tau;
            if (cursor < this.safe.begin || cursor > this.safe.end) {
                this.center.setTime(cursor.getTime());
                this.calcRange();
                this.render();
            }
            this.element.css('left', this.band.calcPixels(this.center - cursor)
                    - (this.width - ww) / 2);

            c = cursor.getTime();
            tau = this.band.calcMs(ww) / 2; // half range in msec
            this.visible.begin.setTime(c - tau);
            this.visible.end.setTime(c + tau);
        }
    };

    /**
     * Band contains Content
     * @param bandInfo
     * @constructor
     */
    function Band(bandInfo) {
        var MS = [
                1,                  // MILLISECOND
                1000,               // SECOND
                60000,              // MINUTE, 60 secs
                3600000,            // HOUR, 3600 secs
                86400000,           // DAY, 24 hours = 86,400 secs
                604800000,          // WEEK, 7 days = 604,800 secs
                2629743750,         // MONTH, 1/12 year = 2,629,743.75 secs
                31556925000,        // YEAR, 365.2421875 days = 31,556,925 secs
                315569250000,       // DECADE, 10 years
                3155692500000,      // CENTURY, 100 years
                31556925000000      // MILLENNIUM, 1000 years
            ],
            FLOOR = [
                function(date)  {   // MILLISECOND
                    var v = date.getMilliseconds();
                    date.setMilliseconds(v - v % this.multiple);
                },
                function(date)  {   // SECOND
                    var v = date.getSeconds();
                    date.setSeconds(v - v % this.multiple, 0);
                },
                function(date)  {   // MINUTE
                    var v = date.getMinutes();
                    date.setMiMinutes(v - v % this.multiple, 0, 0);
                },
                function(date)  {   // HOUR
                    var v = date.getHours();
                    date.setHours(v - v % this.multiple, 0, 0, 0);
                },
                function(date)  {   // DAY
                    var v = date.getTime() / this.ms;   // days since 01-01-1970
                    date.setTime((v - v % this.multiple) * this.ms);
                    date.setHours(0, 0, 0, 0);
                },
                function(date)  {   // WEEK
                    var v = date.getTime();
                    v -= 345600000;                 // 4 days; set to sunday (01-01-1970 is thursday
                    v /= this.ms;                   // weeks since 01-01-1970
                    date.setTime((v - v % this.multiple) * this.ms);
                    date.setHours(0, 0, 0, 0);
                },
                function(date)  {   // MONTH
                    var v = date.getMonth();
                    date.setMonth(v - v % this.multiple, 1);
                    date.setHours(0, 0, 0, 0);
                },
                function(date)  {   // YEAR
                    var v = date.getFullYear();
                    date.setFullYear(v - v % this.multiple, 0, 1);
                    date.setHours(0, 0, 0, 0);
                },
                function(date)  {   // DECADE
                    var v = date.getFullYear();
                    date.setFullYear(v - v % (10 * this.multiple), 0, 1);
                    date.setHours(0, 0, 0, 0);
                },
                function(date)  {   // CENTURY
                    var v = date.getFullYear();
                    date.setFullYear(v - v % (100 * this.multiple), 0, 1);
                    date.setHours(0, 0, 0, 0);
                },
                function(date)  {   // MILLENNIUM
                    var v = date.getFullYear();
                    date.setFullYear(v - v % (1000 * this.multiple), 0, 1);
                    date.setHours(0, 0, 0, 0);
                }
            ],
            INCR = [
                function(date)  {   // MILLISECOND
                    date.setMilliseconds(date.getMilliseconds() + this.multiple);
                },
                function(date)  {   // SECOND
                    date.setSeconds(date.getSeconds() + this.multiple, 0);
                },
                function(date)  {   // MINUTE
                    date.setMinutes(date.getMinutes() + this.multiple, 0, 0);
                },
                function(date)  {   // HOUR
                    date.setHours(date.getHours() + this.multiple, 0, 0, 0);
                },
                function(date)  {   // DAY
                    date.setDate(date.getDate() + this.multiple);
                },
                function(date)  {   // WEEK
                    date.setDate(date.getDate() + 7 * this.multiple);
                },
                function(date)  {   // MONTH
                    date.setMonth(date.getMonth() + this.multiple, 1);
                },
                function(date)  {   // YEAR
                    date.setFullYear(date.getFullYear() + this.multiple, 0, 1);
                },
                function(date)  {   // DECADE
                    date.setFullYear(date.getFullYear() + 10 * this.multiple, 0, 1);
                },
                function(date)  {   // CENTURY
                    date.setFullYear(date.getFullYear() + 100 * this.multiple, 0, 1);
                },
                function(date)  {   // MILLENNIUM
                    date.setFullYear(date.getFullYear() + 1000 * this.multiple, 0, 1);
                }
            ],
            dl = bandInfo.dateline;

        $.extend(this, { multiple: 1 }, bandInfo);
        this.ms = MS[this.scale];
        this.floorDate = FLOOR[this.scale];
        this.incrDate = INCR[this.scale];

        this.before = $('<div>', { class: 'd-range d-before' });
        this.after = $('<div>', { class: 'd-range d-after' });

        this.leftIndicator = $('<div>', { class: 'd-indicator d-left' }).mousedown(function(e) {
            this.stepLeft(e.shiftKey);
            e.preventDefault();
        }.bind(this));
        this.rightIndicator = $('<div>', { class: 'd-indicator d-right' }).mousedown(function(e) {
            this.stepRight(e.shiftKey);
            e.preventDefault();
        }.bind(this));

        this.element = $('<div>', {
            class: 'd-band d-band-' + this.index + ' d-scale-' + this.scale,
            tabindex: '0'
        }).height(this.size).append(
            this.keyInput,
            this.before,
            this.after
        );

        this.content = new Content(this);

        this.element.append(
            this.leftIndicator,
            this.rightIndicator
        ).focus(function(e) {
            this.dateline._focus = this.index;
            this.leftIndicator.show();
            this.rightIndicator.show();
        }.bind(this)).blur(function(e) {
            this.leftIndicator.hide();
            this.rightIndicator.hide();
        }.bind(this)).keydown(function(e) {
                var current = dl._getCursorMs(),
                    events, i, prev = true;

                if (prev)   {
                    switch (e.keyCode) {
                        case 9:     // tab
                            events = dl.options.events;
                            if (events.length)  {
                                if (e.shiftKey) {
                                    i = _.sortedIndex(events, { start: current - 1 }, function(v) {
                                        return v.start;
                                    });
                                    if (i > 0) {
                                        dl._animateTo(events[i - 1].start);
                                    }
                                }
                                else    {
                                    i = _.sortedIndex(events, { start: current + 1 }, function(v) {
                                        return v.start;
                                    });
                                    if (i < events.length) {
                                        dl._animateTo(events[i].start);
                                    }
                                }
                            }
                            break;
                        // Nothing wrong with this code, just seems a little bit too much.
/*
                        case 33: // page up
                            dl._animateTo(current + 10 * this.ms);
                            break;
                        case 34: // page down
                            dl._animateTo(current - 10 * this.ms);
                            break;
*/

                        case 35: // end
                            if (dl.options.end)   {
                                dl._animateTo(dl.options.end.getTime());
                            }
                            break;
                        case 36: // home
                            if (dl.options.begin)   {
                                dl._animateTo(dl.options.begin.getTime());
                            }
                            break;
                        case 37: // left arrow
                            this.stepLeft(e.shiftKey);
                            break;
                        case 38: // up arrow
                            dl._cycleFocus(-1);
                            break;
                        case 39: // right arrow
                            this.stepRight(e.shiftKey);
                            break;
                        case 40: // down arrow
                            dl._cycleFocus(1);
                            break;
                        default:
                            prev = false;
                            break;
                    }
                    if (prev)    {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                }
                return ! prev;

            }.bind(this));
    }

    Band.prototype = {

        place: function()   {
            this.content.place();
        },

        setWidth: function(w)   {
            this.content.setWidth(w);
        },

        setRange: function(range)   {
            var cursor = this.dateline.options.cursor;
            if (range)  {
                this.before.css('width', this.calcPixels(cursor - range.begin));
                this.after.css('width', this.calcPixels(range.end - cursor));
            }
            else    {
                this.before.css('width', '');
                this.after.css('width', '');
            }
        },

        setRangeFrom: function(band)    {
            this.setRange(band.content.visible);
        },

        calcPixels: function(millisecs) {
            var p = millisecs * this.interval / this.ms;
            // three decimals. @link https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/round
            return +(Math.round(p + "e+3")  + "e-3");
        },

        calcMs: function(pixels)    {
            return pixels * this.ms / this.interval;
        },

        setFocus: function()   {
            this.element.focus();
        },

        stepLeft: function(big) {
            var dl = this.dateline;
            dl._animateTo(dl._getCursorMs() + (big ? 10 : 1) * this.ms, big ? 1200 : 150);
        },

        stepRight: function(big) {
            var dl = this.dateline;
            dl._animateTo(dl._getCursorMs() - (big ? 10 : 1) * this.ms, big ? 1200 : 150);
        },

        ceilDate: function(date)    {
            this.floorDate(date);
            this.incrDate(date);
        },

        roundDate: function(date)   {
            var grid = this.dateline.options.grid,
                floor, ceil, mid;

            if (grid !== Dateline.NONE) {   // no change if Dateline.NONE
                floor = new Date(date);
                this.floorDate(floor);
                ceil = new Date(floor);
                this.incrDate(ceil);
                mid = (ceil.getTime() + floor.getTime()) / 2;

                if (grid === Dateline.MIDDLE)   {
                    date.setTime(mid);
                }
                else    {       // Dateline.EDGE
                    if (date.getTime() > mid)   {
                        date.setTime(ceil);
                    }
                    else    {
                        date.setTime(floor);
                    }
                }
            }
        }
    };

    /**
     * Bubble
     * @param dateline
     * @constructor
     */
    function Bubble(dateline)   {
        this.dateline = dateline;
        this.info = $('<div>', {
            class: 'd-info'
        });
        this.element = $('<div>', {
            class: 'd-bubble'
        }).append($('<div>', {
            class: 'd-close'
        }).html('&times;').click(function(e) {
            this.hide();
        }.bind(this)), this.info);
    }

    Bubble.prototype = {
        show: function(pos)    {
            pos.left -= 20;
            pos.top += 20;
            this.element.show().css(pos);
            return this;
        },

        hide: function()    {
            this.element.hide();
            this.dateline._clearHighlight();
            return this;
        },

        setInfo: function(h)   {
            this.info.html(h);
            return this;
        }
    };

    $.widget("sjaakp.dateline", {

        options:    {

            size: '320px',
            bands: [],

            cursor: new Date(),
            begin: null,
            end: null,
            events: [],

            redirect: false,
            url: false,
            grid: Dateline.MIDDLE,
            loading: '<i class="fa fa-refresh fa-spin fa-lg"></i>&nbsp;&hellip;'
        },

        _bands: [],
        _focus: 0,
        _scrollFactor: 5,

        _create: function() {
            var self = this,
                opts = this.options;

            if (! this.element.attr('tabindex'))    {
                this.element.attr('tabindex', 0);
            }

            opts.cursor = createDate(opts.cursor);
            if (opts.begin) { opts.begin = createDate(opts.begin); }
            if (opts.end) { opts.end = createDate(opts.end); }

            this._prepareEvents();

            this._width = this.element.css('height', opts.size).addClass('d-dateline').width();

            this._bubble = new Bubble(this);

            this._inner = $('<div>', {
                class: 'd-inner'
            });

            this.element.append(this._inner, this._bubble.element);

            this._prepareBands();

            this._setWidth();

            this.window.resize(_.debounce(function() {
                var w = self.element.width();
                if (self._width !== w)    {
                    self._width = w;
                    self._setWidth();
                }
            }, 500));

            this.element.focus(function(e)  {
                if (this._bands.length) {
                    this._bands[this._focus].setFocus();
                }
            }.bind(this));
        },

        _setOption: function(key, value)    {
            if ([ 'cursor', 'begin', 'end'].indexOf(key) >= 0)  {
                value = createDate(value);
            }
            this._super(key, value);
            if (key === 'bands')   {
                this._prepareBands();
            }
            if (key === 'events')   {
                this._prepareEvents();
            }
            this._setWidth();       // render complete dateline
        },

        _setOptions: function(options)  {
            this._super(options);
        },

        _prepareBands: function()   {
            var bands = this.options.bands;

            if (! bands.length)    {
                this._inner.html('&nbsp;No bands defined.');
            }

            this._bands = bands.map(function(v, i, a) {
                v.dateline = this;
                v.index = i;

                var r = new Band(v);
                this._inner.append(r.element);
                return r;
            }, this);
        },

        _prepareEvents: function()  {
            var events = this.options.events;

            events.forEach(function(v, i, a) {
                ['start', 'stop', 'post_start', 'pre_stop'].forEach(function(w, j, b) {
                    if (v[w])   {
                        v[w] = createDate(v[w]);

                    }
                });

                v.elements = [];
            });

            events.sort(function(a, b) {
                return a.start - b.start;
            });
        },

        _place: function(ms)  {
            this._bubble.hide();

            if (this.options.begin && ms < this.options.begin.getTime()) {
                ms = this.options.begin.getTime();
            }
            if (this.options.end && ms > this.options.end.getTime()) {
                ms = this.options.end.getTime();
            }
            this.options.cursor.setTime(ms);
            this._bands.forEach(function(v, i, a) {
                v.place();
            });
            this._sync();
        },

        _animateTo: function(ms, duration)    {
            duration = duration || 800;

            $({ cursor: this._getCursorMs() }).animate( { cursor: ms }, {
                step: function(now, tween) {
                    this._place(now);
                }.bind(this),
                complete: function() {
                    this._triggerChange();
                }.bind(this),
                duration: duration
            });
        },

        _getCursorMs: function()    {
            return this.options.cursor.getTime();
        },

        _setWidth: function()   {
            var w = this._width * this._scrollFactor;
            this._bands.forEach(function(v, i, a) {
                v.setWidth(w);
            });
            this._sync();
        },

        _sync: function()   {
            var prev;
            this._bands.forEach(function(v, i, a) {
                if (prev) { v.setRangeFrom(prev); }
                prev = v;
            });
        },

        _cycleFocus: function(step)  {
            var mod = this._bands.length,
                i = this._focus;

            i+= mod + step;
            i%= mod;
            this._bands[i].setFocus();
        },

        _highlight: function(elmt) {
            this._clearHighlight();
            this._hl = elmt.addClass('d-highlight');
            this._intval = window.setInterval(function() {
                this._hl.toggleClass('d-highlight');
            }.bind(this), 500);
        },

        _clearHighlight: function()   {
            if (this._intval)   {
                window.clearInterval(this._intval);
                this._intval = null;
            }
            if (this._hl)   {
                this._hl.removeClass('d-highlight');
                this._hl = null;
            }
        },

        _triggerChange: function()  {
            this._trigger('change', null, { cursor: new Date(this._getCursorMs()) } );
        },

        cursor: function(date) {
            if (date)   {
                this._animateTo(createDate(date).getTime());
            }
            else    {
                return new Date(this._getCursorMs());
            }
        },

        find: function(id) {
            // use == in stead of === to find string key in case v.id is integer
            var found = _.find(this.options.events, function(v) { return v.id == id; });
            if (found)  {
                this._animateTo(found.start.getTime());
            }
        }
    });

} (jQuery));