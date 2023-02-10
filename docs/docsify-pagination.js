(function (global, factory) {
	typeof exports === 'object' && typeof module !== 'undefined' ? factory() :
	typeof define === 'function' && define.amd ? define(factory) :
	(factory());
}(this, (function () { 'use strict';

var commonjsGlobal = typeof window !== 'undefined' ? window : typeof global !== 'undefined' ? global : typeof self !== 'undefined' ? self : {};





function createCommonjsModule(fn, module) {
	return module = { exports: {} }, fn(module, module.exports), module.exports;
}

var componentQuery = createCommonjsModule(function (module, exports) {
function one(selector, el) {
  return el.querySelector(selector);
}

exports = module.exports = function (selector, el) {
  el = el || document;
  return one(selector, el);
};

exports.all = function (selector, el) {
  el = el || document;
  return el.querySelectorAll(selector);
};

exports.engine = function (obj) {
  if (!obj.one) throw new Error('.one callback required');
  if (!obj.all) throw new Error('.all callback required');
  one = obj.one;
  exports.all = obj.all;
  return exports;
};
});

var componentQuery_1 = componentQuery.all;
var componentQuery_2 = componentQuery.engine;

var globalObject = createCommonjsModule(function (module) {
(function ($) {
  try {
    $('export default global');
  } catch (e) {
    try {
      $('export default self');
    } catch (e) {
      try {
        module.exports = commonjsGlobal;
      } catch (e) {
        try {
          self.global = self;
        } catch (e) {
          window.global = window;
        }
      }
    }
  }
})(eval);
});

/**
 * Module dependencies.
 */

try {
  var query$1 = componentQuery;
} catch (err) {
  var query$1 = componentQuery;
}

/**
 * Element prototype.
 */

var Element = globalObject.Element;
var proto = Element && Element.prototype || {};

/**
 * Vendor function.
 */

var vendor = proto.matches || proto.webkitMatchesSelector || proto.mozMatchesSelector || proto.msMatchesSelector || proto.oMatchesSelector;

/**
 * Expose `match()`.
 */

var componentMatchesSelector = match;

/**
 * Match `el` to `selector`.
 *
 * @param {Element} el
 * @param {String} selector
 * @return {Boolean}
 * @api public
 */

function match(el, selector) {
  if (!el || el.nodeType !== 1) return false;
  if (vendor) return vendor.call(el, selector);
  var nodes = query$1.all(selector, el.parentNode);
  for (var i = 0; i < nodes.length; ++i) {
    if (nodes[i] == el) return true;
  }
  return false;
}

/**
 * Module Dependencies
 */

try {
  var matches = componentMatchesSelector;
} catch (err) {
  var matches = componentMatchesSelector;
}

/**
 * Export `closest`
 */

var componentClosest = closest;

/**
 * Closest
 *
 * @param {Element} el
 * @param {String} selector
 * @param {Element} scope (optional)
 */

function closest(el, selector, scope) {
  scope = scope || document.documentElement;

  // walk up the dom
  while (el && el !== scope) {
    if (matches(el, selector)) return el;
    el = el.parentNode;
  }

  // check scope for match
  return matches(el, selector) ? el : null;
}

function styleInject(css, ref) {
  if (ref === void 0) ref = {};
  var insertAt = ref.insertAt;

  if (!css || typeof document === 'undefined') {
    return;
  }

  var head = document.head || document.getElementsByTagName('head')[0];
  var style = document.createElement('style');
  style.type = 'text/css';

  if (insertAt === 'top') {
    if (head.firstChild) {
      head.insertBefore(style, head.firstChild);
    } else {
      head.appendChild(style);
    }
  } else {
    head.appendChild(style);
  }

  if (style.styleSheet) {
    style.styleSheet.cssText = css;
  } else {
    style.appendChild(document.createTextNode(css));
  }
}

var css = `
    .docsify-pagination-container{display:flex;flex-wrap:wrap;justify-content:space-between;overflow:hidden;margin:1em 15px 1em 0;;border-top:1px solid #33A9F4;color: #0366D6;}
    .pagination-item{margin:0 0 2.25em 0;}
    .pagination-item a,.pagination-item a:hover{text-decoration:none}
    .pagination-item a{color:currentColor}
    .pagination-item a:hover .pagination-item-title{text-decoration:underline}
    .pagination-item a .pagination-item-label,.pagination-item a .pagination-item-subtitle,.pagination-item a .pagination-item-title{opacity:.7;transition:all .2s}
    .pagination-item .pagination-item-label,.pagination-item a:hover .pagination-item-label{opacity:.7;transition:all .2s}
    .pagination-item a:hover .pagination-item-title{opacity:1;transition:all .2s}
    .pagination-item-label{color:#0366D6;font-size:1.1em}
    .pagination-item-label>*{line-height:1;vertical-align:middle}
    .pagination-item-label svg{height:.8em;width:auto;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1px;color:#0366D6;}
    .pagination-item--next{margin:0 0 2.25em 0;text-align:right;opacity:1;}
    .pagination-item--previous{margin:0 0 2.25em 0;text-align:left;opacity:1;}
    .pagination-item--next svg{margin-left:.5em}
    .pagination-item--previous svg{margin-right:.5em}
    .pagination-item-title{font-size:1.4em}
    .pagination-item-subtitle{text-transform:uppercase;opacity:.3};
    `
styleInject(css);

var classCallCheck = function (instance, Constructor) {
  if (!(instance instanceof Constructor)) {
    throw new TypeError("Cannot call a class as a function");
  }
};

var createClass = function () {
  function defineProperties(target, props) {
    for (var i = 0; i < props.length; i++) {
      var descriptor = props[i];
      descriptor.enumerable = descriptor.enumerable || false;
      descriptor.configurable = true;
      if ("value" in descriptor) descriptor.writable = true;
      Object.defineProperty(target, descriptor.key, descriptor);
    }
  }

  return function (Constructor, protoProps, staticProps) {
    if (protoProps) defineProperties(Constructor.prototype, protoProps);
    if (staticProps) defineProperties(Constructor, staticProps);
    return Constructor;
  };
}();







var _extends = Object.assign || function (target) {
  for (var i = 1; i < arguments.length; i++) {
    var source = arguments[i];

    for (var key in source) {
      if (Object.prototype.hasOwnProperty.call(source, key)) {
        target[key] = source[key];
      }
    }
  }

  return target;
};

/**
 * constants
 */
var DEFAULT_OPTIONS = function DEFAULT_OPTIONS(config) {
  return {
    previousText: 'PREVIOUS',
    nextText: 'NEXT',
    crossChapter: false,
    crossChapterText: false
  };
};
var CONTAINER_CLASSNAME = 'docsify-pagination-container';

/**
 * basic utilities
 */
function toArray(elements) {
  return Array.prototype.slice.call(elements);
}
function findChapter(element) {
  var container = componentClosest(element, 'div > ul > li');
  return componentQuery('p', container);
}
function findHyperlink(element) {
  return element.href ? element : componentQuery('a', element);
}
function normailizeLink(path) {
  if (path && path.toUpperCase() === '#/README') {
    return '#/';
  }
  return path;
}
function isALinkTo(path, element) {
  if (arguments.length === 1) {
    return function (element) {
      return isALinkTo(path, element);
    };
  }
  return normailizeLink(decodeURIComponent(element.getAttribute('href').split('?')[0])) === normailizeLink(decodeURIComponent(path));
}

/**
 * core renderer
 */

var Link = function () {
  function Link(element) {
    classCallCheck(this, Link);

    if (!element) {
      return;
    }
    this.chapter = findChapter(element);
    this.hyperlink = findHyperlink(element);
  }

  createClass(Link, [{
    key: 'toJSON',
    value: function toJSON() {
      if (!this.hyperlink) {
        return;
      }
      return {
        name: this.hyperlink.innerText,
        href: this.hyperlink.getAttribute('href'),
        chapterName: this.chapter && this.chapter.innerText || '',
        isExternal: this.hyperlink.getAttribute('target') === '_blank'
      };
    }
  }]);
  return Link;
}();

function pagination(vm, _ref) {
  var crossChapter = _ref.crossChapter;

  try {
    var path = vm.router.toURL(vm.route.path);
    var all = toArray(componentQuery.all('.sidebar-nav li a')).filter(function (element) {
      return !componentMatchesSelector(element, '.section-link');
    });
    var active = all.find(isALinkTo(path));
    var group = toArray((componentClosest(active, 'ul') || {}).children).filter(function (element) {
      return element.tagName.toUpperCase() === 'LI';
    });
    var index = crossChapter ? all.findIndex(isALinkTo(path)) : group.findIndex(function (item) {
      var hyperlink = findHyperlink(item);
      return hyperlink && isALinkTo(path, hyperlink);
    });

    var links = crossChapter ? all : group;

    return {
      route: vm.route,
      prev: new Link(links[index - 1]).toJSON(),
      next: new Link(links[index + 1]).toJSON()
    };
  } catch (error) {
    return {
      route: {}
    };
  }
}

var template = {
  container: function container() {
    return '<div class="' + CONTAINER_CLASSNAME + '"></div>';
  },
  inner: function inner(data, options) {
    var _getLocalizationTexts = getLocalizationTexts(options, data.route.path),
        previousText = _getLocalizationTexts.previousText,
        nextText = _getLocalizationTexts.nextText;

    return [data.prev && '\n        <div class="pagination-item pagination-item--previous">\n          <a href="' + data.prev.href + '" ' + (data.prev.isExternal ? 'target="_blank"' : '') + '>\n            <div class="pagination-item-label">\n              <svg width="10" height="16" viewBox="0 0 10 16" xmlns="http://www.w3.org/2000/svg">\n                <polyline fill="none" vector-effect="non-scaling-stroke" points="8,2 2,8 8,14"/>\n              </svg>\n              <span>' + previousText + '</span>\n            </div>\n            <div class="pagination-item-title">' + data.prev.name + '</div>\n      ', data.prev && options.crossChapterText && '<div class="pagination-item-subtitle">' + data.prev.chapterName + '</div>', data.prev && '</a>\n        </div>\n      ', data.next && '\n        <div class="pagination-item pagination-item--next">\n          <a href="' + data.next.href + '" ' + (data.next.isExternal ? 'target="_blank"' : '') + '>\n            <div class="pagination-item-label">\n              <span>' + nextText + '</span>\n              <svg width="10" height="16" viewBox="0 0 10 16" xmlns="http://www.w3.org/2000/svg">\n                <polyline fill="none" vector-effect="non-scaling-stroke" points="2,2 8,8 2,14"/>\n              </svg>\n            </div>\n            <div class="pagination-item-title">' + data.next.name + '</div>\n      ', data.next && options.crossChapterText && '<div class="pagination-item-subtitle">' + data.next.chapterName + '</div>', data.next && '</a>\n        </div>\n      '].filter(Boolean).join('');
  }
};

function getLocalizationTexts(options, path) {
  var texts = {};['previousText', 'nextText'].forEach(function (key) {
    var text = options[key];

    if (typeof text === 'string') {
      texts[key] = text;
    } else {
      Object.keys(text).some(function (local) {
        var isMatch = path && path.indexOf(local) > -1;

        texts[key] = isMatch ? text[local] : text;

        return isMatch;
      });
    }
  });
  return texts;
}

/**
 * installation
 */
function install(hook, vm) {
  var options = _extends({}, DEFAULT_OPTIONS(vm.config), vm.config.pagination || {});

  function render() {
    var container = componentQuery('.' + CONTAINER_CLASSNAME);

    if (!container) return;

    container.innerHTML = template.inner(pagination(vm, options), options);
  }

  hook.afterEach(function (html) {
    return html + template.container();
  });
  hook.doneEach(function () {
    return render();
  });
}

window.$docsify = window.$docsify || {};

window.$docsify.plugins = [install].concat(window.$docsify.plugins || []);

})));